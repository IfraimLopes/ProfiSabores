
from random import randint
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Notificacao
from reservas.models import Reserva, Dispositivo, SubscricaoWebPush
from reservas.notificacoes import (enviar_notificacao_utilizador, enviar_webpush)
from utilizadores.models import Perfil


def gerar_codigo():
    return str(randint(100000, 999999))


@csrf_exempt
@require_POST
def criar_notificacao(request):

    titulo = request.POST.get(
        "titulo",
        ""
    ).strip()

    mensagem = request.POST.get(
        "mensagem",
        ""
    ).strip()

    tipo = request.POST.get(
        "tipo",
        "geral"
    ).strip().lower()

    reserva_id = request.POST.get(
        "reserva_id",
        ""
    ).strip()

    if not titulo:
        return JsonResponse(
            {
                "erro": "O título é obrigatório."
            },
            status=400
        )

    if not mensagem:
        return JsonResponse(
            {
                "erro": "A mensagem é obrigatória."
            },
            status=400
        )

    tipos_validos = [
        "geral",
        "reserva",
        "menu",
        "lembrete",
    ]

    if tipo not in tipos_validos:
        return JsonResponse(
            {
                "erro": "Tipo de notificação inválido."
            },
            status=400
        )

    reserva = None

    if reserva_id:

        try:
            reserva = Reserva.objects.get(
                id=reserva_id
            )

        except Reserva.DoesNotExist:
            return JsonResponse(
                {
                    "erro": "A reserva não existe."
                },
                status=404
            )

    notificacao = Notificacao.objects.create(
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        reserva=reserva
    )

    enviados = 0

    # Notificações gerais, de menu ou lembrete:
    # enviadas para todos os dispositivos ativos.
    if tipo in ["geral", "menu", "lembrete"]:

        dispositivos = Dispositivo.objects.filter(
            ativo=True,
            utilizador__isnull=False
        )

        for dispositivo in dispositivos:

            try:
                from reservas.firebase_admin import enviar_notificacao

                enviar_notificacao(
                    dispositivo.token,
                    titulo,
                    mensagem
                )

                enviados += 1

            except Exception as erro:
                print(
                    "Profisabores: erro ao enviar notificação geral:",
                    erro
                )

        # Enviar também para as subscrições Web Push ativas,
        # incluindo as de alunos, funcionários e visitantes.
        subscricoes_webpush = SubscricaoWebPush.objects.filter(
            ativo=True
        )

        enviados += enviar_webpush(
            subscricoes_webpush,
            titulo,
            mensagem
        )

    # Notificação associada a uma reserva:
    # enviada apenas ao utilizador dessa reserva.
    elif tipo == "reserva" and reserva and reserva.utilizador:

        enviados = enviar_notificacao_utilizador(
            reserva.utilizador,
            titulo,
            mensagem
        )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Notificação criada com sucesso.",
            "notificacao_id": notificacao.id,
            "titulo": notificacao.titulo,
            "tipo": notificacao.tipo,
            "enviados": enviados,
        },
        status=201
    )


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
