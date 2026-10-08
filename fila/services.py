"""
Regras de negócio da fila, isoladas das views.

Toda alteração da fila passa por aqui. Se a arquitetura definir um canal de
tempo real (WebSocket, SSE, etc.), basta disparar a notificação dentro destas
funções, sem mexer nas views.
"""

from django.db import transaction

from .models import Chamada, Paciente


class FilaVaziaError(Exception):
    """Não há ninguém aguardando para ser chamado."""


class PacienteJaRemovidoError(Exception):
    """O paciente já tinha sido removido da fila."""


def cadastrar_paciente(nome):
    return Paciente.objects.create(nome=nome.strip())


@transaction.atomic
def remover_paciente(paciente_id):
    paciente = Paciente.objects.select_for_update().get(pk=paciente_id)
    if paciente.status == Paciente.Status.REMOVIDO:
        raise PacienteJaRemovidoError()
    paciente.status = Paciente.Status.REMOVIDO
    paciente.save(update_fields=["status"])
    return paciente


@transaction.atomic
def chamar_proximo(sala, medico):
    """Chama o paciente que está há mais tempo aguardando (ordem de chegada)."""
    paciente = (
        Paciente.objects.select_for_update()
        .filter(status=Paciente.Status.AGUARDANDO)
        .order_by("chegada_em", "id")
        .first()
    )
    if paciente is None:
        raise FilaVaziaError()
    paciente.status = Paciente.Status.CHAMADO
    paciente.save(update_fields=["status"])
    return Chamada.objects.create(paciente=paciente, sala=sala.strip(), medico=medico.strip())


def estado_do_painel(limite_chamadas=5):
    """Dados públicos do painel: só o necessário para a chamada (LGPD)."""
    aguardando = Paciente.objects.filter(status=Paciente.Status.AGUARDANDO).count()
    chamadas = list(
        Chamada.objects.select_related("paciente")
        .filter(paciente__status=Paciente.Status.CHAMADO)[:limite_chamadas]
    )
    ultima = Chamada.objects.order_by("-id").values_list("id", flat=True).first()
    return {
        "aguardando": aguardando,
        "chamadas": chamadas,
        # O painel compara este valor com o anterior: se mudou, toca o aviso sonoro.
        "ultima_chamada_id": ultima,
    }
