from django.db import models


class Notificacao(models.Model):

    TIPOS = [
        ("geral", "Geral"),
        ("reserva", "Reserva"),
        ("menu", "Menu"),
        ("lembrete", "Lembrete"),
    ]

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

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.titulo