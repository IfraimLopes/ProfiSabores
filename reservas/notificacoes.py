import json

from django.conf import settings

from pywebpush import webpush, WebPushException

from reservas.models import Dispositivo, SubscricaoWebPush
from reservas.firebase_admin import enviar_notificacao


def enviar_webpush(subscricoes, titulo, mensagem, url="/"):
    enviados = 0

    for subscricao in subscricoes:
        dados_subscricao = {
            "endpoint": subscricao.endpoint,
            "keys": {
                "p256dh": subscricao.p256dh,
                "auth": subscricao.auth,
            },
        }

        try:
            webpush(
                subscription_info=dados_subscricao,
                data=json.dumps({
                    "title": titulo,
                    "body": mensagem,
                    "url": url,
                }),
                vapid_private_key=str(
                    settings.WEBPUSH_VAPID_PRIVATE_KEY_PATH
                ),
                vapid_claims={
                    "sub": settings.WEBPUSH_VAPID_SUBJECT,
                },
            )
            enviados += 1

        except WebPushException as erro:
            print(
                "Profisabores: erro Web Push:",
                erro
            )

            resposta = getattr(erro, "response", None)

            if resposta is not None and resposta.status_code in (404, 410):
                subscricao.ativo = False
                subscricao.save(update_fields=["ativo"])

        except Exception as erro:
            print(
                "Profisabores: erro inesperado Web Push:",
                erro
            )

    return enviados


def enviar_notificacao_utilizador(utilizador, titulo, mensagem):
    if utilizador is None:
        return 0

    enviados = 0

    dispositivos = Dispositivo.objects.filter(
        utilizador=utilizador,
        ativo=True
    )

    for dispositivo in dispositivos:
        try:
            enviar_notificacao(
                dispositivo.token,
                titulo,
                mensagem
            )
            enviados += 1

        except Exception as erro:
            print(
                "Profisabores: erro Firebase:",
                erro
            )

    subscricoes = SubscricaoWebPush.objects.filter(
        utilizador=utilizador,
        ativo=True
    )

    enviados += enviar_webpush(
        subscricoes,
        titulo,
        mensagem
    )

    return enviados


def enviar_notificacao_visitante(token_visitante, titulo, mensagem):
    if not token_visitante:
        return 0

    subscricoes = SubscricaoWebPush.objects.filter(
        visitante_token=token_visitante,
        ativo=True
    )

    return enviar_webpush(
        subscricoes,
        titulo,
        mensagem
    )
