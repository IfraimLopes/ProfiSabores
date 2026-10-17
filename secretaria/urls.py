from django.urls import path
from .views import painel_secretaria

urlpatterns = [
    path("", painel_secretaria, name="painel_secretaria"),
]