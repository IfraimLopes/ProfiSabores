from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import set_language
from django.conf import settings
from django.conf.urls.static import static

from menu.views import pagina_entrada, home, menu, api_menu
from reservas.views import servir_service_worker


urlpatterns = [
    path("sw.js", servir_service_worker, name="service_worker"),
    path("admin/", admin.site.urls),
    path("restaurante/", include("restaurante.urls")),
    path("", pagina_entrada, name="entrada"),
    path("inicio/", home, name="home"),
    path("i18n/set-language/", set_language, name="set_language"),
    path("menu/", menu, name="menu"),
    path("utilizadores/", include("utilizadores.urls")),
    path("reservas/", include("reservas.urls")),
    path("notificacoes/", include("notificacoes.urls")),
    path("api/menu/", api_menu, name="api_menu"),
    path("cozinha/", include("cozinha.urls")),
    path("funcionarios/", include("funcionarios.urls")),
    path("secretaria/", include("secretaria.urls")),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
