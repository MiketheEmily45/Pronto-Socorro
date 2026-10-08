from django.contrib import admin
from django.urls import include, path

from fila.views import AdminFilaView, PainelPublicoView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin-fila/", AdminFilaView.as_view(), name="admin-fila"),
    path("painel/", PainelPublicoView.as_view(), name="painel-publico"),
    path("api/", include("fila.urls")),
]

