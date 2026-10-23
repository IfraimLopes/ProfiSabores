from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from reservas.models import Reserva

User = get_user_model()


class CancelamentoEstadoPreparacaoTests(TestCase):
    def setUp(self):
        self.utilizador = User.objects.create_user(
            username="aluno_cancelamento_teste",
            password="teste-seguro-123",
        )

        self.reserva = Reserva.objects.create(
            utilizador=self.utilizador,
            nome="Teste Cancelamento",
            telemovel="910000000",
            data=date.today(),
            hora="13:00",
            preco_unitario=Decimal("5.00"),
            total=Decimal("5.00"),
        )

        self.url = reverse(
            "cancelar_reserva",
            args=[self.reserva.pk],
        )

        self.client.force_login(self.utilizador)

    def test_nao_permite_cancelar_refeicao_feita(self):
        self.reserva.estado_preparacao = "feito"
        self.reserva.save(update_fields=["estado_preparacao"])

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("erro", resposta.json())

        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, "confirmada")
        self.assertEqual(self.reserva.estado_preparacao, "feito")

    def test_permite_cancelar_refeicao_em_processo(self):
        self.reserva.estado_preparacao = "em_processo"
        self.reserva.save(update_fields=["estado_preparacao"])

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["sucesso"])

        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, "cancelada")
        self.assertEqual(self.reserva.estado_preparacao, "em_processo")
        self.assertIsNotNone(self.reserva.cancelada_em)
