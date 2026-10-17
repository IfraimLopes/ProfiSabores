from django.urls import path

from .views import painel_cozinha


urlpatterns = [
    path("", painel_cozinha, name="painel_cozinha"),
]