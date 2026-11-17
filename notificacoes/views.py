


from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from reservas.views import (
    obter_token_visitante,
    definir_cookie_visitante,
)
from .models import Notificacao










# ============================================================
# CAIXA DE ENTRADA DE NOTIFICAÇÕES
# ============================================================

def obter_notificacoes_do_pedido(request):

    if request.user.is_authenticated:
        return (
            Notificacao.objects.filter(
                utilizador=request.user
            ),
            None
        )

    token_visitante = obter_token_visitante(request)

    return (
        Notificacao.objects.filter(
            utilizador__isnull=True,
            visitante_token=token_visitante
        ),
        token_visitante
    )


def resposta_notificacoes(request, dados, token_visitante=None, status=200):

    resposta = JsonResponse(
        dados,
        status=status
    )

    if token_visitante:
        definir_cookie_visitante(
            resposta,
            token_visitante,
            request
        )

    return resposta


@require_GET
def listar_notificacoes(request):

    notificacoes, token_visitante = obter_notificacoes_do_pedido(
        request
    )

    notificacoes = notificacoes.order_by("-criada_em")

    dados = [
        {
            "id": notificacao.id,
            "titulo": notificacao.titulo,
            "mensagem": notificacao.mensagem,
            "tipo": notificacao.tipo,
            "lida": notificacao.lida,
            "criada_em": notificacao.criada_em.isoformat(),
        }
        for notificacao in notificacoes
    ]

    return resposta_notificacoes(
        request,
        {
            "notificacoes": dados,
            "total": len(dados),
            "nao_lidas": notificacoes.filter(lida=False).count(),
        },
        token_visitante
    )


@require_POST
def marcar_notificacao_lida(request, notificacao_id):

    notificacoes, token_visitante = obter_notificacoes_do_pedido(
        request
    )

    try:
        notificacao = notificacoes.get(
            id=notificacao_id
        )

    except Notificacao.DoesNotExist:
        return resposta_notificacoes(
            request,
            {"erro": "Notificação não encontrada."},
            token_visitante,
            status=404
        )

    if not notificacao.lida:
        notificacao.lida = True
        notificacao.lida_em = timezone.now()

        notificacao.save(
            update_fields=["lida", "lida_em"]
        )

    return resposta_notificacoes(
        request,
        {
            "sucesso": True,
            "nao_lidas": notificacoes.filter(
                lida=False
            ).count()
        },
        token_visitante
    )


@require_POST
def eliminar_notificacao(request, notificacao_id):

    notificacoes, token_visitante = obter_notificacoes_do_pedido(
        request
    )

    eliminadas, _ = notificacoes.filter(
        id=notificacao_id
    ).delete()

    if not eliminadas:
        return resposta_notificacoes(
            request,
            {"erro": "Notificação não encontrada."},
            token_visitante,
            status=404
        )

    return resposta_notificacoes(
        request,
        {"sucesso": True},
        token_visitante
    )


@require_POST
def eliminar_todas_notificacoes(request):

    notificacoes, token_visitante = obter_notificacoes_do_pedido(
        request
    )

    eliminadas, _ = notificacoes.delete()

    return resposta_notificacoes(
        request,
        {
            "sucesso": True,
            "eliminadas": eliminadas
        },
        token_visitante
    )


# ============================================================
# PÁGINA VISUAL DA CAIXA DE ENTRADA
# ============================================================

@require_GET
def caixa_notificacoes(request):

    notificacoes, token_visitante = obter_notificacoes_do_pedido(
        request
    )

    notificacoes = notificacoes.order_by("-criada_em")

    resposta = render(
        request,
        "notificacoes/caixa.html",
        {
            "notificacoes": notificacoes,
            "nao_lidas": notificacoes.filter(lida=False).count(),
        }
    )

    if token_visitante:
        definir_cookie_visitante(
            resposta,
            token_visitante,
            request
        )

    return resposta
