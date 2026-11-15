from django.conf import settings
from django.db import models


class Notificacao(models.Model):

    TIPOS = [
        ("geral", "Geral"),
        ("reserva", "Reserva"),
        ("menu", "Menu"),
        ("lembrete", "Lembrete"),
    ]

    utilizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificacoes"
    )

    titulo = models.CharField(
        max_length=150
    )

    mensagem = models.TextField()

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default="geral"
    )

    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificacoes"
    )

    lida = models.BooleanField(
        default=False
    )

    lida_em = models.DateTimeField(
        null=True,
        blank=True
    )

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.titulo