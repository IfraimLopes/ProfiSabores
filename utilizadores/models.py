
from django.db import models
from django.contrib.auth.models import User


IDIOMAS = [
    ("pt-pt", "Português"),
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
]


class Perfil(models.Model):
    """Modelo antigo, mantido temporariamente durante a migração."""

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
    nome_completo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TIPOS_UTILIZADOR)
    idioma = models.CharField(
        max_length=10,
        choices=IDIOMAS,
        default="pt-pt",
    )
    telemovel = models.CharField(max_length=20)
    sexo = models.CharField(max_length=20, choices=SEXOS, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    curso = models.ForeignKey(
        "menu.Curso",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfis"
    )
    verificado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    @property
    def escalao_preco(self):
        return "aluno" if self.tipo == "aluno" else "profissional"

    def __str__(self):
        return f"{self.nome_completo} - {self.get_tipo_display()}"


class Aluno(models.Model):
    utilizador = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="aluno"
    )
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    curso = models.ForeignKey(
        "menu.Curso",
        on_delete=models.PROTECT,
        related_name="alunos"
    )

    def __str__(self):
        return self.nome


class Staff(models.Model):
    utilizador = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff"
    )
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nome


class PreferenciasUtilizador(models.Model):
    utilizador = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preferencias_utilizador"
    )
    idioma = models.CharField(
        max_length=10,
        choices=IDIOMAS,
        default="pt-pt",
    )

    def __str__(self):
        return f"Preferências de {self.utilizador.username}"


class CodigoVerificacao(models.Model):
    FINALIDADES = [
        ("registo", "Registo"),
        ("login", "Login"),
        ("recuperacao", "Recuperação"),
    ]

    email = models.EmailField()
    codigo = models.CharField(max_length=6)
    finalidade = models.CharField(max_length=20, choices=FINALIDADES)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    usado = models.BooleanField(default=False)
    tentativas = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.email} - {self.finalidade} - [PROTEGIDO]"
