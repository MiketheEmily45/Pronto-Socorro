# Fila de Pronto-Socorro — API (Bloco 2)

Back-end em Django + Django REST Framework. Este projeto é a base: o mecanismo de
atualização em tempo real e o painel público serão encaixados conforme o desenho
de arquitetura do Bloco 1.

## Estrutura

```
config/          configurações do Django (settings por variável de ambiente)
fila/
  models.py      Paciente e Chamada
  services.py    regras de negócio (cadastrar, remover, chamar próximo, estado do painel)
  serializers.py entrada/saída da API (visão pública reduzida para LGPD)
  views.py       endpoints
  tests.py       testes automatizados
```

## Instalação

Requer Python 3.12 ou superior e Git.

### Linux / macOS

```bash
git clone <URL-DO-REPOSITORIO> fila-ps
cd fila-ps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # este é o usuário administrador
```

### Windows (PowerShell)

```powershell
git clone <URL-DO-REPOSITORIO> fila-ps
cd fila-ps
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

Se o PowerShell bloquear a ativação do venv, rode uma vez:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Executar em máquinas diferentes

1. Descubra o IP do notebook que roda a API (`ip a` no Linux, `ipconfig` no Windows). Exemplo: `192.168.0.10`.
2. Configure os hosts permitidos e, se o painel for uma página web em outra máquina, a origem dele:

   **Linux / macOS**
   ```bash
   export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,192.168.0.10"
   export CORS_ALLOWED_ORIGINS="http://192.168.0.20:8080"
   ```

   **Windows (PowerShell)**
   ```powershell
   $env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.0.10"
   $env:CORS_ALLOWED_ORIGINS = "http://192.168.0.20:8080"
   ```

3. Suba o servidor escutando em todas as interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
4. Libere a porta 8000 no firewall do notebook, se necessário.
5. Na outra máquina, teste: `http://192.168.0.10:8000/api/painel/`

Todas as variáveis estão listadas em `.env.example`.

## Endpoints

| Método | Rota | Acesso | O que faz |
|---|---|---|---|
| POST | `/api/auth/token/` | público | login do administrador, devolve o token |
| POST | `/api/pacientes/` | admin | cadastra paciente `{"nome": "..."}` |
| GET | `/api/pacientes/` | admin | lista (filtro `?status=aguardando`) |
| DELETE | `/api/pacientes/{id}/` | admin | remove da fila |
| POST | `/api/chamar-proximo/` | admin | chama o próximo `{"sala": "3", "medico": "Dra. Helena"}` |
| GET | `/api/painel/` | público, somente leitura | contagem, chamadas e `ultima_chamada_id` |

O painel deve consultar `/api/painel/` e tocar o aviso sonoro quando o
`ultima_chamada_id` mudar. O endpoint só mostra nome reduzido ("Maria S."),
sala e médico.

Também há a interface administrativa do Django em `/admin/`.

### Exemplo de uso

```bash
# 1. login
curl -X POST http://192.168.0.10:8000/api/auth/token/ -d "username=admin&password=SUA_SENHA"
# 2. cadastrar
curl -X POST http://192.168.0.10:8000/api/pacientes/ \
  -H "Authorization: Token SEU_TOKEN" -H "Content-Type: application/json" \
  -d '{"nome": "Maria da Silva"}'
# 3. chamar o próximo
curl -X POST http://192.168.0.10:8000/api/chamar-proximo/ \
  -H "Authorization: Token SEU_TOKEN" -H "Content-Type: application/json" \
  -d '{"sala": "3", "medico": "Dra. Helena"}'
# 4. ver o painel (sem autenticação)
curl http://192.168.0.10:8000/api/painel/
```

## Testes

```bash
python manage.py test
```

## Fluxo de trabalho em grupo

- Cada integrante commita com o próprio usuário do Git (`git config user.name` / `user.email`),
  pois o histórico precisa mostrar a contribuição de cada um.
- Uma branch por funcionalidade (`git checkout -b feature/nome`), com merge na `main` por pull request.

## Desvios em relação ao Bloco 1

(Registrar aqui qualquer diferença entre o que foi desenhado e o que foi implementado, com a justificativa.)

| Desvio | Justificativa |
|---|---|
| | |
