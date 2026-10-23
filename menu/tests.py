from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from menu.views import obter_preco_ementa, obter_preco_extra


class PrecosPorTipoUtilizadorTests(SimpleTestCase):
    def setUp(self):
        self.ementa = SimpleNamespace(
            preco_base_aluno=Decimal("4.00"),
            preco_base_staff=Decimal("5.00"),
            preco_base_visitante=Decimal("6.00"),
        )

        self.extra = SimpleNamespace(
            preco_aluno=Decimal("0.50"),
            preco_staff=Decimal("0.75"),
            preco_visitante=Decimal("1.00"),
        )

    def test_preco_ementa_por_tipo(self):
        self.assertEqual(
            obter_preco_ementa(self.ementa, "aluno"),
            Decimal("4.00"),
        )
        self.assertEqual(
            obter_preco_ementa(self.ementa, "staff"),
            Decimal("5.00"),
        )
        self.assertEqual(
            obter_preco_ementa(self.ementa, "visitante"),
            Decimal("6.00"),
        )

    def test_preco_extra_por_tipo(self):
        self.assertEqual(
            obter_preco_extra(self.extra, "aluno"),
            Decimal("0.50"),
        )
        self.assertEqual(
            obter_preco_extra(self.extra, "staff"),
            Decimal("0.75"),
        )
        self.assertEqual(
            obter_preco_extra(self.extra, "visitante"),
            Decimal("1.00"),
        )
