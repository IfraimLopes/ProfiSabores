from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):

    TIPOS_UTILIZADOR = [
        ("aluno", "Aluno"),
        ("staff", "Staff"),
    ]

    SEXOS = [
        ("masculino", "Masculino"),
        ("feminino", "Feminino"),
        ("outro", "Outro"),
    ]

    utilizador = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil"
    )

    nome_completo = models.CharField(
        max_length=150
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_UTILIZADOR
    )

    telemovel = models.CharField(
        max_length=20
    )

    sexo = models.CharField(
        max_length=20,
        choices=SEXOS,
        blank=True
    )
    data_nascimento = models.DateField(
        null=True,
        blank=True
    )

    curso = models.ForeignKey(
        "menu.Curso",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfis"
    )

    verificado = models.BooleanField(
        default=False
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    @property
    def escalão_preco(self):
        if self.tipo == "aluno":
            return "aluno"

        return "profissional"

    def __str__(self):
        return f"{self.nome_completo} - {self.get_tipo_display()}"


class CodigoVerificacao(models.Model):

    FINALIDADES = [
        ("registo", "Registo"),
        ("login", "Login"),
        ("recuperacao", "Recuperação"),
    ]

    email = models.EmailField()

    codigo = models.CharField(
        max_length=6
    )

    finalidade = models.CharField(
        max_length=20,
        choices=FINALIDADES
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    expira_em = models.DateTimeField()

    usado = models.BooleanField(
        default=False
    )

    tentativas = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.email} - {self.finalidade} - {self.codigo}"
