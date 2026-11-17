from django.urls import path
from .views import (
    registar,
    verificar_registo,
    login_utilizador,
    verificar_login,
    alterar_idioma,
    pagina_login,
    pagina_verificar_registo,
    pagina_verificar_login,
    pagina_registar,
    pagina_perfil,
    logout_utilizador,
)


urlpatterns = [
    path(
        "login/",
        pagina_login,
        name="pagina_login"
    ),
    path(
    "idioma/",
    alterar_idioma,
    name="alterar_idioma",
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