
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from reservas.models import Reserva


def cozinha_required(view_func):
    @login_required(login_url="/funcionarios/login/")
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if request.user.groups.filter(name="Cozinha").exists():
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden(
            "Não tens permissão para aceder à Cozinha."
        )

    return wrapper


@cozinha_required
def painel_cozinha(request):
    data_atual = timezone.localdate()

    reservas = list(
        Reserva.objects.filter(
            data=data_atual,
            estado="confirmada",
            pagamento="pago",
            ementa__isnull=False,
        )
        .select_related(
            "curso",
            "ementa",
            "ementa__entrada",
            "ementa__prato_principal",
            "utilizador",
            "utilizador__perfil",
        )
        .prefetch_related(
            "extras__extra",
        )
        .order_by(
            "hora",
            "curso__codigo",
            "nome",
        )
    )

    entradas_contagem = Counter()
    pratos_contagem = Counter()
    sobremesas_contagem = Counter()
    extras_contagem = Counter()

    for reserva in reservas:
        ementa = reserva.ementa

        if ementa.entrada:
            entradas_contagem[ementa.entrada.nome] += 1

        if ementa.prato_principal:
            pratos_contagem[ementa.prato_principal.nome] += 1

        for reserva_extra in reserva.extras.all():
            chave = (
                reserva_extra.extra.tipo,
                reserva_extra.extra.nome,
            )
            extras_contagem[chave] += reserva_extra.quantidade

            if "sobremesa" in reserva_extra.extra.tipo.lower():
                sobremesas_contagem[reserva_extra.extra.nome] += (
                    reserva_extra.quantidade
                )

    total_refeicoes = len(reservas)
    total_entradas = sum(entradas_contagem.values())
    total_pratos = sum(pratos_contagem.values())
    total_sobremesas = sum(sobremesas_contagem.values())
    total_extras = sum(extras_contagem.values())

    contexto = {
        "reservas": reservas,
        "data_selecionada": data_atual,
        "total_refeicoes": total_refeicoes,
        "total_entradas": total_entradas,
        "total_pratos": total_pratos,
        "total_sobremesas": total_sobremesas,
        "total_extras": total_extras,
        "entradas_contagem": entradas_contagem.items(),
        "pratos_contagem": pratos_contagem.items(),
        "sobremesas_contagem": sobremesas_contagem.items(),
        "extras_contagem": extras_contagem.items(),
    }

    return render(
        request,
        "cozinha/painel.html",
        contexto,
    )
