from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Chamada, Paciente


class BaseAPITestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user("admin", password="senha-forte-123", is_staff=True)
        self.comum = User.objects.create_user("comum", password="senha-forte-123")
        self.anonimo = APIClient()
        self.cliente_admin = APIClient()
        self.cliente_admin.credentials(
            HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.admin).key}"
        )
        self.cliente_comum = APIClient()
        self.cliente_comum.credentials(
            HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.comum).key}"
        )

    def cadastrar(self, nome):
        resp = self.cliente_admin.post("/api/pacientes/", {"nome": nome}, format="json")
        self.assertEqual(resp.status_code, 201)
        return resp.data["id"]


class ModeloTests(TestCase):
    def test_nome_publico_reduzido(self):
        self.assertEqual(Paciente(nome="Maria da Silva Santos").nome_publico, "Maria S.")
        self.assertEqual(Paciente(nome="joão").nome_publico, "joão")
        self.assertEqual(Paciente(nome="Ana  Lima").nome_publico, "Ana L.")


class AutenticacaoTests(BaseAPITestCase):
    def test_login_devolve_token(self):
        resp = self.anonimo.post(
            "/api/auth/token/", {"username": "admin", "password": "senha-forte-123"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.data)

    def test_login_com_senha_errada_falha(self):
        resp = self.anonimo.post(
            "/api/auth/token/", {"username": "admin", "password": "errada"}, format="json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_operacoes_administrativas_exigem_autenticacao(self):
        self.assertEqual(self.anonimo.get("/api/pacientes/").status_code, 401)
        self.assertEqual(
            self.anonimo.post("/api/pacientes/", {"nome": "X"}, format="json").status_code, 401
        )
        self.assertEqual(self.anonimo.delete("/api/pacientes/1/").status_code, 401)
        self.assertEqual(
            self.anonimo.post(
                "/api/chamar-proximo/", {"sala": "1", "medico": "Dr. X"}, format="json"
            ).status_code,
            401,
        )

    def test_usuario_sem_permissao_de_admin_e_negado(self):
        resp = self.cliente_comum.post("/api/pacientes/", {"nome": "X"}, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Paciente.objects.count(), 0)


class AdministracaoDaFilaTests(BaseAPITestCase):
    def test_cadastrar_paciente(self):
        resp = self.cliente_admin.post("/api/pacientes/", {"nome": "  Maria Souza "}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["nome"], "Maria Souza")
        self.assertEqual(resp.data["status"], "aguardando")

    def test_nome_vazio_e_rejeitado(self):
        resp = self.cliente_admin.post("/api/pacientes/", {"nome": "   "}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_listar_com_filtro_de_status(self):
        self.cadastrar("Ana Lima")
        self.cadastrar("Bruno Dias")
        resp = self.cliente_admin.get("/api/pacientes/?status=aguardando")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_remover_paciente(self):
        pid = self.cadastrar("Ana Lima")
        resp = self.cliente_admin.delete(f"/api/pacientes/{pid}/")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Paciente.objects.get(pk=pid).status, "removido")

    def test_remover_duas_vezes_da_conflito(self):
        pid = self.cadastrar("Ana Lima")
        self.cliente_admin.delete(f"/api/pacientes/{pid}/")
        resp = self.cliente_admin.delete(f"/api/pacientes/{pid}/")
        self.assertEqual(resp.status_code, 409)

    def test_remover_inexistente_da_404(self):
        self.assertEqual(self.cliente_admin.delete("/api/pacientes/999/").status_code, 404)

    def test_chamar_proximo_respeita_ordem_de_chegada(self):
        primeiro = self.cadastrar("Ana Lima")
        self.cadastrar("Bruno Dias")
        resp = self.cliente_admin.post(
            "/api/chamar-proximo/", {"sala": "3", "medico": "Dra. Helena"}, format="json"
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["sala"], "3")
        self.assertEqual(resp.data["medico"], "Dra. Helena")
        self.assertEqual(Paciente.objects.get(pk=primeiro).status, "chamado")
        self.assertEqual(Chamada.objects.count(), 1)

    def test_chamar_proximo_com_fila_vazia(self):
        resp = self.cliente_admin.post(
            "/api/chamar-proximo/", {"sala": "1", "medico": "Dr. X"}, format="json"
        )
        self.assertEqual(resp.status_code, 404)

    def test_chamar_proximo_exige_sala_e_medico(self):
        self.cadastrar("Ana Lima")
        resp = self.cliente_admin.post("/api/chamar-proximo/", {"sala": "1"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Chamada.objects.count(), 0)


class PainelPublicoTests(BaseAPITestCase):
    def test_painel_e_publico(self):
        resp = self.anonimo.get("/api/painel/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["aguardando"], 0)
        self.assertEqual(resp.data["chamadas"], [])
        self.assertIsNone(resp.data["ultima_chamada_id"])

    def test_painel_e_somente_leitura(self):
        for metodo in ("post", "put", "patch", "delete"):
            resp = getattr(self.anonimo, metodo)("/api/painel/", {}, format="json")
            self.assertEqual(resp.status_code, 405, metodo)
        # nem mesmo o administrador altera a fila por este endpoint
        resp = self.cliente_admin.post("/api/painel/", {}, format="json")
        self.assertEqual(resp.status_code, 405)

    def test_contagem_e_chamadas_ficam_consistentes(self):
        for nome in ("Ana Lima", "Bruno Dias", "Carla Souza"):
            self.cadastrar(nome)
        self.cliente_admin.post(
            "/api/chamar-proximo/", {"sala": "2", "medico": "Dr. Paulo"}, format="json"
        )
        resp = self.anonimo.get("/api/painel/")
        self.assertEqual(resp.data["aguardando"], 2)
        self.assertEqual(len(resp.data["chamadas"]), 1)
        self.assertEqual(resp.data["chamadas"][0]["paciente"], "Ana L.")
        self.assertEqual(resp.data["chamadas"][0]["sala"], "2")
        self.assertEqual(resp.data["chamadas"][0]["medico"], "Dr. Paulo")

    def test_painel_nao_expoe_dados_alem_do_necessario(self):
        self.cadastrar("Maria da Silva Santos")
        self.cliente_admin.post(
            "/api/chamar-proximo/", {"sala": "1", "medico": "Dr. X"}, format="json"
        )
        chamada = self.anonimo.get("/api/painel/").data["chamadas"][0]
        self.assertEqual(
            set(chamada.keys()), {"id", "paciente", "sala", "medico", "chamada_em"}
        )
        self.assertEqual(chamada["paciente"], "Maria S.")
        self.assertNotIn("Silva", str(chamada))

    def test_ultima_chamada_id_muda_a_cada_nova_chamada(self):
        self.cadastrar("Ana Lima")
        self.cadastrar("Bruno Dias")
        self.cliente_admin.post("/api/chamar-proximo/", {"sala": "1", "medico": "Dr. X"}, format="json")
        id1 = self.anonimo.get("/api/painel/").data["ultima_chamada_id"]
        self.cliente_admin.post("/api/chamar-proximo/", {"sala": "2", "medico": "Dr. Y"}, format="json")
        id2 = self.anonimo.get("/api/painel/").data["ultima_chamada_id"]
        self.assertNotEqual(id1, id2)

    def test_paciente_removido_some_do_painel(self):
        pid = self.cadastrar("Ana Lima")
        self.cliente_admin.post("/api/chamar-proximo/", {"sala": "1", "medico": "Dr. X"}, format="json")
        self.cliente_admin.delete(f"/api/pacientes/{pid}/")
        resp = self.anonimo.get("/api/painel/")
        self.assertEqual(resp.data["chamadas"], [])
        self.assertEqual(resp.data["aguardando"], 0)

    def test_painel_ignora_credenciais_invalidas(self):
        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION="Token token-invalido")
        self.assertEqual(cliente.get("/api/painel/").status_code, 200)
