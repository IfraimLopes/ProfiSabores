from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from menu.models import Ementa
from reservas.models import Pagamento, Reserva

User = get_user_model()


class PainelRestauranteTests(TestCase):
    def setUp(self):
        self.utilizador = User.objects.create_user(
            username="restaurante_teste",
            password="teste-seguro-123",
        )
        grupo, _ = Group.objects.get_or_create(name="Restaurante")
        self.utilizador.groups.add(grupo)

        self.reserva = Reserva.objects.create(
            nome="Cliente Teste",
            telemovel="910000000",
            data=date.today(),
            hora="13:00",
            preco_unitario=Decimal("7.50"),
            total=Decimal("9.25"),
            estado="confirmada",
            pagamento="pendente",
        )

        self.client.force_login(self.utilizador)

    def test_grupo_restaurante_pode_consultar_painel(self):
        resposta = self.client.get(reverse("painel_restaurante"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Cliente Teste")
        self.assertContains(resposta, "9,25")

    def test_utilizador_sem_permissao_nao_acede_ao_painel(self):
        outro = User.objects.create_user(
            username="sem_acesso",
            password="teste-seguro-123",
        )
        self.client.force_login(outro)

        resposta = self.client.get(reverse("painel_restaurante"))
        self.assertEqual(resposta.status_code, 403)

    def test_marcar_pagamento_sincroniza_os_dois_modelos(self):
        resposta = self.client.post(
            reverse(
                "marcar_pagamento_restaurante",
                args=[self.reserva.pk],
            )
        )
        self.assertEqual(resposta.status_code, 302)

        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.pagamento, "pago")
        self.assertEqual(self.reserva.pago_por, self.utilizador)
        self.assertIsNotNone(self.reserva.pago_em)

        pagamento = Pagamento.objects.get(reserva=self.reserva)
        self.assertEqual(pagamento.estado, "pago")
        self.assertEqual(pagamento.valor, Decimal("9.25"))
        self.assertEqual(pagamento.pago_por, self.utilizador)
        self.assertIsNotNone(pagamento.pago_em)

    def test_segundo_pedido_nao_altera_registo_original_do_pagamento(self):
        url = reverse(
            "marcar_pagamento_restaurante",
            args=[self.reserva.pk],
        )

        primeira_resposta = self.client.post(url)
        self.assertEqual(primeira_resposta.status_code, 302)

        self.reserva.refresh_from_db()
        data_original = self.reserva.pago_em
        responsavel_original = self.reserva.pago_por

        outro_utilizador = User.objects.create_user(
            username="outro_funcionario",
            password="teste-seguro-456",
        )
        grupo = self.utilizador.groups.get(name="Restaurante")
        outro_utilizador.groups.add(grupo)
        self.client.force_login(outro_utilizador)

        segunda_resposta = self.client.post(url)
        self.assertEqual(segunda_resposta.status_code, 403)

        self.reserva.refresh_from_db()
        pagamento = Pagamento.objects.get(reserva=self.reserva)

        self.assertEqual(self.reserva.pago_em, data_original)
        self.assertEqual(self.reserva.pago_por, responsavel_original)
        self.assertEqual(pagamento.pago_em, data_original)
        self.assertEqual(pagamento.pago_por, responsavel_original)
        self.assertEqual(pagamento.valor, Decimal("9.25"))
        self.assertEqual(pagamento.estado, "pago")

    def test_nao_permite_pagar_reserva_cancelada(self):
        self.reserva.estado = "cancelada"
        self.reserva.save(update_fields=["estado"])

        resposta = self.client.post(
            reverse(
                "marcar_pagamento_restaurante",
                args=[self.reserva.pk],
            )
        )

        self.assertEqual(resposta.status_code, 403)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.pagamento, "pendente")
        self.assertFalse(
            Pagamento.objects.filter(reserva=self.reserva).exists()
        )

    def test_ativar_e_desativar_ementa(self):
        ementa = Ementa.objects.create(
            data_refeicao=date.today() + timedelta(days=1),
            descricao="Ementa de teste",
            preco_base_aluno=Decimal("5.00"),
            preco_base_staff=Decimal("6.00"),
            preco_base_visitante=Decimal("7.00"),
            publicada=True,
            ativa=True,
        )

        url = reverse(
            "alternar_ementa_restaurante",
            args=[ementa.pk],
        )

        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 302)

        ementa.refresh_from_db()
        self.assertFalse(ementa.ativa)
        self.assertTrue(ementa.publicada)

        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 302)

        ementa.refresh_from_db()
        self.assertTrue(ementa.ativa)
        self.assertTrue(ementa.publicada)

    def test_nao_permite_ativar_ementa_nao_publicada(self):
        ementa = Ementa.objects.create(
            data_refeicao=date.today() + timedelta(days=3),
            descricao="Ementa ainda não publicada",
            preco_base_aluno=Decimal("5.00"),
            preco_base_staff=Decimal("6.00"),
            preco_base_visitante=Decimal("7.00"),
            publicada=False,
            ativa=False,
        )

        resposta = self.client.post(
            reverse(
                "alternar_ementa_restaurante",
                args=[ementa.pk],
            )
        )

        self.assertEqual(resposta.status_code, 403)
        ementa.refresh_from_db()
        self.assertFalse(ementa.ativa)
        self.assertFalse(ementa.publicada)

    def test_alterar_ementa_exige_post(self):
        ementa = Ementa.objects.create(
            data_refeicao=date.today() + timedelta(days=2),
            descricao="Ementa de teste GET",
            preco_base_aluno=Decimal("5.00"),
            preco_base_staff=Decimal("6.00"),
            preco_base_visitante=Decimal("7.00"),
            publicada=True,
            ativa=True,
        )

        resposta = self.client.get(
            reverse(
                "alternar_ementa_restaurante",
                args=[ementa.pk],
            )
        )

        self.assertEqual(resposta.status_code, 405)
        ementa.refresh_from_db()
        self.assertTrue(ementa.ativa)

    def test_desativar_ementa_preserva_reservas_existentes(self):
        ementa = Ementa.objects.create(
            data_refeicao=date.today() + timedelta(days=1),
            descricao="Ementa com reserva existente",
            preco_base_aluno=Decimal("5.00"),
            preco_base_staff=Decimal("6.00"),
            preco_base_visitante=Decimal("7.00"),
            publicada=True,
            ativa=True,
        )

        self.reserva.ementa = ementa
        self.reserva.total = Decimal("9.25")
        self.reserva.estado = "confirmada"
        self.reserva.save(
            update_fields=["ementa", "total", "estado"]
        )

        resposta = self.client.post(
            reverse(
                "alternar_ementa_restaurante",
                args=[ementa.pk],
            )
        )

        self.assertEqual(resposta.status_code, 302)

        ementa.refresh_from_db()
        self.reserva.refresh_from_db()

        self.assertFalse(ementa.ativa)
        self.assertTrue(ementa.publicada)
        self.assertTrue(Reserva.objects.filter(pk=self.reserva.pk).exists())
        self.assertEqual(self.reserva.ementa_id, ementa.pk)
        self.assertEqual(self.reserva.total, Decimal("9.25"))
        self.assertEqual(self.reserva.estado, "confirmada")
