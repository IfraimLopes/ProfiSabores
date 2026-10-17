from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):

    list_display = (
        "nome_completo",
        "utilizador",
        "tipo",
        "curso",
        "telemovel",
        "verificado",
        "criado_em",
    )

    list_filter = (
        "tipo",
        "verificado",
        "sexo",
        "curso",
    )

    search_fields = (
        "nome_completo",
        "utilizador__username",
        "utilizador__email",
        "telemovel",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )