from django.conf import settings
from django.utils import translation

from .models import PreferenciasUtilizador


class IdiomaPerfilMiddleware:
    """
    Aplica o idioma guardado nas preferências do utilizador.
    Para visitantes, respeita o idioma selecionado no cookie.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        idioma = None

        if request.user.is_authenticated:
            try:
                preferencias = (
                    request.user.preferencias_utilizador
                )
                idioma = preferencias.idioma

            except PreferenciasUtilizador.DoesNotExist:
                idioma = None

        if idioma not in dict(settings.LANGUAGES):
            idioma = request.COOKIES.get(
                settings.LANGUAGE_COOKIE_NAME,
                settings.LANGUAGE_CODE,
            )

        if idioma not in dict(settings.LANGUAGES):
            idioma = settings.LANGUAGE_CODE

        with translation.override(idioma):
            request.LANGUAGE_CODE = idioma
            response = self.get_response(request)

        return response