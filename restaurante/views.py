from decimal import Decimal
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from menu.models import Ementa
from reservas.models import Pagamento, Reserva
from reservas.notificacoes import (
    enviar_notificacao_utilizador,
    enviar_notificacao_visitante,
)


def restaurante_required(view_func):
    @login_required(login_url="/funcionarios/login/")
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if (
            request.user.is_superuser
            or request.user.groups.filter(name="Restaurante").exists()
        ):
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden(
            "Não tens permissão para aceder ao Restaurante."
        )

    return wrapper


@restaurante_required
def painel_restaurante(request):
    data_atual = timezone.localdate()
    data_filtro = request.GET.get("data", "").strip()
    pesquisa = request.GET.get("pesquisa", "").strip()

    data_selecionada = data_atual

    if data_filtro:
        try:
            from datetime import datetime

            data_selecionada = datetime.strptime(
                data_filtro, "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    reservas = (
        Reserva.objects.filter(data=data_selecionada)
        .select_related(
            "utilizador",
            "utilizador__perfil",
            "curso",
            "ementa",
            "ementa__entrada",
            "ementa__prato_principal",
            "prato",
            "sobremesa",
        )
        .prefetch_related("extras__extra")
        .order_by("criada_em", "pk")
    )

    if pesquisa:
        reservas = reservas.filter(nome__icontains=pesquisa)

    ementas = Ementa.objects.filter(
        data_refeicao__gte=data_atual
    ).order_by("data_refeicao", "id")

    reservas_ativas = reservas.exclude(estado="cancelada")

    contexto = {
        "reservas": reservas,
        "ementas": ementas,
        "data_selecionada": data_selecionada,
        "pesquisa": pesquisa,
        "total_reservas": reservas_ativas.count(),
        "total_pendentes": reservas_ativas.filter(
            pagamento="pendente"
        ).count(),
        "total_pagos": reservas_ativas.filter(
            pagamento="pago"
        ).count(),
        "total_recebido": (
            reservas_ativas.filter(pagamento="pago").aggregate(
                soma=Sum("total")
            )["soma"] or Decimal("0.00")
        ),
        "total_a_receber": (
            reservas_ativas.exclude(pagamento="pago").aggregate(
                soma=Sum("total")
            )["soma"] or Decimal("0.00")
        ),
    }

    return render(
        request,
        "restaurante/painel.html",
        contexto,
    )


@restaurante_required
@require_POST
def marcar_pagamento(request, reserva_id):
    with transaction.atomic():
        reserva = get_object_or_404(
            Reserva.objects.select_for_update(),
            pk=reserva_id,
        )

        if reserva.estado == "cancelada":
            return HttpResponseForbidden(
                "Não é possível alterar o pagamento de uma reserva cancelada."
            )

        pagamento, _ = Pagamento.objects.get_or_create(
            reserva=reserva,
            defaults={
                "valor": reserva.total,
                "estado": "pendente",
            },
        )

        if reserva.pagamento == "pago":
            pagamento.estado = "pendente"
            pagamento.pago_em = None
            pagamento.pago_por = None
            pagamento.save(
                update_fields=[
                    "estado",
                    "pago_em",
                    "pago_por",
                    "atualizado_em",
                ]
            )

            reserva.pagamento = "pendente"
            reserva.pago_em = None
            reserva.pago_por = None
            reserva.save(
                update_fields=[
                    "pagamento",
                    "pago_em",
                    "pago_por",
                ]
            )
        else:
            pagamento.valor = reserva.total
            pagamento.estado = "pago"
            pagamento.pago_em = timezone.now()
            pagamento.pago_por = request.user
            pagamento.save(
                update_fields=[
                    "valor",
                    "estado",
                    "pago_em",
                    "pago_por",
                    "atualizado_em",
                ]
            )

            reserva.pagamento = "pago"
            reserva.pago_em = pagamento.pago_em
            reserva.pago_por = request.user
            reserva.save(
                update_fields=[
                    "pagamento",
                    "pago_em",
                    "pago_por",
                ]
            )

    try:
        if reserva.pagamento == "pago":
            titulo = "Pagamento confirmado"
            mensagem = "O pagamento da tua reserva foi confirmado."
        else:
            titulo = "Pagamento pendente"
            mensagem = "O pagamento da tua reserva está pendente."

        if reserva.utilizador_id:
            enviar_notificacao_utilizador(
                reserva.utilizador,
                titulo,
                mensagem,
            )
        elif reserva.visitante_token:
            enviar_notificacao_visitante(
                reserva.visitante_token,
                titulo,
                mensagem,
            )
    except Exception as erro:
        print(
            "Profisabores: falha ao notificar "
            f"o pagamento da reserva #{reserva.pk}: {erro}"
        )

    return redirect(
        f"/restaurante/?data={reserva.data.isoformat()}"
    )


@restaurante_required
@require_POST
def alternar_ementa(request, ementa_id):
    ementa = get_object_or_404(Ementa, pk=ementa_id)

    # Uma ementa não publicada não pode ser ativada.
    if not ementa.publicada and not ementa.ativa:
        return HttpResponseForbidden(
            "Não podes ativar uma ementa que ainda não foi publicada."
        )

    ementa.ativa = not ementa.ativa
    ementa.save(update_fields=["ativa", "atualizada_em"])

    return redirect("painel_restaurante")
