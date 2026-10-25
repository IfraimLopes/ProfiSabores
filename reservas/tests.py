from unittest.mock import patch
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


class NotificacoesFCMTests(TestCase):
    def setUp(self):
        from reservas.models import Dispositivo
        self.Dispositivo = Dispositivo
        self.dispositivo = Dispositivo.objects.create(
            token="token-fcm-teste",
            plataforma="android",
            ativo=True,
            visitante_token="visitante-token-teste",
        )

    @patch("reservas.notificacoes.enviar_notificacao")
    @patch("reservas.notificacoes.enviar_webpush", return_value=0)
    def test_visitante_nao_conta_envio_quando_firebase_devolve_none(
        self, mock_webpush, mock_fcm
    ):
        mock_fcm.return_value = None

        from reservas.notificacoes import enviar_notificacao_visitante
        enviados = enviar_notificacao_visitante(
            "visitante-token-teste", "Teste", "Mensagem"
        )

        self.assertEqual(enviados, 0)
        mock_fcm.assert_called_once_with(
            "token-fcm-teste", "Teste", "Mensagem"
        )

    @patch("reservas.notificacoes.enviar_notificacao")
    @patch("reservas.notificacoes.enviar_webpush", return_value=0)
    def test_visitante_conta_envio_quando_firebase_confirma(
        self, mock_webpush, mock_fcm
    ):
        mock_fcm.return_value = "projects/test/messages/123"

        from reservas.notificacoes import enviar_notificacao_visitante
        enviados = enviar_notificacao_visitante(
            "visitante-token-teste", "Teste", "Mensagem"
        )

        self.assertEqual(enviados, 1)


class RegistoDispositivoVisitanteTests(TestCase):
    def test_regista_dispositivo_anonimo_com_cookie_visitante(self):
        from reservas.models import Dispositivo

        resposta = self.client.post(
            reverse("registar_dispositivo"),
            {
                "token": "teste-fcm-visitante-local",
                "plataforma": "android",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.json()["sucesso"])
        self.assertIn("profisabores_visitante", resposta.cookies)

        dispositivo = Dispositivo.objects.get(
            token="teste-fcm-visitante-local"
        )
        self.assertIsNone(dispositivo.utilizador)
        self.assertEqual(dispositivo.plataforma, "android")
        self.assertTrue(dispositivo.visitante_token)
        self.assertEqual(
            dispositivo.visitante_token,
            resposta.cookies["profisabores_visitante"].value,
        )
