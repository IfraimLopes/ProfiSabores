from django.urls import path

from .views import painel_cozinha, atualizar_estado_preparacao


urlpatterns = [
    path("", painel_cozinha, name="painel_cozinha"),
    path(
        "reserva/<int:reserva_id>/preparacao/",
        atualizar_estado_preparacao,
        name="atualizar_estado_preparacao",
    ),
]