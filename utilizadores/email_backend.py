import base64
import json
import os
from pathlib import Path

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


GMAIL_SCOPE = ["https://www.googleapis.com/auth/gmail.send"]


class GmailAPIEmailBackend(BaseEmailBackend):

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.service = None

    def _get_service(self):
        if self.service is not None:
            return self.service

        token_json = os.environ.get("GMAIL_TOKEN_JSON")

        if token_json:
            token_data = json.loads(token_json)
        else:
            token_path = (
                Path(settings.BASE_DIR)
                / "secrets"
                / "gmail-token.json"
            )
            token_data = json.loads(
                token_path.read_text(encoding="utf-8")
            )

        credentials = Credentials.from_authorized_user_info(
            token_data,
            GMAIL_SCOPE,
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials.valid:
            raise RuntimeError(
                "Credenciais Gmail inválidas ou expiradas."
            )

        self.service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        return self.service

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        try:
            service = self._get_service()
            enviados = 0

            for message in email_messages:
                if not message.recipients():
                    continue

                mime_message = message.message()

                raw_message = base64.urlsafe_b64encode(
                    mime_message.as_bytes()
                ).decode("utf-8")

                service.users().messages().send(
                    userId="me",
                    body={"raw": raw_message},
                ).execute()

                enviados += 1

            return enviados

        except Exception:
            if not self.fail_silently:
                raise

            return 0
