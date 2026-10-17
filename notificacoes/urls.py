from django.urls import path

from .views import criar_notificacao


urlpatterns = [

    path(
        "criar/",
        criar_notificacao,
        name="criar_notificacao"
    ),

]