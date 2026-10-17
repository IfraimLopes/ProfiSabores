import json
import os

import firebase_admin
from firebase_admin import credentials, messaging


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FIREBASE_CREDENTIALS = os.path.join(
    BASE_DIR,
    "firebase",
    "profisabores-542c2-firebase-adminsdk-fbsvc-98a8eae0c3.json",
)


def _obter_credenciais():
    """
    No Render, utiliza FIREBASE_CREDENTIALS_JSON.
    Localmente, utiliza o ficheiro Firebase existente.
    """
    credenciais_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

    if credenciais_json:
        dados = json.loads(credenciais_json)
        return credentials.Certificate(dados)

    if os.path.isfile(FIREBASE_CREDENTIALS):
        return credentials.Certificate(FIREBASE_CREDENTIALS)

    raise RuntimeError(
        "Credenciais Firebase não configuradas. "
        "Define FIREBASE_CREDENTIALS_JSON ou disponibiliza "
        "o ficheiro local de credenciais."
    )


if not firebase_admin._apps:
    firebase_admin.initialize_app(_obter_credenciais())


def enviar_notificacao(token, titulo, mensagem):
    notificacao = messaging.Message(
        notification=messaging.Notification(
            title=titulo,
            body=mensagem,
        ),
        token=token,
    )

    return messaging.send(notificacao)
