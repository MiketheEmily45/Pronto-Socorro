from django.db import models


class Paciente(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO = "aguardando", "Aguardando"
        CHAMADO = "chamado", "Chamado"
        REMOVIDO = "removido", "Removido"

    nome = models.CharField(max_length=120)
    chegada_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.AGUARDANDO, db_index=True
    )

    class Meta:
        ordering = ["chegada_em", "id"]

    def __str__(self):
        return f"{self.nome} ({self.get_status_display()})"

    @property
    def nome_publico(self):
        """Nome reduzido para o painel público (LGPD): primeiro nome + inicial do último."""
        partes = self.nome.split()
        if len(partes) <= 1:
            return partes[0] if partes else ""
        return f"{partes[0]} {partes[-1][0].upper()}."


class Chamada(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="chamadas")
    sala = models.CharField(max_length=20)
    medico = models.CharField(max_length=120)
    chamada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-chamada_em", "-id"]

    def __str__(self):
        return f"{self.paciente.nome_publico} -> sala {self.sala} ({self.medico})"


class Sala(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def __str__(self):
        return self.nome


class Medico(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Médico"
        verbose_name_plural = "Médicos"

    def __str__(self):
        return self.nome
