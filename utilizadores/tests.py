from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User

from menu.models import Curso
from .models import Aluno, Staff, EmailAutorizado, CodigoVerificacao
from django.utils import timezone
from datetime import timedelta
from .views import obter_utilizador_aluno_staff


class TestWhitelistLogin(TestCase):

    def setUp(self):
        self.curso = Curso.objects.create(
            codigo="TESTE",
            nome="Curso de Teste",
            ano=2026,
        )

    def criar_aluno(self, email, ativo=True):
        utilizador = User.objects.create_user(
            username="aluno_teste",
            email=email,
            password="Teste123!",
            is_active=ativo,
        )

        Aluno.objects.create(
            utilizador=utilizador,
            nome="Aluno de Teste",
            email=email,
            curso=self.curso,
        )

        return utilizador

    def criar_staff(self, email, ativo=True):
        utilizador = User.objects.create_user(
            username="staff_teste",
            email=email,
            password="Teste123!",
            is_active=ativo,
        )

        Staff.objects.create(
            utilizador=utilizador,
            nome="Staff de Teste",
            email=email,
        )

        return utilizador

    def test_aluno_autorizado_e_ativo(self):
        email = "aluno@alunos.profitecla.pt"
        utilizador = self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=True,
        )

        self.assertEqual(
            obter_utilizador_aluno_staff(email),
            utilizador,
        )

    def test_staff_autorizado_e_ativo(self):
        email = "staff@professores.profitecla.pt"
        utilizador = self.criar_staff(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="staff",
            ativo=True,
        )

        self.assertEqual(
            obter_utilizador_aluno_staff(email),
            utilizador,
        )

    def test_email_sem_whitelist_e_rejeitado(self):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        self.assertIsNone(
            obter_utilizador_aluno_staff(email)
        )

    def test_email_inativo_na_whitelist_e_rejeitado(self):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=False,
        )

        self.assertIsNone(
            obter_utilizador_aluno_staff(email)
        )

    def test_tipo_incorreto_e_rejeitado(self):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="staff",
            ativo=True,
        )

        self.assertIsNone(
            obter_utilizador_aluno_staff(email)
        )

    def test_utilizador_inativo_e_rejeitado(self):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email, ativo=False)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=True,
        )

        self.assertIsNone(
            obter_utilizador_aluno_staff(email)
        )


    def criar_codigo_login_teste(self):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=True,
        )

        return CodigoVerificacao.objects.create(
            email=email,
            codigo="123456",
            finalidade="login",
            expira_em=timezone.now() + timedelta(minutes=10),
        )

    def test_quinta_tentativa_invalida_codigo(self):
        codigo = self.criar_codigo_login_teste()

        for tentativa in range(5):
            resposta = self.client.post(
                "/utilizadores/api/verificar-login/",
                {
                    "email": codigo.email,
                    "codigo": "000000",
                },
            )

        codigo.refresh_from_db()

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(codigo.tentativas, 5)
        self.assertTrue(codigo.usado)
        self.assertIn(
            "Limite de tentativas atingido",
            resposta.json()["erro"],
        )

    def test_codigo_invalidado_nao_pode_ser_reutilizado(self):
        codigo = self.criar_codigo_login_teste()

        for _ in range(5):
            self.client.post(
                "/utilizadores/api/verificar-login/",
                {
                    "email": codigo.email,
                    "codigo": "000000",
                },
            )

        resposta = self.client.post(
            "/utilizadores/api/verificar-login/",
            {
                "email": codigo.email,
                "codigo": "123456",
            },
        )

        codigo.refresh_from_db()

        self.assertEqual(resposta.status_code, 400)
        self.assertTrue(codigo.usado)
        self.assertEqual(codigo.tentativas, 5)
        self.assertIn(
            "Não existe um código",
            resposta.json()["erro"],
        )


    @patch("utilizadores.views.send_mail")
    @patch("utilizadores.views.gerar_codigo", return_value="654321")
    def test_login_autorizado_cria_codigo_e_envia_email(
        self, mock_gerar, mock_send
    ):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=True,
        )

        resposta = self.client.post(
            "/utilizadores/api/login/",
            {"email": email},
        )

        codigo = CodigoVerificacao.objects.get(
            email=email,
            finalidade="login",
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(codigo.codigo, "654321")
        self.assertFalse(codigo.usado)
        self.assertTrue(
            9 * 60 <=
            (codigo.expira_em - timezone.now()).total_seconds()
            <= 10 * 60
        )
        mock_gerar.assert_called_once()
        mock_send.assert_called_once()

    @patch("utilizadores.views.send_mail")
    def test_login_sem_whitelist_nao_cria_codigo(self, mock_send):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        resposta = self.client.post(
            "/utilizadores/api/login/",
            {"email": email},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(
            CodigoVerificacao.objects.filter(email=email).exists()
        )
        mock_send.assert_not_called()

    @patch("utilizadores.views.send_mail")
    @patch("utilizadores.views.gerar_codigo", return_value="654321")
    def test_novo_login_invalida_codigos_anteriores(
        self, mock_gerar, mock_send
    ):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=True,
        )

        codigo_antigo = CodigoVerificacao.objects.create(
            email=email,
            codigo="111111",
            finalidade="login",
            expira_em=timezone.now() + timedelta(minutes=10),
        )

        self.client.post(
            "/utilizadores/api/login/",
            {"email": email},
        )

        codigo_antigo.refresh_from_db()

        self.assertTrue(codigo_antigo.usado)
        self.assertEqual(
            CodigoVerificacao.objects.filter(
                email=email,
                finalidade="login",
                usado=False,
            ).count(),
            1,
        )


    @patch("utilizadores.views.send_mail")
    def test_login_whitelist_inativa_nao_cria_codigo(self, mock_send):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=False,
        )

        resposta = self.client.post(
            "/utilizadores/api/login/",
            {"email": email},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(
            CodigoVerificacao.objects.filter(email=email).exists()
        )
        mock_send.assert_not_called()

    @patch("utilizadores.views.send_mail")
    def test_login_tipo_incorreto_nao_cria_codigo(self, mock_send):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email)

        EmailAutorizado.objects.create(
            email=email,
            tipo="staff",
            ativo=True,
        )

        resposta = self.client.post(
            "/utilizadores/api/login/",
            {"email": email},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(
            CodigoVerificacao.objects.filter(email=email).exists()
        )
        mock_send.assert_not_called()

    @patch("utilizadores.views.send_mail")
    def test_login_conta_inativa_nao_cria_codigo(self, mock_send):
        email = "aluno@alunos.profitecla.pt"
        self.criar_aluno(email, ativo=False)

        EmailAutorizado.objects.create(
            email=email,
            tipo="aluno",
            ativo=True,
        )

        resposta = self.client.post(
            "/utilizadores/api/login/",
            {"email": email},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(
            CodigoVerificacao.objects.filter(email=email).exists()
        )
        mock_send.assert_not_called()
