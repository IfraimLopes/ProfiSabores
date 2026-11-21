// ==========================================
// PROFISABORES — NOTIFICAÇÕES NATIVAS
// ==========================================

console.log("PROFISABORES: notificacoes.js carregado");

document.addEventListener("DOMContentLoaded", async () => {

    const plugins = window.CapacitorPlugins;

    if (!plugins) {
        console.log(
            "Profisabores: aplicação a correr no navegador."
        );
        return;
    }

    const {
        Capacitor,
        PushNotifications,
        LocalNotifications
    } = plugins;

    if (!Capacitor.isNativePlatform()) {
        console.log(
            "Profisabores: plataforma Web, mantém-se o Web Push."
        );
        return;
    }

    const plataforma = Capacitor.getPlatform();

    console.log(
        "Profisabores: aplicação nativa detetada:",
        plataforma
    );

    try {

        // ==========================================
        // PERMISSÕES
        // ==========================================

        let permissao =
            await PushNotifications.checkPermissions();

        if (permissao.receive === "prompt") {
            permissao =
                await PushNotifications.requestPermissions();
        }

        if (permissao.receive !== "granted") {
            console.warn(
                "Profisabores: permissão de notificações recusada."
            );
            return;
        }

        // ==========================================
        // REGISTO DO TOKEN FCM
        // ==========================================

        await PushNotifications.addListener(
            "registration",
            async (token) => {

                console.log(
                    "Profisabores: token FCM recebido.",
                    token.value.substring(0, 12) + "..."
                );

                try {

                    const resposta = await fetch(
                        "/reservas/dispositivo/",
                        {
                            method: "POST",
                            credentials: "same-origin",
                            headers: {
                                "Content-Type":
                                    "application/x-www-form-urlencoded"
                            },
                            body: new URLSearchParams({
                                token: token.value,
                                plataforma: plataforma
                            })
                        }
                    );

                    const resultado = await resposta.json();

                    if (!resposta.ok) {
                        console.error(
                            "Profisabores: erro ao registar dispositivo:",
                            resposta.status,
                            resultado
                        );
                        return;
                    }

                    console.log(
                        "Profisabores: dispositivo registado:",
                        resultado
                    );

                } catch (erro) {

                    console.error(
                        "Profisabores: erro ao enviar token:",
                        erro
                    );

                }
            }
        );

        // ==========================================
        // ERRO DE REGISTO
        // ==========================================

        await PushNotifications.addListener(
            "registrationError",
            (erro) => {
                console.error(
                    "Profisabores: erro de registo FCM:",
                    erro
                );
            }
        );

        // ==========================================
        // NOTIFICAÇÃO RECEBIDA EM PRIMEIRO PLANO
        // ==========================================

        await PushNotifications.addListener(
            "pushNotificationReceived",
            async (notificacao) => {

                console.log(
                    "Profisabores: notificação recebida:",
                    notificacao
                );

                try {

                    await LocalNotifications.schedule({
                        notifications: [
                            {
                                id: Math.floor(
                                    Date.now() % 2147483647
                                ),
                                title:
                                    notificacao.title ||
                                    "🍽️ Profisabores",
                                body:
                                    notificacao.body ||
                                    "Recebeste uma nova notificação.",
                                sound: "default"
                            }
                        ]
                    });

                    console.log(
                        "Profisabores: notificação local apresentada."
                    );

                } catch (erro) {

                    console.error(
                        "Profisabores: erro na notificação local:",
                        erro
                    );

                }
            }
        );

        // ==========================================
        // UTILIZADOR ABRIU UMA NOTIFICAÇÃO
        // ==========================================

        await PushNotifications.addListener(
            "pushNotificationActionPerformed",
            (evento) => {

                console.log(
                    "Profisabores: notificação aberta:",
                    evento
                );

            }
        );

        // ==========================================
        // REGISTAR NO FCM
        // ==========================================

        await PushNotifications.register();

        console.log(
            "Profisabores: pedido de registo FCM efetuado."
        );

    } catch (erro) {

        console.error(
            "Profisabores: erro na configuração:",
            erro
        );

    }

});
