
from random import randint
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from reservas.views import (
    obter_token_visitante,
    definir_cookie_visitante,
)
from utilizadores.models import Perfil, CodigoVerificacao
from .models import Notificacao


def gerar_codigo():
    return str(randint(100000, 999999))



@csrf_exempt
@require_POST
def login_utilizador(request):

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()

    password = request.POST.get(
        "password",
        ""
    )

    if not email or not password:
        return JsonResponse(
            {
                "erro": "E-mail e palavra-passe são obrigatórios."
            },
            status=400
        )

    try:
        utilizador = User.objects.get(
            email=email
        )

    except User.DoesNotExist:
        return JsonResponse(
            {
                "erro": "E-mail ou palavra-passe incorretos."
            },
            status=401
        )

    utilizador_auth = authenticate(
        request,
        username=utilizador.username,
        password=password
    )

    if utilizador_auth is None:
        return JsonResponse(
            {
                "erro": "E-mail ou palavra-passe incorretos."
            },
            status=401
        )

    if not utilizador.is_active:
        return JsonResponse(
            {
                "erro": "A conta não está ativa."
            },
            status=403
        )

    codigo = gerar_codigo()

    CodigoVerificacao.objects.create(
        email=email,
        codigo=codigo,
        finalidade="login",
        expira_em=timezone.now() + timedelta(minutes=10)
    )

    send_mail(
        "Código de login - Restaurante Profitecla",
        (
            f"O seu código de login é: {codigo}\n\n"
            "Este código é válido durante 10 minutos "
            "e só pode ser utilizado uma vez."
        ),
        None,
        [email],
        fail_silently=False,
    )

    return JsonResponse({
        "sucesso": True,
        "mensagem": (
            "Palavra-passe correta. Introduza o código "
            "enviado para o seu e-mail."
        ),
        "email": email
    })


@csrf_exempt
@require_POST
def verificar_login(request):

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()

    codigo = request.POST.get(
        "codigo",
        ""
    ).strip()

    if not email or not codigo:
        return JsonResponse(
            {
                "erro": "E-mail e código são obrigatórios."
            },
            status=400
        )

    try:
        verificacao = CodigoVerificacao.objects.filter(
            email=email,
            finalidade="login",
            usado=False
        ).latest("criado_em")

    except CodigoVerificacao.DoesNotExist:
        return JsonResponse(
            {
                "erro": "Código inválido ou inexistente."
            },
            status=400
        )

    if timezone.now() > verificacao.expira_em:
        return JsonResponse(
            {
                "erro": "O código expirou. Solicite um novo código."
            },
            status=400
        )

    if verificacao.tentativas >= 5:
        return JsonResponse(
            {
                "erro": "Número máximo de tentativas atingido."
            },
            status=400
        )

    if verificacao.codigo != codigo:

        verificacao.tentativas += 1

        verificacao.save(
            update_fields=["tentativas"]
        )

        return JsonResponse(
            {
                "erro": "Código incorreto."
            },
            status=400
        )

    try:
        utilizador = User.objects.get(
            email=email
        )

        perfil = utilizador.perfil

    except (User.DoesNotExist, Perfil.DoesNotExist):
        return JsonResponse(
            {
                "erro": "Perfil do utilizador não encontrado."
            },
            status=404
        )

    verificacao.usado = True

    verificacao.save(
        update_fields=["usado"]
    )

    login(
        request,
        utilizador
    )

    return JsonResponse({
        "sucesso": True,
        "mensagem": "Login efetuado com sucesso.",
        "utilizador": {
            "id": utilizador.id,
            "nome": perfil.nome_completo,
            "email": utilizador.email,
            "tipo": perfil.tipo,
            "escalao_preco": perfil.escalão_preco,
        }
    })



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


# ============================================================
# PÁGINA VISUAL DA CAIXA DE ENTRADA
# ============================================================

@require_GET
def caixa_notificacoes(request):

    if not request.user.is_authenticated:
        return JsonResponse(
            {"erro": "É necessário iniciar sessão."},
            status=401
        )

    notificacoes = Notificacao.objects.filter(
        utilizador=request.user
    ).order_by("-criada_em")

    return render(
        request,
        "notificacoes/caixa.html",
        {
            "notificacoes": notificacoes,
            "nao_lidas": notificacoes.filter(lida=False).count(),
        }
    )
