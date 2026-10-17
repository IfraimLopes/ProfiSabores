
from django.contrib import admin
from django.utils import timezone

from .models import (
    Reserva,
    ReservaExtra,
    Pagamento,
    Dispositivo,
)

from reservas.notificacoes import (
    enviar_notificacao_utilizador,
    enviar_notificacao_visitante,
)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nome",
        "telemovel",
        "curso",
        "item_reserva",
        "data",
        "hora",
        "preco_unitario",
        "total",
        "estado",
        "estado_pagamento",
        "criada_em",
    )

    list_filter = (
        "estado",
        "pagamento",
        "data",
        "hora",
        "curso",
    )

    search_fields = (
        "nome",
        "telemovel",
        "alergias",
        "ementa__descricao",
        "ementa__entrada__nome",
        "ementa__prato_principal__nome",
        "prato__nome",
        "sobremesa__nome",
        "curso__codigo",
        "utilizador__email",
    )

    readonly_fields = (
        "utilizador",
        "criada_em",
        "cancelada_em",
        "pago_em",
        "pago_por",
    )

    fieldsets = (

        (
            "👤 Dados do utilizador",
            {
                "fields": (
                    "utilizador",
                    "nome",
                    "telemovel",
                    "curso",
                )
            }
        ),

        (
            "🍽️ Refeição",
            {
                "fields": (
                    "ementa",
                    "prato",
                    "sobremesa",
                    "data",
                    "hora",
                )
            }
        ),

        (
            "⚠️ Alergias e restrições alimentares",
            {
                "fields": (
                    "alergias",
                )
            }
        ),

        (
            "💰 Valores",
            {
                "fields": (
                    "preco_unitario",
                    "total",
                )
            }
        ),

        (
            "💳 Pagamento",
            {
                "fields": (
                    "pagamento",
                    "pago_em",
                    "pago_por",
                )
            }
        ),

        (
            "📋 Estado da reserva",
            {
                "fields": (
                    "estado",
                    "criada_em",
                    "cancelada_em",
                )
            }
        ),
    )

    ordering = (
        "-data",
        "-hora",
        "-criada_em",
    )

    def item_reserva(self, obj):

        if obj.ementa:

            partes = []

            if obj.ementa.entrada:
                partes.append(
                    f"Entrada: {obj.ementa.entrada.nome}"
                )

            if obj.ementa.prato_principal:
                partes.append(
                    f"Prato: {obj.ementa.prato_principal.nome}"
                )

            if partes:
                return " | ".join(partes)

            return str(obj.ementa)

        if obj.prato:
            return obj.prato.nome

        if obj.sobremesa:
            return obj.sobremesa.nome

        return "—"

    item_reserva.short_description = "Refeição"

    def estado_pagamento(self, obj):

        try:
            pagamento = obj.pagamento_registo

            if pagamento.estado == "pago":
                return "✅ Pago"

            return "⏳ Pendente"

        except Pagamento.DoesNotExist:
            return "⚠️ Sem registo"

    estado_pagamento.short_description = "Pagamento"

    def save_model(self, request, obj, form, change):
        """
        Mantém temporariamente a compatibilidade com os campos
        antigos de pagamento da Reserva.

        Ao confirmar o pagamento:
        - regista a data/hora;
        - regista o administrador;
        - sincroniza o modelo Pagamento;
        - envia a notificação ao utilizador.
        """

        pagamento_anterior = None

        if obj.pk:

            try:
                reserva_anterior = Reserva.objects.get(pk=obj.pk)
                pagamento_anterior = reserva_anterior.pagamento

            except Reserva.DoesNotExist:
                pass

        pagamento_confirmado_agora = (
            obj.pagamento == "pago"
            and pagamento_anterior != "pago"
        )

        if obj.pagamento == "pago":

            if pagamento_anterior != "pago":
                obj.pago_em = timezone.now()
                obj.pago_por = request.user

        else:

            obj.pago_em = None
            obj.pago_por = None

        super().save_model(
            request,
            obj,
            form,
            change
        )

        # ==================================================
        # SINCRONIZAR PAGAMENTO
        # ==================================================

        pagamento, criado = Pagamento.objects.get_or_create(
            reserva=obj,
            defaults={
                "valor": obj.total,
                "estado": obj.pagamento,
            }
        )

        pagamento.valor = obj.total
        pagamento.estado = obj.pagamento

        if obj.pagamento == "pago":

            pagamento.pago_em = obj.pago_em
            pagamento.pago_por = obj.pago_por

        else:

            pagamento.pago_em = None
            pagamento.pago_por = None

        pagamento.save()

        # ==================================================
        # NOTIFICAÇÃO
        # ==================================================

        if pagamento_confirmado_agora:

            if obj.ementa and obj.ementa.prato_principal:
                item_reserva = obj.ementa.prato_principal.nome
            elif obj.ementa:
                item_reserva = str(obj.ementa)
            elif obj.prato:
                item_reserva = obj.prato.nome
            elif obj.sobremesa:
                item_reserva = obj.sobremesa.nome
            else:
                item_reserva = "a refeição"

            titulo_notificacao = "✅ Profisabores"
            mensagem_notificacao = (
                f"O pagamento da tua reserva de "
                f"{item_reserva} para "
                f"{obj.data.strftime('%d/%m/%Y')} "
                "foi confirmado."
            )

            print(
                "PROFISABORES DEBUG — "
                "A ENVIAR NOTIFICAÇÃO DE PAGAMENTO:",
                obj.id
            )

            if obj.utilizador:
                resultado_notificacao = enviar_notificacao_utilizador(
                    obj.utilizador,
                    titulo_notificacao,
                    mensagem_notificacao
                )
            else:
                resultado_notificacao = enviar_notificacao_visitante(
                    obj.visitante_token,
                    titulo_notificacao,
                    mensagem_notificacao
                )

            print(
                "PROFISABORES DEBUG — "
                "NOTIFICAÇÕES DE PAGAMENTO ENVIADAS:",
                resultado_notificacao
            )


@admin.register(ReservaExtra)
class ReservaExtraAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "reserva",
        "extra",
        "quantidade",
        "preco",
    )

    list_filter = (
        "extra__tipo",
    )

    search_fields = (
        "reserva__nome",
        "extra__nome",
        "extra__tipo",
    )

    autocomplete_fields = (
        "reserva",
        "extra",
    )


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "reserva",
        "valor",
        "estado",
        "pago_em",
        "pago_por",
        "criado_em",
    )

    list_filter = (
        "estado",
        "criado_em",
    )

    search_fields = (
        "reserva__nome",
        "reserva__telemovel",
        "reserva__utilizador__email",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
        "pago_em",
        "pago_por",
    )

    autocomplete_fields = (
        "reserva",
    )

    ordering = (
        "-criado_em",
    )


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "plataforma",
        "ativo",
        "criado_em",
        "atualizado_em",
    )

    list_filter = (
        "plataforma",
        "ativo",
    )

    search_fields = (
        "token",
    )

    ordering = (
        "-criado_em",
    )
