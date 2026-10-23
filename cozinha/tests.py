from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from reservas.models import Reserva


User = get_user_model()


class EstadoPreparacaoTests(TestCase):
    def setUp(self):
        self.reserva = Reserva.objects.create(
            nome="Teste Preparação",
            telemovel="910000000",
            data=date.today(),
            hora="13:00",
            preco_unitario=Decimal("5.00"),
            total=Decimal("5.00"),
        )

        self.url = reverse(
            "atualizar_estado_preparacao",
            args=[self.reserva.pk],
        )

    def test_reserva_nova_comeca_em_processo(self):
        self.assertEqual(
            self.reserva.estado_preparacao,
            "em_processo",
        )

    def test_cozinha_pode_marcar_feito_e_reverter(self):
        utilizador = User.objects.create_user(
            username="cozinha_teste",
            password="teste-seguro-123",
        )
        grupo, _ = Group.objects.get_or_create(name="Cozinha")
        utilizador.groups.add(grupo)
        self.client.force_login(utilizador)

        resposta = self.client.post(
            self.url,
            {"estado_preparacao": "feito"},
        )
        self.assertEqual(resposta.status_code, 302)

        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado_preparacao, "feito")

        resposta = self.client.post(
            self.url,
            {"estado_preparacao": "em_processo"},
        )
        self.assertEqual(resposta.status_code, 302)

        self.reserva.refresh_from_db()
        self.assertEqual(
            self.reserva.estado_preparacao,
            "em_processo",
        )

    def test_utilizador_sem_permissao_nao_altera_estado(self):
        utilizador = User.objects.create_user(
            username="aluno_teste",
            password="teste-seguro-123",
        )
        self.client.force_login(utilizador)

        resposta = self.client.post(
            self.url,
            {"estado_preparacao": "feito"},
        )

        self.assertEqual(resposta.status_code, 403)
        self.reserva.refresh_from_db()
        self.assertEqual(
            self.reserva.estado_preparacao,
            "em_processo",
        )

    def test_estado_invalido_e_rejeitado(self):
        utilizador = User.objects.create_user(
            username="cozinha_teste2",
            password="teste-seguro-123",
        )
        grupo, _ = Group.objects.get_or_create(name="Cozinha")
        utilizador.groups.add(grupo)
        self.client.force_login(utilizador)

        resposta = self.client.post(
            self.url,
            {"estado_preparacao": "invalido"},
        )

        self.assertEqual(resposta.status_code, 403)
        self.reserva.refresh_from_db()
        self.assertEqual(
            self.reserva.estado_preparacao,
            "em_processo",
        )
