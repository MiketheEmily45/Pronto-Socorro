from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Medico, Paciente, Sala
from .serializers import (
    ChamadaPublicaSerializer,
    ChamarProximoSerializer,
    PacienteSerializer,
    PainelSerializer,
    RecursosAtendimentoSerializer,
)


class PacienteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Administração da fila (somente administrador autenticado).

    POST   /api/pacientes/       cadastra um paciente
    GET    /api/pacientes/       lista (filtro opcional: ?status=aguardando)
    DELETE /api/pacientes/{id}/  remove da fila (o registro fica como "removido")
    """

    serializer_class = PacienteSerializer

    def get_queryset(self):
        qs = Paciente.objects.all()
        status_filtro = self.request.query_params.get("status")
        if status_filtro:
            qs = qs.filter(status=status_filtro)
        return qs

    def perform_create(self, serializer):
        serializer.instance = services.cadastrar_paciente(serializer.validated_data["nome"])

    def destroy(self, request, *args, **kwargs):
        paciente = get_object_or_404(Paciente, pk=kwargs["pk"])
        try:
            services.remover_paciente(paciente.pk)
        except services.PacienteJaRemovidoError:
            return Response(
                {"detail": "Este paciente já foi removido da fila."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChamarProximoView(APIView):
    """POST /api/chamar-proximo/  {"sala": "3", "medico": "Dra. Ana"}"""

    def post(self, request):
        entrada = ChamarProximoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            chamada = services.chamar_proximo(**entrada.validated_data)
        except services.FilaVaziaError:
            return Response(
                {"detail": "Não há pacientes aguardando."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(ChamadaPublicaSerializer(chamada).data, status=status.HTTP_201_CREATED)


class PainelView(APIView):
    """
    GET /api/painel/  (público, somente leitura)

    Devolve a contagem de aguardando, as últimas chamadas e o id da última
    chamada. Expõe apenas nome reduzido, sala e médico.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # público: ignora credenciais, nunca altera nada
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return Response(PainelSerializer(services.estado_do_painel()).data)


class RecursosAtendimentoView(APIView):
    """
    GET /api/recursos-atendimento/  (somente administrador autenticado)

    Devolve listas de salas e médicos ativos para preencher os seletores
    na tela de atendimento do administrador.
    """

    http_method_names = ["get", "head", "options"]

    def get(self, request):
        salas = Sala.objects.filter(ativo=True)
        medicos = Medico.objects.filter(ativo=True)
        serializer = RecursosAtendimentoSerializer(
            {"salas": salas, "medicos": medicos}
        )
        return Response(serializer.data)

