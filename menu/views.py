import json

from datetime import timedelta
from menu.models import Ementa, BannerHome
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from menu.models import Ementa


from django.views.decorators.cache import never_cache


def obter_tipo_utilizador(request):
    """Determina o perfil utilizado para apresentar os preços."""

    if not request.user.is_authenticated:
        return request.session.get("tipo_visitante", "visitante")

    try:
        perfil = request.user.perfil
        return "staff" if perfil.tipo == "staff" else "aluno"
    except AttributeError:
        return "aluno"

def obter_preco_ementa(ementa, tipo_utilizador):
    """Devolve o preço-base adequado ao perfil."""

    if tipo_utilizador in ("staff", "visitante"):
        return ementa.preco_base_staff

    return ementa.preco_base_aluno


def obter_ementas_do_dia(data, tipo_utilizador):
    """Obtém as ementas publicadas e ativas para uma data."""
    ementas = (
        Ementa.objects.filter(
            data_refeicao=data,
            publicada=True,
            ativa=True,
        )
        .select_related("entrada", "prato_principal")
        .prefetch_related("extras")
        .order_by("id")
    )

    for ementa in ementas:
        ementa.preco = obter_preco_ementa(
            ementa,
            tipo_utilizador,
        )

        extras_ativos = []

        
        for extra in ementa.extras.all():
            extra.preco_exibicao = (
                extra.preco_staff
                if tipo_utilizador in ("staff", "visitante")
                else extra.preco_aluno
            )

          
            if extra.ativo:
                extras_ativos.append({
                    "id": extra.id,
                    "tipo": extra.tipo,
                    "nome": extra.nome,
                    "descricao": extra.descricao,
                    "alergenios": extra.alergenios,
                    "preco": str(extra.preco_exibicao),
                })


        ementa.extras_json = json.dumps(extras_ativos, ensure_ascii=False)

    return ementas


@never_cache
def pagina_entrada(request):
    """Página inicial de escolha do tipo de acesso."""
    return render(request, "entrada.html")


@never_cache
def home(request):
    """Página inicial do Profisabores."""
    hoje = timezone.localdate()
    tipo_utilizador = obter_tipo_utilizador(request)

    ementas = obter_ementas_do_dia(
        hoje,
        tipo_utilizador,
    )

    # Banners ativos do carrossel superior
    banners_topo = BannerHome.objects.filter(
        posicao="topo",
        ativo=True,
    ).order_by("ordem", "id")

    # Banners ativos do carrossel inferior
    banners_fim = BannerHome.objects.filter(
        posicao="fim",
        ativo=True,
    ).order_by("ordem", "id")

    contexto = {
        "ementas": ementas,
        "hoje": hoje,
        "banners_topo": banners_topo,
        "banners_fim": banners_fim,
    }

    return render(
        request,
        "index.html",
        contexto,
    )


@never_cache
def menu(request):
    """Mostra as ementas de hoje, amanhã e depois de amanhã."""
    hoje = timezone.localdate()
    tipo_utilizador = obter_tipo_utilizador(request)

    dias = [
        {
            "data": hoje,
            "titulo": "Hoje",
            "ementas": [],
        },
        {
            "data": hoje + timedelta(days=1),
            "titulo": "Amanhã",
            "ementas": [],
        },
        {
            "data": hoje + timedelta(days=2),
            "titulo": "Depois de amanhã",
            "ementas": [],
        },
    ]

    for dia in dias:
        dia["ementas"] = obter_ementas_do_dia(
            dia["data"],
            tipo_utilizador,
        )

    return render(
        request,
        "menu.html",
        {
            "dias_menu": dias,
        },
    )


@never_cache
def api_menu(request):
    """API com as ementas publicadas e ativas."""
    hoje = timezone.localdate()
    tipo_utilizador = obter_tipo_utilizador(request)

    datas = [
        hoje,
        hoje + timedelta(days=1),
        hoje + timedelta(days=2),
    ]

    ementas = (
        Ementa.objects.filter(
            data_refeicao__in=datas,
            publicada=True,
            ativa=True,
        )
        .select_related("entrada", "prato_principal")
        .prefetch_related("extras")
        .order_by("data_refeicao", "id")
    )

    resultado = []

    for ementa in ementas:
        preco = obter_preco_ementa(
            ementa,
            tipo_utilizador,
        )

        extras = []

        for extra in ementa.extras.all():
            preco_extra = (
               extra.preco_staff
                if tipo_utilizador in ("staff", "visitante")
                else extra.preco_aluno
            )

            extras.append(
                {
                    "id": extra.id,
                    "nome": extra.nome,
                    "tipo": extra.tipo,
                    "descricao": extra.descricao,
                    "preco": (
                        str(preco_extra)
                        if preco_extra is not None
                        else None
                    ),
                    "alergenios": extra.alergenios,
                }
            )

        resultado.append(
            {
                "id": ementa.id,
                "data_refeicao": str(ementa.data_refeicao),
                "descricao": ementa.descricao,
                "entrada": (
                    {
                        "id": ementa.entrada.id,
                        "nome": ementa.entrada.nome,
                        "descricao": ementa.entrada.descricao,
                        "alergenios": ementa.entrada.alergenios,
                    }
                    if ementa.entrada
                    else None
                ),
                "prato_principal": (
                    {
                        "id": ementa.prato_principal.id,
                        "nome": ementa.prato_principal.nome,
                        "descricao": ementa.prato_principal.descricao,
                        "alergenios": ementa.prato_principal.alergenios,
                    }
                    if ementa.prato_principal
                    else None
                ),
                "extras": extras,
                "preco": (
                    str(preco)
                    if preco is not None
                    else None
                ),
            }
        )

    return JsonResponse(
        {
            "ementas": resultado,
            "data_consulta": str(hoje),
        }
    )
