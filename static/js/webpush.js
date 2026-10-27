"use strict";

(function () {
    const botao = document.getElementById("webPushButton");
    const estado = document.getElementById("webPushStatus");
    const formularioCSRF = document.getElementById("webPushCsrfForm");

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
            "As notificações são geridas pela aplicação nativa.";
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
            "Para ativares as notificações no iPhone, adiciona primeiro " +
            "o Profisabores ao ecrã principal. No Safari, toca em Partilhar, " +
            "escolhe Adicionar ao ecrã principal e abre o Profisabores " +
            "através do novo ícone."
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
                resultado.erro || "Não foi possível guardar a subscrição."
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
                "Este navegador não suporta notificações Web Push."
            );
            return;
        }

        if (!window.isSecureContext) {
            mostrarEstado(
                "As notificações exigem HTTPS ou localhost em desenvolvimento."
            );
            return;
        }

        if (!chavePublica) {
            mostrarEstado(
                "A chave pública de notificações não está configurada."
            );
            return;
        }

        botao.disabled = true;
        mostrarEstado("A preparar as notificações…");

        try {
            let permissao = Notification.permission;

            if (permissao === "default") {
                permissao = await Notification.requestPermission();
            }

            if (permissao !== "granted") {
                mostrarEstado(
                    permissao === "denied"
                        ? "As notificações estão bloqueadas nas definições do navegador."
                        : "Não autorizaste as notificações."
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
                '<i class="fa-solid fa-check"></i> Notificações ativadas';

            mostrarEstado(
                "As notificações do navegador estão ativadas para esta conta."
            );
            window.dispatchEvent(
                new Event("profisabores:notificacoes-ativadas")
            );
        } catch (erro) {
            console.error("Profisabores Web Push:", erro);

            mostrarEstado(
                erro.message ||
                "Não foi possível ativar as notificações. Tenta novamente."
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
            "Já autorizaste as notificações neste navegador. Podes confirmar a subscrição através do botão."
        );
    }
})();
