from django.contrib import admin

from .models import Chamada, Medico, Paciente, Sala


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "status", "chegada_em")
    list_filter = ("status",)
    search_fields = ("nome",)


@admin.register(Chamada)
class ChamadaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "sala", "medico", "chamada_em")


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)
