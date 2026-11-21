from datetime import datetime, timedelta
import secrets
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import translation
from django.db import transaction

from menu.models import Curso
from .models import (
    Aluno,
    Staff,
    Perfil,
    CodigoVerificacao,
    PreferenciasUtilizador,
)

@require_POST
def alterar_idioma(request):
    idioma = request.POST.get("idioma", "").strip()

    idiomas_validos = dict(settings.LANGUAGES)

    if idioma not in idiomas_validos:
        return redirect("perfil")

    if request.user.is_authenticated:
        PreferenciasUtilizador.objects.update_or_create(
            utilizador=request.user,
            defaults={"idioma": idioma},
        )

    translation.activate(idioma)
    request.session["django_language"] = idioma

    destino = request.POST.get("next", "").strip()

    if not destino.startswith("/") or destino.startswith("//"):
        destino = "/utilizadores/perfil/"

    resposta = redirect(destino)

    resposta.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        idioma,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
    )

    return resposta

@csrf_exempt
@require_POST

def registar(request):
    return JsonResponse(
        {
            "sucesso": False,
            "erro": "O registo público está desativado."
        },
        status=403
    )


def gerar_codigo():
    """Gera um PIN numérico de 6 dígitos."""
    return f"{secrets.randbelow(1_000_000):06d}"


@csrf_exempt
@require_POST
def verificar_registo(request):
    return JsonResponse(
        {
            "sucesso": False,
            "erro": "A verificação de registos públicos está desativada."
        },
        status=403
    )


# ============================================================
# LOGIN
# ============================================================


def obter_utilizador_aluno_staff(email):
    email = email.strip().lower()

    aluno = (
        Aluno.objects
        .select_related("utilizador")
        .filter(email__iexact=email)
        .first()
    )

    staff = (
        Staff.objects
        .select_related("utilizador")
        .filter(email__iexact=email)
        .first()
    )

    if bool(aluno) == bool(staff):
        return None

    conta = aluno or staff
    utilizador = conta.utilizador

    if not utilizador.is_active:
        return None

    if utilizador.email.strip().lower() != email:
        return None

    return utilizador


def login_utilizador(request):
    email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse(
            {"erro": "O e-mail é obrigatório."},
            status=400
        )

    utilizador = obter_utilizador_aluno_staff(email)

    if not utilizador:
        return JsonResponse(
            {"erro": "Não existe uma conta ativa de Aluno ou Staff com este e-mail."},
            status=403
        )

    CodigoVerificacao.objects.filter(
        email__iexact=email,
        finalidade="login",
        usado=False
    ).update(usado=True)

    codigo = gerar_codigo()

    CodigoVerificacao.objects.create(
        email=email,
        codigo=codigo,
        finalidade="login",
        expira_em=timezone.now() + timedelta(minutes=10)
    )

    send_mail(
        "Código de acesso - Restaurante Profitecla",
        (
            f"O seu código de acesso é: {codigo}\n\n"
            "Este código é válido durante 10 minutos.\n"
            "Se não solicitou este código, ignore esta mensagem."
        ),
        None,
        [email],
        fail_silently=False,
    )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Código de acesso enviado para o seu e-mail.",
            "email": email,
            "redirect": "/utilizadores/verificar-login/"
        },
        status=200
    )


@csrf_exempt
@require_POST
def verificar_login(request):
    email = request.POST.get("email", "").strip().lower()
    codigo_digitado = request.POST.get("codigo", "").strip()

    if not email or not codigo_digitado:
        return JsonResponse(
            {"erro": "O e-mail e o código são obrigatórios."},
            status=400
        )

    if len(codigo_digitado) != 6 or not codigo_digitado.isdigit():
        return JsonResponse(
            {"erro": "O código deve conter exatamente seis dígitos."},
            status=400
        )

    codigo_obj = (
        CodigoVerificacao.objects
        .filter(
            email__iexact=email,
            finalidade="login",
            usado=False
        )
        .order_by("-criado_em")
        .first()
    )

    if not codigo_obj:
        return JsonResponse(
            {"erro": "Não existe um código de login válido. Solicite um novo."},
            status=400
        )

    if timezone.now() > codigo_obj.expira_em:
        codigo_obj.usado = True
        codigo_obj.save(update_fields=["usado"])

        return JsonResponse(
            {"erro": "O código expirou. Faça login novamente."},
            status=400
        )

    if codigo_obj.tentativas >= 5:
        codigo_obj.usado = True
        codigo_obj.save(update_fields=["usado"])

        return JsonResponse(
            {"erro": "Limite de tentativas atingido. Solicite um novo código."},
            status=400
        )

    codigo_obj.tentativas += 1

    if not secrets.compare_digest(
        codigo_digitado,
        codigo_obj.codigo
    ):
        if codigo_obj.tentativas >= 5:
            codigo_obj.usado = True
            codigo_obj.save(update_fields=["tentativas", "usado"])

            return JsonResponse(
                {
                    "erro": (
                        "Limite de tentativas atingido. "
                        "Solicite um novo código."
                    )
                },
                status=400
            )

        codigo_obj.save(update_fields=["tentativas"])

        return JsonResponse(
            {"erro": "Código incorreto."},
            status=400
        )

    codigo_obj.save(update_fields=["tentativas"])

    utilizador = obter_utilizador_aluno_staff(email)

    if not utilizador:
        codigo_obj.usado = True
        codigo_obj.save(update_fields=["usado"])

        return JsonResponse(
            {"erro": "A conta não está disponível para autenticação."},
            status=403
        )

    # Autenticação por sessão, sem exigir palavra-passe.
    login(
        request,
        utilizador,
        backend="django.contrib.auth.backends.ModelBackend"
    )

    codigo_obj.usado = True
    codigo_obj.save(update_fields=["usado"])

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Login efetuado com sucesso.",
            "redirect": "/inicio/"
        },
        status=200
    )


# ============================================================
# RECUPERAÇÃO DE PALAVRA-PASSE
# ============================================================

@csrf_exempt
@require_POST
def recuperar_password(request):
    email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse(
            {"erro": "O e-mail é obrigatório."},
            status=400
        )

    utilizador = obter_utilizador_aluno_staff(email)

    if not utilizador:
        return JsonResponse(
            {"erro": "Não existe uma conta ativa de Aluno ou Staff com este e-mail."},
            status=403
        )

    CodigoVerificacao.objects.filter(
        email__iexact=email,
        finalidade="recuperacao",
        usado=False
    ).update(usado=True)

    codigo = gerar_codigo()

    CodigoVerificacao.objects.create(
        email=email,
        codigo=codigo,
        finalidade="recuperacao",
        expira_em=timezone.now() + timedelta(minutes=10)
    )

    send_mail(
        "Recuperação de palavra-passe - Restaurante Profitecla",
        (
            f"O seu código de recuperação é: {codigo}\\n\\n"
            "Este código é válido durante 10 minutos."
        ),
        None,
        [email],
        fail_silently=False,
    )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Código de recuperação enviado para o seu e-mail.",
            "email": email
        },
        status=200
    )


@csrf_exempt
@require_POST
def verificar_recuperacao(request):
    email = request.POST.get("email", "").strip().lower()
    codigo_digitado = request.POST.get("codigo", "").strip()

    if not email or not codigo_digitado:
        return JsonResponse(
            {"erro": "O e-mail e o código são obrigatórios."},
            status=400
        )

    utilizador = obter_utilizador_aluno_staff(email)

    if not utilizador:
        return JsonResponse(
            {"erro": "A conta não está disponível para recuperação."},
            status=403
        )

    codigo_obj = (
        CodigoVerificacao.objects
        .filter(
            email=email,
            finalidade="recuperacao",
            usado=False
        )
        .order_by("-criado_em")
        .first()
    )

    if not codigo_obj:
        return JsonResponse(
            {"erro": "Não existe um código de recuperação válido."},
            status=400
        )

    if timezone.now() > codigo_obj.expira_em:
        return JsonResponse(
            {"erro": "O código expirou. Solicite um novo código."},
            status=400
        )

    if codigo_obj.tentativas >= 5:
        return JsonResponse(
            {"erro": "Limite de tentativas atingido."},
            status=400
        )

    codigo_obj.tentativas += 1
    codigo_obj.save(update_fields=["tentativas"])

    if not secrets.compare_digest(codigo_digitado, codigo_obj.codigo):
        return JsonResponse(
            {"erro": "Código incorreto."},
            status=400
        )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Código confirmado.",
            "email": email
        },
        status=200
    )


@csrf_exempt
@require_POST
def redefinir_password(request):
    email = request.POST.get("email", "").strip().lower()
    nova_password = request.POST.get("password", "")
    codigo_digitado = request.POST.get("codigo", "").strip()

    if not email or not codigo_digitado:
        return JsonResponse(
            {"erro": "O e-mail e o código são obrigatórios."},
            status=400
        )

    if len(codigo_digitado) != 6 or not codigo_digitado.isdigit():
        return JsonResponse(
            {"erro": "O código deve conter exatamente seis dígitos."},
            status=400
        )

    if not nova_password:
        return JsonResponse(
            {"erro": "A nova palavra-passe é obrigatória."},
            status=400
        )

    if len(nova_password) < 8:
        return JsonResponse(
            {"erro": "A palavra-passe deve ter pelo menos 8 caracteres."},
            status=400
        )

    utilizador = obter_utilizador_aluno_staff(email)

    if not utilizador:
        return JsonResponse(
            {"erro": "A conta não está disponível para recuperação."},
            status=403
        )

    codigo_obj = (
        CodigoVerificacao.objects
        .filter(
            email=email,
            finalidade="recuperacao",
            usado=False
        )
        .order_by("-criado_em")
        .first()
    )

    if not codigo_obj:
        return JsonResponse(
            {"erro": "Código de recuperação inválido."},
            status=400
        )

    if timezone.now() > codigo_obj.expira_em:
        return JsonResponse(
            {"erro": "O código expirou."},
            status=400
        )

    if codigo_obj.tentativas >= 5:
        return JsonResponse(
            {"erro": "Limite de tentativas atingido."},
            status=400
        )

    if not secrets.compare_digest(codigo_digitado, codigo_obj.codigo):
        return JsonResponse(
            {"erro": "Código incorreto."},
            status=400
        )

    utilizador.set_password(nova_password)
    utilizador.save(update_fields=["password"])

    codigo_obj.usado = True
    codigo_obj.save(update_fields=["usado"])

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Palavra-passe alterada com sucesso.",
            "redirect": "/utilizadores/login/"
        },
        status=200
    )

# ============================================================
# PÁGINAS HTML
# ============================================================

@ensure_csrf_cookie
def pagina_login(request):
    return render(request, "login.html")


@ensure_csrf_cookie
def pagina_verificar_registo(request):
    return render(request, "verificar-registo.html")


@ensure_csrf_cookie
def pagina_verificar_login(request):
    return render(request, "verificar-login.html")


@ensure_csrf_cookie
def pagina_recuperar_password(request):
    return render(request, "recuperar-password.html")


def pagina_registar(request):
    return render(request, "registar.html")


# ============================================================
# PERFIL E LOGOUT
# ============================================================

def pagina_perfil(request):
    utilizador = None
    nome_utilizador = "Visitante"
    tipo_utilizador = "visitante"

    if request.user.is_authenticated:
        utilizador = request.user

        try:
            aluno = utilizador.aluno
            nome_utilizador = aluno.nome
            tipo_utilizador = "aluno"

        except Aluno.DoesNotExist:
            try:
                staff = utilizador.staff
                nome_utilizador = staff.nome
                tipo_utilizador = "staff"

            except Staff.DoesNotExist:
                nome_utilizador = (
                    utilizador.get_full_name()
                    or utilizador.username
                )
                tipo_utilizador = "conta_interna"

    idioma_atual = request.COOKIES.get(
        settings.LANGUAGE_COOKIE_NAME,
        settings.LANGUAGE_CODE,
    )

    if utilizador:
        try:
            preferencias = utilizador.preferencias_utilizador
            idioma_atual = preferencias.idioma
        except PreferenciasUtilizador.DoesNotExist:
            pass

    return render(
        request,
        "perfil.html",
        {
            "utilizador": utilizador,
            "nome_utilizador": nome_utilizador,
            "tipo_utilizador": tipo_utilizador,
            "idiomas_disponiveis": settings.LANGUAGES,
            "idioma_atual": idioma_atual,
            "webpush_vapid_public_key": (
                settings.WEBPUSH_VAPID_PUBLIC_KEY
            ),
        },
    )


@csrf_exempt
@require_POST
def logout_utilizador(request):

    logout(request)

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Sessão terminada com sucesso.",
            "redirect": "/"
        },
        status=200
    )

@ensure_csrf_cookie
def pagina_registar(request):
    cursos = Curso.objects.all().order_by("nome")

    return render(
        request,
        "registar.html",
        {"cursos": cursos}
    )