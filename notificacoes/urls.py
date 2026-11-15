from django.urls import path

from . import views


urlpatterns = [
    path(
        "caixa/",
        views.caixa_notificacoes,
        name="caixa_notificacoes"
    ),
    path(
        "",
        views.listar_notificacoes,
        name="listar_notificacoes"
    ),
    path(
        "<int:notificacao_id>/lida/",
        views.marcar_notificacao_lida,
        name="marcar_notificacao_lida"
    ),
    path(
        "<int:notificacao_id>/eliminar/",
        views.eliminar_notificacao,
        name="eliminar_notificacao"
    ),
    path(
        "eliminar-todas/",
        views.eliminar_todas_notificacoes,
        name="eliminar_todas_notificacoes"
    ),
]
