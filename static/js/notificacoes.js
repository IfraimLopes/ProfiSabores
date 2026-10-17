// ==========================================
// PROFISABORES — NOTIFICAÇÕES PUSH
// ==========================================

console.log("PROFISABORES: notificacoes.js FOI CARREGADO");
const { LocalNotifications } = Capacitor.Plugins;
document.addEventListener("DOMContentLoaded", async () => {

    // Verificar se estamos dentro do Capacitor
    if (!window.Capacitor) {
        console.log(
            "Profisabores: aplicação a correr no navegador."
        );
        return;
    }

    try {

        const { PushNotifications } =
            Capacitor.Plugins;


        if (!PushNotifications) {

            console.error(
                "Profisabores: plugin PushNotifications não encontrado."
            );

            return;
        }


        // ==========================================
        // PEDIR PERMISSÃO
        // ==========================================

        let permissao =
            await PushNotifications.checkPermissions();


        if (permissao.receive === "prompt") {

            permissao =
                await PushNotifications.requestPermissions();

        }


        if (permissao.receive !== "granted") {

            console.warn(
                "Profisabores: permissão para notificações não concedida."
            );

            return;
        }


        // ==========================================
        // TOKEN FCM
        // ==========================================

        PushNotifications.addListener(
            "registration",
            async (token) => {

                console.log(
                    "================================="
                );

                console.log(
                    "PROFISABORES — TOKEN FCM"
                );

                console.log(
                    token.value
                );

                console.log(
                    "================================="
                );


                // ==========================================
                // ENVIAR TOKEN PARA O DJANGO
                // ==========================================

                try {

                    const resposta =
                        await fetch(
                            "/reservas/dispositivo/",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/x-www-form-urlencoded"
                                },

                                body:
                                    new URLSearchParams({
                                        token:
                                            token.value,

                                        plataforma:
                                            "android"
                                    })
                            }
                        );


                    const resultado =
                        await resposta.json();


                    if (!resposta.ok) {

                        console.error(
                            "Profisabores: erro ao registar dispositivo:",
                            resultado
                        );

                        return;
                    }


                    console.log(
                        "Profisabores: dispositivo registado no Django:",
                        resultado
                    );


                } catch (erro) {

                    console.error(
                        "Profisabores: erro ao enviar token para Django:",
                        erro
                    );

                }

            }
        );


        // ==========================================
        // ERRO DE REGISTO
        // ==========================================

        PushNotifications.addListener(
            "registrationError",
            (erro) => {

                console.error(
                    "Profisabores: erro ao obter token FCM:",
                    erro
                );

            }
        );


        // ==========================================
        // NOTIFICAÇÃO RECEBIDA
        // ==========================================

        PushNotifications.addListener(
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
                                id: Math.floor(Date.now() % 2147483647),
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
                        "Profisabores: erro ao apresentar notificação local:",
                        erro
                    );

                }

            }
    );

        // ==========================================
        // UTILIZADOR TOCOU NA NOTIFICAÇÃO
        // ==========================================

        PushNotifications.addListener(
            "pushNotificationActionPerformed",
            (evento) => {

                console.log(
                    "Profisabores: utilizador abriu a notificação:",
                    evento
                );

            }
        );


        // ==========================================
        // REGISTAR DISPOSITIVO NO FCM
        // ==========================================

        await PushNotifications.register();


    } catch (erro) {

        console.error(
            "Profisabores: erro na configuração das notificações:",
            erro
        );

    }

});