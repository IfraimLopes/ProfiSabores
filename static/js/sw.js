"use strict";

self.addEventListener("push", function (event) {
    let dados = {
        title: "Profisabores",
        body: "Tens uma nova notificação.",
        url: "/"
    };

    if (event.data) {
        try {
            const recebidos = event.data.json();
            dados = {
                ...dados,
                ...recebidos
            };
        } catch (erro) {
            dados.body = event.data.text();
        }
    }

    const opcoes = {
        body: dados.body,
        icon: "/static/img/rofiteclaICON.png",
        badge: "/static/img/rofiteclaICON.png",
        data: {
            url: dados.url || "/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(
            dados.title || "Profisabores",
            opcoes
        )
    );
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();

    const destino = new URL(
        event.notification.data?.url || "/",
        self.location.origin
    );

    if (destino.origin !== self.location.origin) {
        return;
    }

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then(function (janelas) {
            for (const janela of janelas) {
                if (janela.url.startsWith(self.location.origin)) {
                    return janela.focus().then(function () {
                        return janela.navigate(destino.href);
                    });
                }
            }

            return clients.openWindow(destino.href);
        })
    );
});
