
from django.db import models


class Curso(models.Model):

    codigo = models.CharField(
        max_length=20,
        unique=True
    )

    nome = models.CharField(
        max_length=100
    )

    ano = models.PositiveIntegerField()

    def __str__(self):
        return self.codigo


class ItemEmenta(models.Model):

    nome = models.CharField(
        max_length=100
    )

    descricao = models.TextField(
        blank=True
    )

    alergenios = models.TextField(
        blank=True,
        help_text="Indique os alergénios presentes neste alimento."
    )

    imagem = models.ImageField(
        upload_to="ementas/itens/",
        blank=True,
        null=True
    )

    ativo = models.BooleanField(
        default=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nome


class Ementa(models.Model):

    data_refeicao = models.DateField(
        verbose_name="Data da refeição"
    )

    descricao = models.TextField(
        blank=True
    )

    entrada = models.ForeignKey(
        ItemEmenta,
        on_delete=models.PROTECT,
        related_name="ementas_como_entrada",
        null=True,
        blank=True
    )

    prato_principal = models.ForeignKey(
        ItemEmenta,
        on_delete=models.PROTECT,
        related_name="ementas_como_prato_principal",
        null=True,
        blank=True
    )

    preco_base_aluno = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    preco_base_staff = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    preco_base_visitante = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    publicada = models.BooleanField(
        default=False
    )

    ativa = models.BooleanField(
        default=True
    )

    publicada_em = models.DateTimeField(
        null=True,
        blank=True
    )

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizada_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["data_refeicao", "id"]
        verbose_name = "Ementa"
        verbose_name_plural = "Ementas"

    def __str__(self):
        return f"Ementa de {self.data_refeicao.strftime('%d/%m/%Y')}"


class Extra(models.Model):

    ementa = models.ForeignKey(
        Ementa,
        on_delete=models.CASCADE,
        related_name="extras"
    )

    tipo = models.CharField(
        max_length=100,
        help_text="Ex.: Sobremesa, Café, Fruta, Bebida..."
    )

    nome = models.CharField(
        max_length=100
    )

    descricao = models.TextField(
        blank=True
    )

    imagem = models.ImageField(
        upload_to="ementas/extras/",
        blank=True,
        null=True
    )

    alergenios = models.TextField(
        blank=True,
        help_text="Indique os alergénios presentes neste extra."
    )

    preco_aluno = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    preco_staff = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    preco_visitante = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    ativo = models.BooleanField(
        default=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.tipo} - {self.nome}"


class Prato(models.Model):

    nome = models.CharField(
        max_length=100
    )

    descricao = models.TextField()

    preco_aluno = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    preco_profissional = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    imagem = models.ImageField(
        upload_to="pratos/"
    )

    data = models.DateField(
        default="2026-09-15"
    )

    disponivel = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.nome


class BannerHome(models.Model):

    POSICOES = [
        ("topo", "Topo"),
        ("fim", "Fim"),
    ]

    posicao = models.CharField(
        max_length=10,
        choices=POSICOES
    )

    imagem = models.ImageField(
        upload_to="banners/"
    )

    ordem = models.PositiveIntegerField(
        default=1
    )

    ativo = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.get_posicao_display()} - Imagem {self.ordem}"

    class Meta:
        ordering = ["posicao", "ordem"]
        verbose_name = "Banner da Home"
        verbose_name_plural = "Banners da Home"


class Sobremesa(models.Model):

    nome = models.CharField(
        max_length=100
    )

    descricao = models.TextField()

    preco_aluno = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    preco_profissional = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    imagem = models.ImageField(
        upload_to="sobremesas/"
    )

    data = models.DateField()

    disponivel = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.nome

