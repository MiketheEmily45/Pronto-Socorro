from rest_framework import serializers

from .models import Chamada, Medico, Paciente, Sala


class PacienteSerializer(serializers.ModelSerializer):
    """Visão completa, só para o administrador."""

    class Meta:
        model = Paciente
        fields = ["id", "nome", "chegada_em", "status"]
        read_only_fields = ["id", "chegada_em", "status"]

    def validate_nome(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Informe o nome do paciente.")
        return valor


class ChamarProximoSerializer(serializers.Serializer):
    sala = serializers.CharField(max_length=20)
    medico = serializers.CharField(max_length=120)


class ChamadaPublicaSerializer(serializers.ModelSerializer):
    """Visão pública (LGPD): nome reduzido, sala e médico. Nada além disso."""

    paciente = serializers.CharField(source="paciente.nome_publico", read_only=True)

    class Meta:
        model = Chamada
        fields = ["id", "paciente", "sala", "medico", "chamada_em"]


class PainelSerializer(serializers.Serializer):
    aguardando = serializers.IntegerField()
    chamadas = ChamadaPublicaSerializer(many=True)
    ultima_chamada_id = serializers.IntegerField(allow_null=True)


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = ["id", "nome"]


class MedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medico
        fields = ["id", "nome"]


class RecursosAtendimentoSerializer(serializers.Serializer):
    salas = SalaSerializer(many=True)
    medicos = MedicoSerializer(many=True)

