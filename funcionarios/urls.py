from django.urls import path
from .views import login_funcionarios, logout_funcionarios

urlpatterns = [
    path("login/", login_funcionarios, name="login_funcionarios"),
    path("logout/", logout_funcionarios, name="logout_funcionarios"),
]