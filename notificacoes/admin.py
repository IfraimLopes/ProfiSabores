from django.contrib import admin

from .models import Notificacao
from reservas.firebase_admin import enviar_notificacao
from reservas.models import Dispositivo, SubscricaoWebPush
from reservas.notificacoes import (enviar_notificacao_utilizador, enviar_webpush)


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):

    list_display = (
        "titulo",
        "tipo",
        "reserva",
        "criada_em",
    )

    list_filter = (
        "tipo",
        "criada_em",
    )

    search_fields = (
        "titulo",
        "mensagem",
    )

    readonly_fields = (
        "criada_em",
    )

    def save_model(self, request, obj, form, change):

        super().save_model(
            request,
            obj,
            form,
            change
        )

        enviados = 0

        # Geral, Menu e Lembrete:
        # enviar para todos os dispositivos ativos.
        if obj.tipo in [
            "geral",
            "menu",
            "lembrete",
        ]:

            dispositivos = Dispositivo.objects.filter(
                ativo=True,
                utilizador__isnull=False
            )

            for dispositivo in dispositivos:

                try:

                    enviar_notificacao(
                        dispositivo.token,
                        obj.titulo,
                        obj.mensagem
                    )

                    enviados += 1

                except Exception as erro:

                    print(
                        "Profisabores: erro ao enviar notificação:",
                        erro
                    )

            # Enviar também por Web Push para todas as subscrições ativas.
            subscricoes_webpush = SubscricaoWebPush.objects.filter(
                ativo=True
            )

            enviados_webpush = enviar_webpush(
                subscricoes_webpush,
                obj.titulo,
                obj.mensagem
            )

            enviados += enviados_webpush

            print(
                "PROFISABORES ADMIN — WEB PUSH ENVIADAS:",
                enviados_webpush
            )

        # Reserva:
        # enviar apenas para o utilizador da reserva.
        elif (
            obj.tipo == "reserva"
            and obj.reserva
            and obj.reserva.utilizador
        ):

            enviados = enviar_notificacao_utilizador(
                obj.reserva.utilizador,
                obj.titulo,
                obj.mensagem
            )

        print(
            "PROFISABORES ADMIN — NOTIFICAÇÃO ENVIADA:",
            enviados
        )