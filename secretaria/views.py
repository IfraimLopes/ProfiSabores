from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from reservas.models import Reserva


def secretaria_required(view_func):
    @login_required(login_url="/funcionarios/login/")
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if request.user.groups.filter(name="Secretaria").exists():
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden(
            "Não tens permissão para aceder à Secretaria."
        )

    return wrapper


@secretaria_required
def painel_secretaria(request):

    data_atual = timezone.localdate()

    data_filtro = request.GET.get("data", "").strip()

    if data_filtro:
        try:
            from datetime import datetime
            data_selecionada = datetime.strptime(
                data_filtro,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            data_selecionada = data_atual
    else:
        data_selecionada = data_atual

    pagamento_filtro = request.GET.get(
        "pagamento",
        "todos"
    )

    pesquisa = request.GET.get(
        "pesquisa",
        ""
    ).strip()

    reservas = (
        Reserva.objects
        .filter(
            data=data_selecionada
        )
        .select_related(
            "curso",
            "prato",
            "sobremesa",
            "utilizador",
        )
        .order_by(
            "hora",
            "nome",
        )
    )

    if pagamento_filtro in ["pago", "pendente"]:
        reservas = reservas.filter(
            pagamento=pagamento_filtro
        )

    if pesquisa:
        reservas = reservas.filter(
            nome__icontains=pesquisa
        )

    total_reservas = reservas.count()

    total_pagos = reservas.filter(
        pagamento="pago"
    ).count()

    total_pendentes = reservas.filter(
        pagamento="pendente"
    ).count()

    total_recebido = sum(
        reserva.total
        for reserva in reservas
        if reserva.pagamento == "pago"
    )

    contexto = {
        "reservas": reservas,
        "data_selecionada": data_selecionada,
        "total_reservas": total_reservas,
        "total_pagos": total_pagos,
        "total_pendentes": total_pendentes,
        "total_recebido": total_recebido,
        "pagamento_filtro": pagamento_filtro,
        "pesquisa": pesquisa,
    }

    return render(
        request,
        "secretaria/painel.html",
        contexto
    )