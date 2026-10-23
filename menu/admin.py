
from django.contrib import admin

from .models import (
    Curso,
    Prato,
    Sobremesa,
    BannerHome,
    ItemEmenta,
    Ementa,
    Extra,
)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "nome",
        "ano",
    )

    search_fields = (
        "codigo",
        "nome",
    )


@admin.register(ItemEmenta)
class ItemEmentaAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "ativo",
        "criado_em",
        "atualizado_em",
    )

    list_filter = (
        "ativo",
    )

    search_fields = (
        "nome",
        "descricao",
        "alergenios",
    )

    ordering = (
        "nome",
    )


@admin.register(Ementa)
class EmentaAdmin(admin.ModelAdmin):

    list_display = (
        "data_refeicao",
        "entrada",
        "prato_principal",
        "preco_base_aluno",
        "preco_base_staff",
        "preco_base_visitante",
        "publicada",
        "ativa",
    )

    list_filter = (
        "data_refeicao",
        "publicada",
        "ativa",
    )

    search_fields = (
        "descricao",
        "entrada__nome",
        "prato_principal__nome",
    )

    autocomplete_fields = (
        "entrada",
        "prato_principal",
    )

    ordering = (
        "-data_refeicao",
    )

    readonly_fields = (
        "publicada_em",
        "criada_em",
        "atualizada_em",
    )


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "tipo",
        "ementa",
        "preco_aluno",
        "preco_staff",
        "preco_visitante",
        "ativo",
    )

    list_filter = (
        "tipo",
        "ativo",
        "ementa",
    )

    search_fields = (
        "nome",
        "tipo",
        "descricao",
        "alergenios",
    )

    autocomplete_fields = (
        "ementa",
    )

    ordering = (
        "ementa",
        "tipo",
        "nome",
    )


@admin.register(Prato)
class PratoAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "preco_aluno",
        "preco_profissional",
        "data",
        "disponivel",
    )

    list_filter = (
        "data",
        "disponivel",
    )

    search_fields = (
        "nome",
    )


@admin.register(Sobremesa)
class SobremesaAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "preco_aluno",
        "preco_profissional",
        "data",
        "disponivel",
    )

    list_filter = (
        "data",
        "disponivel",
    )

    search_fields = (
        "nome",
    )


@admin.register(BannerHome)
class BannerHomeAdmin(admin.ModelAdmin):

    list_display = (
        "posicao",
        "ordem",
        "ativo",
    )

    list_filter = (
        "posicao",
        "ativo",
    )

    ordering = (
        "posicao",
        "ordem",
    )

