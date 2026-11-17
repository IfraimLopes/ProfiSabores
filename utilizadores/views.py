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
    EmailAutorizado,
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
    nome = request.POST.get("nome", "").strip()
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")
    telemovel = request.POST.get("telemovel", "").strip()
    tipo_formulario = request.POST.get("tipo", "").strip().lower()
    curso_id = request.POST.get("curso", "").strip()
    sexo = request.POST.get("sexo", "").strip().lower()
    data_nascimento = request.POST.get("data_nascimento", "").strip()

    if not nome or not email or not password or not telemovel:
        return JsonResponse(
            {"erro": "Preencha todos os campos obrigatórios."},
            status=400
        )

    if len(password) < 8:
        return JsonResponse(
            {"erro": "A palavra-passe deve ter pelo menos 8 caracteres."},
            status=400
        )

    if sexo not in ["masculino", "feminino", "outro"]:
        return JsonResponse(
            {"erro": "Sexo inválido."},
            status=400
        )

    try:
        data_nascimento = datetime.strptime(
            data_nascimento, "%Y-%m-%d"
        ).date()
    except ValueError:
        return JsonResponse(
            {"erro": "A data de nascimento é inválida."},
            status=400
        )

    # A autorização determina o tipo real da conta.
    autorizacao = EmailAutorizado.objects.filter(
        email__iexact=email,
        ativo=True
    ).first()

    if not autorizacao:
        return JsonResponse(
            {"erro": "Não foi possível autorizar este registo."},
            status=403
        )

    tipo = autorizacao.tipo

    if tipo_formulario != tipo:
        return JsonResponse(
            {"erro": "O tipo de conta não corresponde à autorização."},
            status=403
        )

    curso = None

    if tipo == "aluno":
        if not curso_id:
            return JsonResponse(
                {"erro": "O curso é obrigatório para alunos."},
                status=400
            )

        try:
            curso = Curso.objects.get(pk=curso_id)
        except (Curso.DoesNotExist, ValueError):
            return JsonResponse(
                {"erro": "Curso inválido."},
                status=400
            )

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {"erro": "Já existe uma conta com este e-mail."},
            status=400
        )

    codigo = gerar_codigo()

    try:
        with transaction.atomic():
            utilizador = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=nome,
                is_active=False
            )

            Perfil.objects.create(
                utilizador=utilizador,
                nome_completo=nome,
                tipo=tipo,
                telemovel=telemovel,
                sexo=sexo,
                data_nascimento=data_nascimento,
                curso=curso,
                verificado=False
            )

            CodigoVerificacao.objects.create(
                email=email,
                codigo=codigo,
                finalidade="registo",
                expira_em=timezone.now() + timedelta(minutes=10)
            )

    except Exception:
        return JsonResponse(
            {"erro": "Não foi possível criar a conta."},
            status=400
        )

    send_mail(
        "Código de verificação - Restaurante Profitecla",
        (
            f"O seu código de verificação é: {codigo}\n\n"
            "Este código é válido durante 10 minutos."
        ),
        None,
        [email],
        fail_silently=False,
    )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Conta criada. Verifique o seu e-mail.",
            "email": email,
        },
        status=201
    )



def gerar_codigo():
    """Gera um PIN numérico de 6 dígitos."""
    return f"{secrets.randbelow(1_000_000):06d}"


@csrf_exempt
@require_POST
def verificar_registo(request):
    email = request.POST.get("email", "").strip().lower()
    codigo_digitado = request.POST.get("codigo", "").strip()

    if not email or not codigo_digitado:
        return JsonResponse(
            {"erro": "O e-mail e o PIN são obrigatórios."},
            status=400
        )

    autorizacao = EmailAutorizado.objects.filter(
        email__iexact=email,
        ativo=True
    ).first()

    if not autorizacao:
        return JsonResponse(
            {"erro": "A autorização deste registo não está ativa."},
            status=403
        )

    codigo_obj = (
        CodigoVerificacao.objects
        .filter(
            email__iexact=email,
            finalidade="registo",
            usado=False
        )
        .order_by("-criado_em")
        .first()
    )

    if not codigo_obj:
        return JsonResponse(
            {"erro": "Não existe um PIN válido para este registo."},
            status=400
        )

    if timezone.now() > codigo_obj.expira_em:
        codigo_obj.usado = True
        codigo_obj.save(update_fields=["usado"])
        return JsonResponse(
            {"erro": "O PIN expirou. Solicite um novo código."},
            status=400
        )

    if codigo_obj.tentativas >= 5:
        codigo_obj.usado = True
        codigo_obj.save(update_fields=["usado"])
        return JsonResponse(
            {"erro": "Limite de tentativas atingido. Solicite um novo PIN."},
            status=400
        )

    codigo_obj.tentativas += 1
    codigo_obj.save(update_fields=["tentativas"])

    if not secrets.compare_digest(codigo_digitado, codigo_obj.codigo):
        return JsonResponse(
            {"erro": "PIN incorreto."},
            status=400
        )

    try:
        with transaction.atomic():
            utilizador = User.objects.get(email__iexact=email)
            perfil = Perfil.objects.get(utilizador=utilizador)

            if perfil.tipo != autorizacao.tipo:
                raise ValueError("Tipo de conta incompatível.")

            if utilizador.is_active or perfil.verificado:
                raise ValueError("Conta já verificada.")

            if autorizacao.tipo == "aluno":
                if not perfil.curso_id:
                    raise ValueError("O aluno não tem curso associado.")

                if Staff.objects.filter(email__iexact=email).exists():
                    raise ValueError("Email já associado a Staff.")

                Aluno.objects.get_or_create(
                    utilizador=utilizador,
                    defaults={
                        "nome": perfil.nome_completo,
                        "email": email,
                        "curso": perfil.curso,
                    }
                )

            else:
                if Aluno.objects.filter(email__iexact=email).exists():
                    raise ValueError("Email já associado a Aluno.")

                Staff.objects.get_or_create(
                    utilizador=utilizador,
                    defaults={
                        "nome": perfil.nome_completo,
                        "email": email,
                    }
                )

            PreferenciasUtilizador.objects.get_or_create(
                utilizador=utilizador,
                defaults={"idioma": perfil.idioma}
            )

            utilizador.is_active = True
            utilizador.save(update_fields=["is_active"])

            perfil.verificado = True
            perfil.save(update_fields=["verificado"])

            codigo_obj.usado = True
            codigo_obj.save(update_fields=["usado"])

    except (User.DoesNotExist, Perfil.DoesNotExist, ValueError):
        return JsonResponse(
            {"erro": "Não foi possível validar esta conta."},
            status=400
        )

    except Exception:
        return JsonResponse(
            {"erro": "Ocorreu um erro ao validar a conta."},
            status=400
        )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Conta verificada com sucesso. Já pode iniciar sessão.",
            "redirect": "/utilizadores/login/"
        },
        status=200
    )


# ============================================================
# LOGIN
# ============================================================

def dominio_institucional_permitido(email):
    dominios_permitidos = {
        "alunos.profitecla.pt",
        "professores.profitecla.pt",
        "profitecla.pt",
    }

    if "@" not in email:
        return False

    dominio = email.rsplit("@", 1)[1].lower()
    return dominio in dominios_permitidos


def obter_utilizador_aluno_staff(email):
    """
    Devolve apenas utilizadores ativos, autorizados e associados
    ao tipo de conta correspondente.
    """

    autorizacao = EmailAutorizado.objects.filter(
        email__iexact=email,
        ativo=True
    ).first()

    if not autorizacao:
        return None

    if autorizacao.tipo == "aluno":
        conta = (
            Aluno.objects
            .select_related("utilizador")
            .filter(email__iexact=email)
            .first()
        )

        if Staff.objects.filter(email__iexact=email).exists():
            return None

    elif autorizacao.tipo == "staff":
        conta = (
            Staff.objects
            .select_related("utilizador")
            .filter(email__iexact=email)
            .first()
        )

        if Aluno.objects.filter(email__iexact=email).exists():
            return None

    else:
        return None

    if not conta:
        return None

    utilizador = conta.utilizador

    if not utilizador.is_active:
        return None

    if utilizador.email.strip().lower() != email:
        return None

    return utilizador


@csrf_exempt
@require_POST
def login_utilizador(request):
    email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse(
            {"erro": "O e-mail é obrigatório."},
            status=400
        )

    if not dominio_institucional_permitido(email):
        return JsonResponse(
            {
                "erro": (
                    "Utilize o seu e-mail institucional "
                    "da Profitecla."
                )
            },
            status=400
        )

    utilizador = obter_utilizador_aluno_staff(email)

    if utilizador:
        # Invalidar todos os códigos de login anteriores.
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

    # Resposta genérica para não revelar se o endereço está registado.
    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": (
                "Se existir uma conta ativa associada a este e-mail, "
                "receberá um código de acesso."
            ),
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
    codigo_obj.save(update_fields=["tentativas"])

    if not secrets.compare_digest(
        codigo_digitado,
        codigo_obj.codigo
    ):
        return JsonResponse(
            {"erro": "Código incorreto."},
            status=400
        )

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
def pagina_login(request):
    return render(request, "login.html")


@ensure_csrf_cookie
def pagina_verificar_registo(request):
    return render(request, "verificar-registo.html")


@ensure_csrf_cookie
def pagina_verificar_login(request):
    return render(request, "verificar-login.html")


@ensure_csrf_cookie
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