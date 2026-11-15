
from django.contrib import admin
from django.contrib.auth.models import User

from .models import Notificacao
from reservas.firebase_admin import enviar_notificacao
from reservas.models import Dispositivo, SubscricaoWebPush
from reservas.notificacoes import (
    enviar_notificacao_utilizador,
    enviar_webpush,
)


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):

    list_display = (
        "titulo",
        "tipo",
        "utilizador",
        "reserva",
        "lida",
        "criada_em",
    )

    list_filter = (
        "tipo",
        "lida",
        "criada_em",
    )

    search_fields = (
        "titulo",
        "mensagem",
    )

    readonly_fields = (
        "utilizador",
        "lida",
        "lida_em",
        "criada_em",
    )

    def save_model(self, request, obj, form, change):

        # Não repetir operações quando uma notificação é editada.
        if change:
            super().save_model(request, obj, form, change)
            return

        # Notificações de reserva pertencem ao utilizador da reserva.
        if obj.tipo == "reserva" and obj.reserva:
            obj.utilizador = obj.reserva.utilizador

        # Notificações gerais são distribuídas individualmente.
        elif obj.tipo in ["geral", "menu", "lembrete"]:
            obj.utilizador = None

        super().save_model(request, obj, form, change)

        # Geral, Menu e Lembrete:
        # criar um registo individual para cada conta ativa.
        if obj.tipo in ["geral", "menu", "lembrete"]:

            destinatarios = User.objects.filter(
                is_active=True
            )

            notificacoes = [
                Notificacao(
                    utilizador=utilizador,
                    titulo=obj.titulo,
                    mensagem=obj.mensagem,
                    tipo=obj.tipo,
                    reserva=obj.reserva,
                )
                for utilizador in destinatarios
            ]

            Notificacao.objects.bulk_create(notificacoes)

            print(
                "PROFISABORES — NOTIFICAÇÕES INTERNAS CRIADAS:",
                len(notificacoes)
            )

            # Manter envio Firebase para dispositivos ativos.
            dispositivos = Dispositivo.objects.filter(
                ativo=True,
                utilizador__isnull=False
            )

            enviados = 0

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

            # Manter envio Web Push.
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
        # enviar apenas ao utilizador associado.
        elif (
            obj.tipo == "reserva"
            and obj.utilizador
        ):

            enviados = enviar_notificacao_utilizador(
                obj.utilizador,
                obj.titulo,
                obj.mensagem
            )

        else:
            enviados = 0

        print(
            "PROFISABORES ADMIN — NOTIFICAÇÃO ENVIADA:",
            enviados
        )
