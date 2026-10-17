from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from menu.models import Curso
from .models import Perfil, CodigoVerificacao


@csrf_exempt
@require_POST

def registar(request):

    nome = request.POST.get("nome", "").strip()
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")
    telemovel = request.POST.get("telemovel", "").strip()
    tipo = request.POST.get("tipo", "").strip().lower()
    curso_id = request.POST.get("curso", "").strip()

    sexo = request.POST.get("sexo", "").strip().lower()
    data_nascimento = request.POST.get("data_nascimento", "").strip()


# Validar campos obrigatórios
    
    # Validar campos obrigatórios

    if not nome:
        return JsonResponse(
            {"erro": "O nome é obrigatório."},
            status=400
        )

    if not email:
        return JsonResponse(
            {"erro": "O e-mail é obrigatório."},
            status=400
        )

    if not password:
        return JsonResponse(
            {"erro": "A palavra-passe é obrigatória."},
            status=400
        )

    if len(password) < 8:
        return JsonResponse(
            {
                "erro": (
                    "A palavra-passe deve ter "
                    "pelo menos 8 caracteres."
                )
            },
            status=400
        )

    if not telemovel:
        return JsonResponse(
            {"erro": "O telemóvel é obrigatório."},
            status=400
        )

    # Validar sexo

    if not sexo:
        return JsonResponse(
            {"erro": "O sexo é obrigatório."},
            status=400
        )

    if sexo not in [
        "masculino",
        "feminino",
        "outro"
    ]:
        return JsonResponse(
            {"erro": "Sexo inválido."},
            status=400
        )

    # Validar ano de nascimento
    # Validar data de nascimento

    if not data_nascimento:
        return JsonResponse(
            {
                "sucesso": False,
                "erro": "A data de nascimento é obrigatória."
            },
            status=400
        )

    try:
        data_nascimento = datetime.strptime(
            data_nascimento,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return JsonResponse(
            {
                "sucesso": False,
                "erro": "A data de nascimento é inválida."
            },
            status=400
        )
    # Validar tipo de utilizador

    if tipo not in ["aluno", "staff"]:
        return JsonResponse(
            {"erro": "Tipo de utilizador inválido."},
            status=400
        )

    # Validar curso: obrigatório apenas para alunos

    curso = None

    if tipo == "aluno":

        if not curso_id:
            return JsonResponse(
                {
                    "erro": (
                        "O curso é obrigatório "
                        "para alunos."
                    )
                },
                status=400
            )

        try:
            curso = Curso.objects.get(pk=curso_id)
        except (Curso.DoesNotExist, ValueError):
            return JsonResponse(
                {"erro": "Curso inválido."},
                status=400
            )

    # Verificar se o e-mail já existe

    if User.objects.filter(email=email).exists():
        return JsonResponse(
            {
                "erro": (
                    "Já existe uma conta "
                    "com este e-mail."
                )
            },
            status=400
        )

    # Criar utilizador inativo até validar o PIN

    utilizador = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=nome,
        is_active=False
    )

    # Criar perfil

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

    # Gerar e guardar PIN

    codigo = gerar_codigo()

    CodigoVerificacao.objects.create(
        email=email,
        codigo=codigo,
        finalidade="registo",
        expira_em=timezone.now() + timedelta(minutes=10)
    )

    # Enviar PIN por e-mail

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
            "mensagem": (
                "Conta criada. Verifique o seu e-mail."
            ),
            "email": email,
        },
        status=201
    )



import secrets


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

    # Procurar o código mais recente de registo ainda não utilizado
    codigo_obj = (
        CodigoVerificacao.objects
        .filter(
            email=email,
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

    # Verificar validade temporal
    if timezone.now() > codigo_obj.expira_em:
        return JsonResponse(
            {"erro": "O PIN expirou. Solicite um novo código."},
            status=400
        )

    # Limitar tentativas
    if codigo_obj.tentativas >= 5:
        return JsonResponse(
            {"erro": "Limite de tentativas atingido. Solicite um novo PIN."},
            status=400
        )

    # Contar a tentativa
    codigo_obj.tentativas += 1
    codigo_obj.save(update_fields=["tentativas"])

    if codigo_digitado != codigo_obj.codigo:
        return JsonResponse(
            {"erro": "PIN incorreto."},
            status=400
        )

    # Encontrar a conta associada
    try:
        utilizador = User.objects.get(email=email)
        perfil = Perfil.objects.get(utilizador=utilizador)
    except (User.DoesNotExist, Perfil.DoesNotExist):
        return JsonResponse(
            {"erro": "Não foi encontrada uma conta para este e-mail."},
            status=404
        )

    # Ativar a conta e verificar o perfil
    utilizador.is_active = True
    utilizador.save(update_fields=["is_active"])

    perfil.verificado = True
    perfil.save(update_fields=["verificado"])

    # Marcar o PIN como utilizado
    codigo_obj.usado = True
    codigo_obj.save(update_fields=["usado"])

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

@csrf_exempt
@require_POST
def login_utilizador(request):
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    if not email or not password:
        return JsonResponse(
            {"erro": "O e-mail e a palavra-passe são obrigatórios."},
            status=400
        )

    try:
        utilizador = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse(
            {"erro": "E-mail ou palavra-passe incorretos."},
            status=401
        )

    if not utilizador.is_active:
        return JsonResponse(
            {"erro": "A conta ainda não foi verificada."},
            status=403
        )

    utilizador_autenticado = authenticate(
        request,
        username=utilizador.username,
        password=password
    )

    if utilizador_autenticado is None:
        return JsonResponse(
            {"erro": "E-mail ou palavra-passe incorretos."},
            status=401
        )

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
            "Este código é válido durante 10 minutos."
        ),
        None,
        [email],
        fail_silently=False,
    )

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Código enviado para o seu e-mail.",
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

    codigo_obj = (
        CodigoVerificacao.objects
        .filter(
            email=email,
            finalidade="login",
            usado=False
        )
        .order_by("-criado_em")
        .first()
    )

    if not codigo_obj:
        return JsonResponse(
            {"erro": "Não existe um código de login válido."},
            status=400
        )

    if timezone.now() > codigo_obj.expira_em:
        return JsonResponse(
            {"erro": "O código expirou. Faça login novamente."},
            status=400
        )

    if codigo_obj.tentativas >= 5:
        return JsonResponse(
            {"erro": "Limite de tentativas atingido."},
            status=400
        )

    codigo_obj.tentativas += 1
    codigo_obj.save(update_fields=["tentativas"])

    if codigo_digitado != codigo_obj.codigo:
        return JsonResponse(
            {"erro": "Código incorreto."},
            status=400
        )

    try:
        utilizador = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse(
            {"erro": "Utilizador não encontrado."},
            status=404
        )

    login(request, utilizador)

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

    try:
        User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse(
            {"erro": "Não existe uma conta com este e-mail."},
            status=404
        )

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
            f"O seu código de recuperação é: {codigo}\n\n"
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

    if codigo_digitado != codigo_obj.codigo:
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

    if not email:
        return JsonResponse(
            {"erro": "O e-mail é obrigatório."},
            status=400
        )

    if not nova_password:
        return JsonResponse(
            {"erro": "A nova palavra-passe é obrigatória."},
            status=400
        )

    if len(nova_password) < 8:
        return JsonResponse(
            {
                "erro": (
                    "A palavra-passe deve ter pelo menos "
                    "8 caracteres."
                )
            },
            status=400
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

    # Se o frontend enviar o código nesta etapa,
    # validamos novamente.
    if codigo_digitado and codigo_digitado != codigo_obj.codigo:
        return JsonResponse(
            {"erro": "Código incorreto."},
            status=400
        )

    try:
        utilizador = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse(
            {"erro": "Utilizador não encontrado."},
            status=404
        )

    utilizador.set_password(nova_password)
    utilizador.save()

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

def pagina_login(request):
    return render(request, "login.html")


def pagina_verificar_registo(request):
    return render(request, "verificar-registo.html")


def pagina_verificar_login(request):
    return render(request, "verificar-login.html")


def pagina_recuperar_password(request):
    return render(request, "recuperar-password.html")


def pagina_registar(request):
    return render(request, "registar.html")


# ============================================================
# PERFIL E LOGOUT
# ============================================================

def pagina_perfil(request):
    from django.conf import settings

    # Visitante sem conta: abrir o perfil sem exigir login.
    if not request.user.is_authenticated:
        return render(
            request,
            "perfil.html",
            {
                "utilizador": None,
                "perfil": None,
                "tipo_utilizador": "visitante",
                "webpush_vapid_public_key": settings.WEBPUSH_VAPID_PUBLIC_KEY,
            }
        )

    # Alunos e funcionários mantêm o perfil atual.
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil = None

    return render(
        request,
        "perfil.html",
        {
            "utilizador": request.user,
            "webpush_vapid_public_key": settings.WEBPUSH_VAPID_PUBLIC_KEY,
            "perfil": perfil,
            "tipo_utilizador": (
                perfil.tipo if perfil else None
            ),
        }
    )


@csrf_exempt
@require_POST
def logout_utilizador(request):

    logout(request)

    return JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Sessão terminada com sucesso.",
            "redirect": "/utilizadores/login/"
        },
        status=200
    )

def pagina_registar(request):
    cursos = Curso.objects.all().order_by("nome")

    return render(
        request,
        "registar.html",
        {"cursos": cursos}
    )