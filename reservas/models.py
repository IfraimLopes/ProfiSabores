
from django.db import models
from django.contrib.auth.models import User
from menu.models import Curso, Prato, Sobremesa, Ementa, Extra


class Reserva(models.Model):

    ESTADOS = [
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
    ]

       # ==============================
    # ESTADO DA PREPARAÇÃO
    # ==============================


    ESTADOS_PREPARACAO = [
        ("em_processo", "Em processo"),
        ("feito", "Feito"),
    ]


    PAGAMENTOS = [
        ("pendente", "Pendente"),
        ("pago", "Pago"),
    ]

    utilizador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="reservas",
        null=True,
        blank=True
    )


    # Identificação persistente das reservas de visitantes
    visitante_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True
    )

    alergias = models.TextField(
        blank=True,
        default=""
    )

    nome = models.CharField(
        max_length=100
    )

    telemovel = models.CharField(
        max_length=20
    )

    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name="reservas",
        null=True,
        blank=True
    )

    # ==============================
    # NOVA ESTRUTURA DE EMENTA
    # ==============================

    ementa = models.ForeignKey(
        Ementa,
        on_delete=models.PROTECT,
        related_name="reservas",
        null=True,
        blank=True
    )

    # ==============================
    # ESTRUTURA ANTIGA
    # Mantida temporariamente para
    # preservar as reservas existentes
    # ==============================

    prato = models.ForeignKey(
        Prato,
        on_delete=models.PROTECT,
        related_name="reservas",
        null=True,
        blank=True
    )

    sobremesa = models.ForeignKey(
        Sobremesa,
        on_delete=models.PROTECT,
        related_name="reservas",
        null=True,
        blank=True
    )

    # ==============================
    # DATA / HORA
    # ==============================

    data = models.DateField()

    hora = models.TimeField(
        default="13:00"
    )

    # ==============================
    # PREÇOS
    # ==============================

    preco_unitario = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    total = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    # ==============================
    # ESTADO
    # ==============================

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="confirmada"
    )

    # ==============================
    # ESTADO DA PREPARAÇÃO
    # ==============================

    estado_preparacao = models.CharField(
        max_length=20,
        choices=ESTADOS_PREPARACAO,
        default="em_processo"
    )

    # ==============================
    # PAGAMENTO
    # Mantido temporariamente
    # ==============================

    pagamento = models.CharField(
        max_length=20,
        choices=PAGAMENTOS,
        default="pendente"
    )

    pago_em = models.DateTimeField(
        null=True,
        blank=True
    )

    pago_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagamentos_confirmados"
    )

    # ==============================
    # DATAS
    # ==============================

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    cancelada_em = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):

        if self.ementa:
            item = f"Ementa de {self.ementa.data_refeicao.strftime('%d/%m/%Y')}"

        elif self.prato:
            item = self.prato.nome

        elif self.sobremesa:
            item = self.sobremesa.nome

        else:
            item = "Item não definido"

        return f"{self.nome} - {item}"


class ReservaExtra(models.Model):

    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name="extras"
    )

    extra = models.ForeignKey(
        Extra,
        on_delete=models.PROTECT,
        related_name="reservas"
    )

    # Preço congelado no momento da marcação.
    # Se o preço do Extra mudar posteriormente,
    # a reserva antiga mantém o preço original.
    preco = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    quantidade = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return f"{self.reserva} - {self.extra.nome}"


class Dispositivo(models.Model):

    utilizador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="dispositivos",
        null=True,
        blank=True
    )

    visitante_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True
    )

    PLATAFORMAS = [
        ("ios", "iOS"),
        ("android", "Android"),
    ]

    token = models.TextField(
        unique=True
    )

    plataforma = models.CharField(
        max_length=20,
        choices=PLATAFORMAS
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
        return f"{self.plataforma} - {self.token[:20]}"

class Pagamento(models.Model):

    ESTADOS = [
        ("pendente", "Pendente"),
        ("pago", "Pago"),
    ]

    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.CASCADE,
        related_name="pagamento_registo"
    )

    valor = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pendente"
    )

    pago_em = models.DateTimeField(
        null=True,
        blank=True
    )

    pago_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagamentos_registados"
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Pagamento #{self.id} - {self.reserva.nome} - {self.valor}€"

class SubscricaoWebPush(models.Model):

    utilizador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscricoes_webpush",
        null=True,
        blank=True
    )

    visitante_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True
    )

    endpoint = models.TextField(
        unique=True
    )

    p256dh = models.TextField()

    auth = models.TextField()

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
        if self.utilizador_id:
            identificacao = self.utilizador.username
        elif self.visitante_token:
            identificacao = "Visitante"
        else:
            identificacao = "Sem identificação"

        return f"Web Push - {identificacao}"