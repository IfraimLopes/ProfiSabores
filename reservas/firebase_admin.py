import json
import logging
import os

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIREBASE_CREDENTIALS = os.path.join(
    BASE_DIR,
    "firebase",
    "profisabores-542c2-firebase-adminsdk-fbsvc-98a8eae0c3.json",
)


def _obter_credenciais():
    credenciais_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

    if credenciais_json:
        return credentials.Certificate(json.loads(credenciais_json))

    if os.path.isfile(FIREBASE_CREDENTIALS):
        return credentials.Certificate(FIREBASE_CREDENTIALS)

    raise RuntimeError("Credenciais Firebase não configuradas.")


def _obter_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    try:
        credencial = _obter_credenciais()
    except RuntimeError:
        logger.warning(
            "Firebase indisponível: credenciais não configuradas. "
            "As notificações estão desativadas."
        )
        return None

    return firebase_admin.initialize_app(credencial)


def enviar_notificacao(token, titulo, mensagem):
    app = _obter_app()

    if app is None:
        return None

    notificacao = messaging.Message(
        notification=messaging.Notification(
            title=titulo,
            body=mensagem,
        ),
        token=token,
    )

    return messaging.send(notificacao, app=app)
