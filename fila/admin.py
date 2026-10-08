from django.contrib import admin

from .models import Chamada, Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "status", "chegada_em")
    list_filter = ("status",)
    search_fields = ("nome",)


@admin.register(Chamada)
class ChamadaAdmin(admin.ModelAdmin):
    list_display = ("paciente", "sala", "medico", "chamada_em")
