import json
import re
from reservas.notificacoes import (
    enviar_notificacao_utilizador,
    enviar_notificacao_visitante,
)
from decimal import Decimal
import secrets

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import (
    Reserva,
    ReservaExtra,
    Dispositivo,
    SubscricaoWebPush,
)
from menu.models import Prato, Sobremesa, Ementa, Extra

# --------------------------------------------------------------
# IDENTIFICAÇÃO PERSISTENTE DOS VISITANTES
# --------------------------------------------------------------

COOKIE_VISITANTE = "profisabores_visitante"
DURACAO_COOKIE_VISITANTE = 60 * 60 * 24 * 30


def obter_token_visitante(request):
    """
    Obtém a identificação persistente do visitante.
    Se não existir, gera uma nova identificação segura.
    """

    token = request.COOKIES.get(COOKIE_VISITANTE)

    if (
        not token
        or len(token) > 64
        or not token.isascii()
        or not all(
            caracter.isalnum() or caracter in "-_"
            for caracter in token
        )
    ):
        token = secrets.token_urlsafe(32)

    return token

def definir_cookie_visitante(resposta, token, request):
    """
    Guarda a identificação do visitante numa cookie persistente.
    """

    resposta.set_cookie(
        COOKIE_VISITANTE,
        token,
        max_age=DURACAO_COOKIE_VISITANTE,
        httponly=True,
        secure=request.is_secure(),
        samesite="Lax",
        path="/",
    )

    return resposta






@csrf_exempt
@require_POST
def criar_reserva(request):

    # ----------------------------------------------------------
    # IDENTIFICAR O UTILIZADOR
    # ----------------------------------------------------------

    autenticado = request.user.is_authenticated

    token_visitante = None

    if not autenticado:
        token_visitante = obter_token_visitante(request)

    if autenticado:
        try:
            perfil = request.user.perfil
        except AttributeError:
            return JsonResponse(
                {"erro": "O perfil do utilizador não foi encontrado."},
                status=400
            )

        tipo_utilizador = perfil.tipo
        nome_reserva = perfil.nome_completo
        telemovel_reserva = perfil.telemovel
        curso = perfil.curso

    else:
        # Os visitantes não precisam de criar uma conta.
        nome_reserva = request.POST.get("nome", "").strip()
        telemovel_reserva = request.POST.get("telemovel", "").strip()
        tipo_utilizador = "visitante"
        curso = None

        if not nome_reserva or not telemovel_reserva:
            return JsonResponse(
                {
                    "erro": "O nome completo e o telemóvel são obrigatórios."
                },
                status=400
            )

        if len(nome_reserva) > 100 or len(telemovel_reserva) > 20:
            return JsonResponse(
                {"erro": "O nome ou o telemóvel excede o tamanho permitido."},
                status=400
            )
                # O nome deve conter apenas letras e separadores permitidos.
        nome_valido = re.fullmatch(
            r"[^\W\d_]+(?:[ '\u2019-][^\W\d_]+)*",
            nome_reserva,
            flags=re.UNICODE
        )

        if not nome_valido:
            return JsonResponse(
                {
                    "erro": "O nome só pode conter letras, espaços, hífen ou apóstrofo."
                },
                status=400
            )

        # Validar o número internacional no formato E.164.
        # Exemplo: +351912345678.
        telemovel_valido = re.fullmatch(
            r"\+[1-9]\d{6,14}",
            telemovel_reserva
        )

        if not telemovel_valido:
            return JsonResponse(
                {
                    "erro": "Introduz um número de telemóvel internacional válido, incluindo o indicativo do país."
                },
                status=400
            )

        
    # ----------------------------------------------------------
    # RECEBER E VALIDAR OS DADOS
    # ----------------------------------------------------------

    prato_id = request.POST.get("prato_id", "").strip()
    sobremesa_id = request.POST.get("sobremesa_id", "").strip()
    ementa_id = request.POST.get("ementa_id", "").strip()
    extras_ids = request.POST.getlist("extras")
    alergias = request.POST.get("alergias", "").strip()

    # Remover IDs repetidos sem alterar a ordem.
    extras_ids = list(dict.fromkeys(extras_ids))

    tipos_escolhidos = sum(
        bool(valor)
        for valor in (prato_id, sobremesa_id, ementa_id)
    )

    if tipos_escolhidos != 1:
        return JsonResponse(
            {"erro": "Escolha uma ementa, um prato ou uma sobremesa."},
            status=400
        )

    if extras_ids and not ementa_id:
        return JsonResponse(
            {"erro": "Os extras só podem ser selecionados numa ementa."},
            status=400
        )

    # ----------------------------------------------------------
    # INICIALIZAR OS ITENS DA RESERVA
    # ----------------------------------------------------------

    prato = None
    sobremesa = None
    ementa = None
    extras = []
    preco = None

    # ----------------------------------------------------------
    # EMENTA E EXTRAS
    # ----------------------------------------------------------

    if ementa_id:

        try:
            ementa = Ementa.objects.get(
                pk=ementa_id,
                publicada=True,
                ativa=True
            )
        except (Ementa.DoesNotExist, ValueError):
            return JsonResponse(
                {"erro": "Ementa não encontrada ou indisponível."},
                status=404
            )

        if tipo_utilizador == "visitante":
            preco = ementa.preco_base_visitante
        elif tipo_utilizador == "staff":
            preco = ementa.preco_base_staff
        else:
            preco = ementa.preco_base_aluno

        if any(
            not identificador.isdigit()
            for identificador in extras_ids
        ):
            return JsonResponse(
                {"erro": "Foi enviado um identificador de extra inválido."},
                status=400
            )

        if extras_ids:
            extras = list(
                Extra.objects.filter(
                    pk__in=extras_ids,
                    ementa=ementa,
                    ativo=True
                )
            )

            if len(extras) != len(extras_ids):
                return JsonResponse(
                    {
                        "erro": (
                            "Um ou mais extras não existem, "
                            "estão indisponíveis ou não pertencem "
                            "a esta ementa."
                        )
                    },
                    status=400
                )

        data = ementa.data_refeicao

    # ----------------------------------------------------------
    # PRATO — COMPATIBILIDADE COM A ESTRUTURA ANTIGA
    # ----------------------------------------------------------

    elif prato_id:

        try:
            prato = Prato.objects.get(
                pk=prato_id,
                disponivel=True
            )
        except (Prato.DoesNotExist, ValueError):
            return JsonResponse(
                {"erro": "Prato não encontrado ou indisponível."},
                status=404
            )

        if (
            tipo_utilizador in ("staff", "visitante")
            and prato.preco_profissional is not None
        ):
            preco = prato.preco_profissional
        else:
            preco = prato.preco_aluno

        data = timezone.localdate()

    # ----------------------------------------------------------
    # SOBREMESA — COMPATIBILIDADE COM A ESTRUTURA ANTIGA
    # ----------------------------------------------------------

    else:

        try:
            sobremesa = Sobremesa.objects.get(
                pk=sobremesa_id,
                disponivel=True
            )
        except (Sobremesa.DoesNotExist, ValueError):
            return JsonResponse(
                {"erro": "Sobremesa não encontrada ou indisponível."},
                status=404
            )

        if (
            tipo_utilizador in ("staff", "visitante")
            and sobremesa.preco_profissional is not None
        ):
            preco = sobremesa.preco_profissional
        else:
            preco = sobremesa.preco_aluno

        data = timezone.localdate()

    if preco is None:
        return JsonResponse(
            {"erro": "Este item ainda não tem preço definido."},
            status=400
        )

    # ----------------------------------------------------------
    # CALCULAR OS PREÇOS DOS EXTRAS NO SERVIDOR
    # ----------------------------------------------------------

    precos_extras = []

    for extra in extras:

        if tipo_utilizador == "visitante":
            preco_extra = extra.preco_visitante
        elif tipo_utilizador == "staff":
            preco_extra = extra.preco_staff
        else:
            preco_extra = extra.preco_aluno

        if preco_extra is None:
            return JsonResponse(
                {
                    "erro": (
                        f"O extra «{extra.nome}» "
                        "não tem preço definido."
                    )
                },
                status=400
            )

        precos_extras.append((extra, preco_extra))

    total = preco + sum(
        (preco_extra for _, preco_extra in precos_extras),
        start=Decimal("0.00")
    )

    # ----------------------------------------------------------
    # CRIAR A RESERVA E OS EXTRAS
    # ----------------------------------------------------------

    with transaction.atomic():

        reserva = Reserva.objects.create(
        utilizador=request.user if autenticado else None,
        visitante_token=token_visitante,
        nome=nome_reserva,
        telemovel=telemovel_reserva,
        curso=curso,
        ementa=ementa,
        prato=prato,
        sobremesa=sobremesa,
        data=data,
        hora="13:00",
        alergias=alergias,
        preco_unitario=preco,
        total=total,
        estado="confirmada"
        )

        for extra, preco_extra in precos_extras:
            ReservaExtra.objects.create(
                reserva=reserva,
                extra=extra,
                preco=preco_extra,
                quantidade=1
            )

    # ----------------------------------------------------------
    # GUARDAR A RESERVA NA SESSÃO DO VISITANTE
    # ----------------------------------------------------------

    if not autenticado:

        reservas_visitante = request.session.get(
            "reservas_visitante", []
        )

        # Garantir que a lista da sessão é válida.
        if not isinstance(reservas_visitante, list):
            reservas_visitante = []

        reservas_visitante.append(reserva.id)

        request.session["reservas_visitante"] = reservas_visitante
        request.session.modified = True

    # ----------------------------------------------------------
    # ----------------------------------------------------------
    # NOTIFICAÇÃO DA RESERVA — UTILIZADORES E VISITANTES
    # ----------------------------------------------------------

    if reserva.ementa:
        item_reserva = (
            "Ementa de "
            f"{reserva.ementa.data_refeicao.strftime('%d/%m/%Y')}"
        )
    elif reserva.prato:
        item_reserva = reserva.prato.nome
    elif reserva.sobremesa:
        item_reserva = reserva.sobremesa.nome
    else:
        item_reserva = "a refeição"

    titulo_notificacao = "🍽️ Profisabores"
    mensagem_notificacao = (
        f"A tua reserva de {item_reserva} para "
        f"{reserva.data.strftime('%d/%m/%Y')} foi registada "
        "e está a aguardar pagamento."
    )

    if autenticado:
        resultado_notificacao = enviar_notificacao_utilizador(
            request.user,
            titulo_notificacao,
            mensagem_notificacao
        )
    else:
        resultado_notificacao = enviar_notificacao_visitante(
            token_visitante,
            titulo_notificacao,
            mensagem_notificacao
        )

    print(
        "PROFISABORES DEBUG — NOTIFICAÇÕES DA RESERVA ENVIADAS:",
        resultado_notificacao
    )

    # ----------------------------------------------------------
    # RESPOSTA JSON
    # ----------------------------------------------------------

    resposta = JsonResponse(
        {
            "sucesso": True,
            "mensagem": "Reserva criada com sucesso.",
            "reserva": {
                "id": reserva.id,
                "nome": reserva.nome,
                "telemovel": reserva.telemovel,
                "curso": (
                    reserva.curso.codigo
                    if reserva.curso else None
                ),
                "ementa": (
                    {
                        "id": reserva.ementa.id,
                        "data_refeicao": str(
                            reserva.ementa.data_refeicao
                        ),
                        "descricao": reserva.ementa.descricao,
                    }
                    if reserva.ementa else None
                ),
                "extras": [
                    {
                        "id": reserva_extra.extra.id,
                        "nome": reserva_extra.extra.nome,
                        "quantidade": reserva_extra.quantidade,
                        "preco": str(reserva_extra.preco),
                    }
                    for reserva_extra in (
                        reserva.extras.select_related("extra")
                    )
                ],
                "prato": (
                    reserva.prato.nome
                    if reserva.prato else None
                ),
                "sobremesa": (
                    reserva.sobremesa.nome
                    if reserva.sobremesa else None
                ),
                "data": str(reserva.data),
                "hora": str(reserva.hora),
                "alergias": reserva.alergias,
                "preco_unitario": str(reserva.preco_unitario),
                "total": str(reserva.total),
                "estado": reserva.estado,
                "estado_preparacao": reserva.estado_preparacao,
                "tipo_utilizador": tipo_utilizador,
            }
        }
    )

    if not autenticado:
        definir_cookie_visitante(
            resposta,
            token_visitante,
            request
        )

    return resposta


# --------------------------------------------------------------
# PÁGINA DE RESERVAS
# --------------------------------------------------------------

def pagina_reservas(request):
    # Os visitantes também podem consultar a página.
    return render(request, "reservas.html")



# --------------------------------------------------------------
# CONSULTAR AS MINHAS RESERVAS
# --------------------------------------------------------------

def minhas_reservas(request):

    token_visitante = None

    if request.user.is_authenticated:
        # Alunos e funcionários só veem as suas reservas.
        reservas = Reserva.objects.filter(
            utilizador=request.user
        )

    else:
        # Identificação persistente do visitante.
        token_visitante = obter_token_visitante(request)

        reservas_visitante = request.session.get(
            "reservas_visitante", []
        )

        if not isinstance(reservas_visitante, list):
            reservas_visitante = []

        # Associar apenas reservas antigas sem token.
        if reservas_visitante:
            Reserva.objects.filter(
                id__in=reservas_visitante,
                utilizador__isnull=True,
                visitante_token__isnull=True
            ).update(
                visitante_token=token_visitante
            )

        # Listar apenas reservas pertencentes ao token atual.
        reservas = Reserva.objects.filter(
            utilizador__isnull=True,
            visitante_token=token_visitante
        )

    reservas = (
        reservas
        .select_related(
            "curso",
            "ementa",
            "prato",
            "sobremesa",
        )
        .prefetch_related("extras__extra")
        .order_by("-data", "-hora")
    )

    lista = []

    for reserva in reservas:

        extras = [
            {
                "id": reserva_extra.extra.id,
                "nome": reserva_extra.extra.nome,
                "tipo": reserva_extra.extra.tipo,
                "quantidade": reserva_extra.quantidade,
                "preco": str(reserva_extra.preco),
                "subtotal": str(
                    reserva_extra.preco
                    * reserva_extra.quantidade
                ),
            }
            for reserva_extra in reserva.extras.all()
        ]

        lista.append({
            "id": reserva.id,
            "nome": reserva.nome,
            "telemovel": reserva.telemovel,
            "curso": (
                reserva.curso.codigo
                if reserva.curso else None
            ),
            "ementa": (
                {
                    "id": reserva.ementa.id,
                    "data_refeicao": str(
                        reserva.ementa.data_refeicao
                    ),
                    "descricao": reserva.ementa.descricao,
                }
                if reserva.ementa else None
            ),
            "extras": extras,
            "prato": (
                reserva.prato.nome
                if reserva.prato else None
            ),
            "sobremesa": (
                reserva.sobremesa.nome
                if reserva.sobremesa else None
            ),
            "data": str(reserva.data),
            "hora": str(reserva.hora),
            "alergias": reserva.alergias,
            "preco_unitario": str(reserva.preco_unitario),
            "total": str(reserva.total),
            "estado": reserva.estado,
            "estado_preparacao": reserva.estado_preparacao,
            "criada_em": (
                reserva.criada_em.isoformat()
                if reserva.criada_em else None
            ),
            "cancelada_em": (
                reserva.cancelada_em.isoformat()
                if reserva.cancelada_em else None
            ),
        })

    resposta = JsonResponse({"reservas": lista})

    if not request.user.is_authenticated:
        definir_cookie_visitante(
            resposta,
            token_visitante,
            request
        )

    return resposta


# --------------------------------------------------------------
# CANCELAR UMA RESERVA
# --------------------------------------------------------------

@csrf_exempt
@require_POST
def cancelar_reserva(request, reserva_id):

    token_visitante = None

    if request.user.is_authenticated:
        # Alunos e funcionários só cancelam as suas reservas.
        reserva = Reserva.objects.filter(
            id=reserva_id,
            utilizador=request.user
        ).first()

    else:
        # Identificação persistente do visitante.
        token_visitante = obter_token_visitante(request)

        reservas_visitante = request.session.get(
            "reservas_visitante", []
        )

        if not isinstance(reservas_visitante, list):
            reservas_visitante = []

        # Procurar uma reserva pertencente ao token atual.
        reserva = Reserva.objects.filter(
            id=reserva_id,
            utilizador__isnull=True,
            visitante_token=token_visitante
        ).first()

        # Compatibilidade com reservas antigas da sessão.
        if (
            reserva is None
            and reserva_id in reservas_visitante
        ):
            reserva = Reserva.objects.filter(
                id=reserva_id,
                utilizador__isnull=True,
                visitante_token__isnull=True
            ).first()

            if reserva is not None:
                reserva.visitante_token = token_visitante
                reserva.save(
                    update_fields=["visitante_token"]
                )

    if reserva is None:
        return JsonResponse(
            {"erro": "Reserva não encontrada."},
            status=404
        )

    if reserva.estado_preparacao == "feito":
        resposta = JsonResponse(
            {
                "erro": (
                    "A refeição já está feita. "
                    "Não é possível cancelar esta reserva."
                ),
                "estado_preparacao": reserva.estado_preparacao,
            },
            status=400
        )

        if not request.user.is_authenticated:
            definir_cookie_visitante(
                resposta,
                token_visitante,
                request
            )

        return resposta

    if reserva.estado == "cancelada":
        resposta = JsonResponse(
            {"erro": "Esta reserva já foi cancelada."},
            status=400
        )

        if not request.user.is_authenticated:
            definir_cookie_visitante(
                resposta,
                token_visitante,
                request
            )

        return resposta

    reserva.estado = "cancelada"
    reserva.cancelada_em = timezone.now()

    reserva.save(
        update_fields=[
            "estado",
            "cancelada_em"
        ]
    )

    resposta = JsonResponse({
        "sucesso": True,
        "mensagem": "Reserva cancelada com sucesso.",
        "reserva_id": reserva.id,
        "estado": reserva.estado,
    })

    if not request.user.is_authenticated:
        definir_cookie_visitante(
            resposta,
            token_visitante,
            request
        )

    return resposta


# REGISTAR DISPOSITIVO PARA NOTIFICAÇÕES
# --------------------------------------------------------------

@csrf_exempt
@require_POST
def registar_dispositivo(request):

    if not request.user.is_authenticated:
        return JsonResponse(
            {"erro": "É necessário iniciar sessão."},
            status=401
        )

    token = request.POST.get("token", "").strip()
    plataforma = request.POST.get("plataforma", "").strip().lower()

    if not token:
        return JsonResponse(
            {"erro": "O token do dispositivo é obrigatório."},
            status=400
        )

    if plataforma not in ("ios", "android"):
        return JsonResponse(
            {"erro": "A plataforma deve ser ios ou android."},
            status=400
        )

    dispositivo, criado = Dispositivo.objects.update_or_create(
        token=token,
        defaults={
            "utilizador": request.user,
            "plataforma": plataforma,
            "ativo": True,
        }
    )

    return JsonResponse(
        {
            "sucesso": True,
            "criado": criado,
            "mensagem": "Dispositivo registado com sucesso.",
            "plataforma": dispositivo.plataforma,
        }
    )


# REGISTAR SUBSCRIÇÃO WEB PUSH
# --------------------------------------------------------------

@require_POST
def registar_subscricao_webpush(request):
    try:
        dados = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"erro": "O JSON enviado é inválido."},
            status=400
        )

    if not isinstance(dados, dict):
        return JsonResponse(
            {"erro": "Os dados enviados são inválidos."},
            status=400
        )

    endpoint = dados.get("endpoint", "")
    chaves = dados.get("keys", {})

    if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
        return JsonResponse(
            {"erro": "O endpoint HTTPS é obrigatório."},
            status=400
        )

    if not isinstance(chaves, dict):
        return JsonResponse(
            {"erro": "As chaves da subscrição são inválidas."},
            status=400
        )

    p256dh = chaves.get("p256dh", "")
    auth = chaves.get("auth", "")

    if (
        not isinstance(p256dh, str) or not p256dh
        or not isinstance(auth, str) or not auth
    ):
        return JsonResponse(
            {"erro": "As chaves da subscrição são obrigatórias."},
            status=400
        )

    autenticado = request.user.is_authenticated
    token_visitante = None

    if not autenticado:
        token_visitante = obter_token_visitante(request)

    subscricao, criada = SubscricaoWebPush.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "utilizador": request.user if autenticado else None,
            "visitante_token": token_visitante,
            "p256dh": p256dh,
            "auth": auth,
            "ativo": True,
        }
    )

    resposta = JsonResponse({
        "sucesso": True,
        "criada": criada,
        "mensagem": "Subscrição Web Push registada com sucesso.",
    })

    if not autenticado:
        definir_cookie_visitante(resposta, token_visitante, request)

    return resposta


# --------------------------------------------------------------
# SERVICE WORKER WEB PUSH
# --------------------------------------------------------------

from django.conf import settings
from django.http import FileResponse


def servir_service_worker(request):
    ficheiro = settings.BASE_DIR / "static" / "js" / "sw.js"

    resposta = FileResponse(
        ficheiro.open("rb"),
        content_type="application/javascript",
    )
    resposta["Service-Worker-Allowed"] = "/"
    resposta["Cache-Control"] = "no-cache"

    return resposta
