from django.urls import path
from .views import pagina_registar
from django.urls import path

from .views import (
    registar,
    verificar_registo,
    login_utilizador,
    verificar_login,
    recuperar_password,
    verificar_recuperacao,
    redefinir_password,

    pagina_login,
    pagina_verificar_registo,
    pagina_verificar_login,
    pagina_recuperar_password,
    pagina_registar,

    pagina_perfil,
    logout_utilizador,
)


urlpatterns = [
    path("registar/", pagina_registar, name="pagina_registar"),

    path(
        "login/",
        pagina_login,
        name="pagina_login"
    ),

    path(
        "verificar-registo/",
        pagina_verificar_registo,
        name="pagina_verificar_registo"
    ),

    path(
        "verificar-login/",
        pagina_verificar_login,
        name="pagina_verificar_login"
    ),

    path(
        "recuperar-password/",
        pagina_recuperar_password,
        name="pagina_recuperar_password"
    ),

    path(
        "registar/",
        pagina_registar,
        name="pagina_registar"
    ),

    # API
    path(
        "api/registar/",
        registar,
        name="registar"
    ),

    path(
        "api/verificar-registo/",
        verificar_registo,
        name="verificar_registo"
    ),

    path(
        "api/login/",
        login_utilizador,
        name="login"
    ),

    path(
        "api/verificar-login/",
        verificar_login,
        name="verificar_login"
    ),

    path(
        "api/recuperar-password/",
        recuperar_password,
        name="recuperar_password"
    ),

    path(
        "api/verificar-recuperacao/",
        verificar_recuperacao,
        name="verificar_recuperacao"
    ),

    path(
        "api/redefinir-password/",
        redefinir_password,
        name="redefinir_password"
    ),

    # PERFIL
    path(
        "perfil/",
        pagina_perfil,
        name="perfil"
    ),

    # LOGOUT
    path(
        "api/logout/",
        logout_utilizador,
        name="logout"
    ),
]