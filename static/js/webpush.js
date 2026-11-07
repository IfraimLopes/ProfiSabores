"use strict";

(function () {
    const botao = document.getElementById("webPushButton");
    const estado = document.getElementById("webPushStatus");
    const formularioCSRF = document.getElementById("webPushCsrfForm");

    const idioma = (
        botao.dataset.language ||
        document.documentElement.lang ||
        "pt-pt"
    ).toLowerCase();

    const traducoes = {
        "pt-pt": {
            nativo: "As notificações são geridas pela aplicação nativa.",
            iphone: "Para ativares as notificações no iPhone, adiciona primeiro o Profisabores ao ecrã principal. No Safari, toca em Partilhar, escolhe Adicionar ao ecrã principal e abre o Profisabores através do novo ícone.",
            guardar: "Não foi possível guardar a subscrição.",
            navegador: "Este navegador não suporta notificações Web Push.",
            https: "As notificações exigem HTTPS ou localhost em desenvolvimento.",
            chave: "A chave pública de notificações não está configurada.",
            preparar: "A preparar as notificações…",
            bloqueadas: "As notificações estão bloqueadas nas definições do navegador.",
            negar: "Não autorizaste as notificações.",
            ativadas: "Notificações ativadas",
            ativa: "As notificações do navegador estão ativadas para esta conta.",
            erro: "Não foi possível ativar as notificações. Tenta novamente.",
            autorizadas: "Já autorizaste as notificações neste navegador. Podes confirmar a subscrição através do botão."
        },
        en: {
            nativo: "Notifications are managed by the native app.",
            iphone: "To enable notifications on iPhone, first add Profisabores to your Home Screen. In Safari, tap Share, choose Add to Home Screen, then open Profisabores using the new icon.",
            guardar: "Unable to save the subscription.",
            navegador: "This browser does not support Web Push notifications.",
            https: "Notifications require HTTPS or localhost during development.",
            chave: "The notification public key is not configured.",
            preparar: "Preparing notifications…",
            bloqueadas: "Notifications are blocked in your browser settings.",
            negar: "You did not allow notifications.",
            ativadas: "Notifications enabled",
            ativa: "Browser notifications are enabled for this account.",
            erro: "Could not enable notifications. Please try again.",
            autorizadas: "You have already allowed notifications in this browser. You can confirm the subscription using the button."
        },
        es: {
            nativo: "Las notificaciones se gestionan desde la aplicación nativa.",
            iphone: "Para activar las notificaciones en el iPhone, primero añade Profisabores a la pantalla de inicio. En Safari, toca Compartir, selecciona Añadir a pantalla de inicio y abre Profisabores desde el nuevo icono.",
            guardar: "No se pudo guardar la suscripción.",
            navegador: "Este navegador no admite notificaciones Web Push.",
            https: "Las notificaciones requieren HTTPS o localhost durante el desarrollo.",
            chave: "La clave pública de notificaciones no está configurada.",
            preparar: "Preparando las notificaciones…",
            bloqueadas: "Las notificaciones están bloqueadas en la configuración del navegador.",
            negar: "No has permitido las notificaciones.",
            ativadas: "Notificaciones activadas",
            ativa: "Las notificaciones del navegador están activadas para esta cuenta.",
            erro: "No se pudieron activar las notificaciones. Inténtalo de nuevo.",
            autorizadas: "Ya has permitido las notificaciones en este navegador. Puedes confirmar la suscripción con el botón."
        },
        fr: {
            nativo: "Les notifications sont gérées par l’application native.",
            iphone: "Pour activer les notifications sur iPhone, ajoutez d’abord Profisabores à l’écran d’accueil. Dans Safari, touchez Partager, choisissez Sur l’écran d’accueil, puis ouvrez Profisabores avec la nouvelle icône.",
            guardar: "Impossible d’enregistrer l’abonnement.",
            navegador: "Ce navigateur ne prend pas en charge les notifications Web Push.",
            https: "Les notifications nécessitent HTTPS ou localhost en développement.",
            chave: "La clé publique de notification n’est pas configurée.",
            preparar: "Préparation des notifications…",
            bloqueadas: "Les notifications sont bloquées dans les paramètres du navigateur.",
            negar: "Vous n’avez pas autorisé les notifications.",
            ativadas: "Notifications activées",
            ativa: "Les notifications du navigateur sont activées pour ce compte.",
            erro: "Impossible d’activer les notifications. Veuillez réessayer.",
            autorizadas: "Vous avez déjà autorisé les notifications dans ce navigateur. Vous pouvez confirmer l’abonnement à l’aide du bouton."
        }
    };

    const textos = traducoes[idioma] ||
        traducoes[idioma.split("-")[0]] ||
        traducoes["pt-pt"];

    const t = (chave) => textos[chave];

    if (!botao || !estado || !formularioCSRF) {
        return;
    }

    // As aplicações nativas usam notificações FCM via Capacitor.
    const capacitor = window.Capacitor;
    const ambienteNativo =
        capacitor &&
        typeof capacitor.isNativePlatform === "function" &&
        capacitor.isNativePlatform();

    if (ambienteNativo) {
        estado.textContent =
            t("nativo");
        botao.hidden = true;
        return;
    }

    const chavePublica = botao.dataset.vapidPublicKey;

    // Deteção de iPhone/iPad e aplicação instalada.
    const eDispositivoApple =
        /iPhone|iPad|iPod/.test(navigator.userAgent) ||
        (
            navigator.platform === "MacIntel" &&
            navigator.maxTouchPoints > 1
        );

    const estaInstalado =
        window.matchMedia("(display-mode: standalone)").matches ||
        navigator.standalone === true;

    const precisaInstalarNoIPhone =
        eDispositivoApple && !estaInstalado;

    function mostrarInstrucaoInstalacao() {
        mostrarEstado(
            t("iphone")
        );
    }

    const campoCSRF = formularioCSRF.querySelector(
        '[name="csrfmiddlewaretoken"]'
    );

    function mostrarEstado(mensagem) {
        estado.textContent = mensagem;
    }

    function converterChaveBase64Url(valor) {
        const base64 = valor
            .replace(/-/g, "+")
            .replace(/_/g, "/");

        const preenchido = base64.padEnd(
            base64.length + (4 - base64.length % 4) % 4,
            "="
        );

        const binario = atob(preenchido);
        const bytes = new Uint8Array(binario.length);

        for (let i = 0; i < binario.length; i++) {
            bytes[i] = binario.charCodeAt(i);
        }

        return bytes;
    }

    async function guardarSubscricao(subscricao) {
        const resposta = await fetch("/reservas/webpush/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": campoCSRF.value
            },
            body: JSON.stringify(subscricao)
        });

        const resultado = await resposta.json();

        if (!resposta.ok) {
            throw new Error(
                resultado.erro || t("guardar")
            );
        }

        return resultado;
    }

    async function ativarNotificacoes() {
        if (precisaInstalarNoIPhone) {
            mostrarInstrucaoInstalacao();
            return;
        }

        if (!("serviceWorker" in navigator) ||
            !("PushManager" in window) ||
            !("Notification" in window)) {
            mostrarEstado(
                t("navegador")
            );
            return;
        }

        if (!window.isSecureContext) {
            mostrarEstado(
                t("https")
            );
            return;
        }

        if (!chavePublica) {
            mostrarEstado(
                t("chave")
            );
            return;
        }

        botao.disabled = true;
        mostrarEstado(t("preparar"));

        try {
            let permissao = Notification.permission;

            if (permissao === "default") {
                permissao = await Notification.requestPermission();
            }

            if (permissao !== "granted") {
                mostrarEstado(
                    permissao === "denied"
                        ? t("bloqueadas")
                        : t("negar")
                );
                return;
            }

            const registo = await navigator.serviceWorker.register("/sw.js", {
                scope: "/"
            });

            await navigator.serviceWorker.ready;

            let subscricao = await registo.pushManager.getSubscription();
            const chavePublicaAtual = converterChaveBase64Url(chavePublica);

            if (subscricao) {
                const chaveExistente = subscricao.options.applicationServerKey;
                const bytesExistentes = chaveExistente
                    ? new Uint8Array(chaveExistente)
                    : null;

                const chavesCorrespondem =
                    bytesExistentes !== null &&
                    bytesExistentes.length === chavePublicaAtual.length &&
                    bytesExistentes.every(
                        (byte, indice) => byte === chavePublicaAtual[indice]
                    );

                if (!chavesCorrespondem) {
                    await subscricao.unsubscribe();
                    subscricao = null;
                }
            }

            if (!subscricao) {
                subscricao = await registo.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: chavePublicaAtual
                });
            }

            await guardarSubscricao(subscricao.toJSON());

            botao.innerHTML =
                '<i class="fa-solid fa-check"></i> ' + t("ativadas");

            mostrarEstado(
                t("ativa")
            );
            window.dispatchEvent(
                new Event("profisabores:notificacoes-ativadas")
            );
        } catch (erro) {
            console.error("Profisabores Web Push:", erro);

            mostrarEstado(
                erro.message ||
                t("erro")
            );
        } finally {
            botao.disabled = false;
        }
    }


    // Permitir que a janela de onboarding reutilize o Web Push existente.
    window.profIsaboresAtivarNotificacoes = ativarNotificacoes;

    // Explicar a instalação logo ao abrir o perfil no Safari do iPhone.
    if (precisaInstalarNoIPhone) {
        mostrarInstrucaoInstalacao();
    }

    botao.addEventListener("click", ativarNotificacoes);

    if ("Notification" in window &&
        Notification.permission === "granted") {
        mostrarEstado(
            t("autorizadas")
        );
    }
})();
