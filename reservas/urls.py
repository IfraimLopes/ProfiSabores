from django.urls import path

from .views import (
    pagina_reservas,
    criar_reserva,
    minhas_reservas,
    cancelar_reserva,
    registar_dispositivo,
    registar_subscricao_webpush,
)


urlpatterns = [

    path(
        "",
        pagina_reservas,
        name="pagina_reservas"
    ),

    path(
        "api/",
        minhas_reservas,
        name="minhas_reservas"
    ),

    path(
        "criar/",
        criar_reserva,
        name="criar_reserva"
    ),

    path(
        "cancelar/<int:reserva_id>/",
        cancelar_reserva,
        name="cancelar_reserva"
    ),

    path(
        "dispositivo/",
        registar_dispositivo,
        name="registar_dispositivo"
    ),

    path(
    "webpush/",
    registar_subscricao_webpush,
    name="registar_subscricao_webpush"
),
]