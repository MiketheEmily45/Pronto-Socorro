from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    ChamarProximoView,
    PacienteViewSet,
    PainelView,
    RecursosAtendimentoView,
)

router = DefaultRouter()
router.register("pacientes", PacienteViewSet, basename="paciente")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="token"),
    path("chamar-proximo/", ChamarProximoView.as_view(), name="chamar-proximo"),
    path("painel/", PainelView.as_view(), name="painel"),
    path("recursos-atendimento/", RecursosAtendimentoView.as_view(), name="recursos-atendimento"),
    path("", include(router.urls)),
]
