from django.urls import path

from .views import (
    painel_restaurante,
    marcar_pagamento,
    alternar_ementa,
)

urlpatterns = [
    path("", painel_restaurante, name="painel_restaurante"),
    path(
        "reserva/<int:reserva_id>/pagar/",
        marcar_pagamento,
        name="marcar_pagamento_restaurante",
    ),
    path(
        "ementa/<int:ementa_id>/alternar/",
        alternar_ementa,
        name="alternar_ementa_restaurante",
    ),
]
