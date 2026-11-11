"use strict";

// ==========================================
// CACHE OFFLINE
// ==========================================

const CACHE_NAME = "profisabores-offline-v1";
const OFFLINE_URL = "/static/offline.html";

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll([
                OFFLINE_URL,
                "/static/css/erros.css",
                "/static/img/profisabores-icon.svg"
            ]);
        }).then(function () {
            return self.skipWaiting();
        })
    );
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys().then(function (nomes) {
            return Promise.all(
                nomes
                    .filter(function (nome) {
                        return nome.startsWith("profisabores-offline-")
                            && nome !== CACHE_NAME;
                    })
                    .map(function (nome) {
                        return caches.delete(nome);
                    })
            );
        }).then(function () {
            return clients.claim();
        })
    );
});

// ==========================================
// NAVEGAÇÃO SEM LIGAÇÃO
// ==========================================

self.addEventListener("fetch", function (event) {
    if (event.request.mode !== "navigate") {
        return;
    }

    event.respondWith(
        fetch(event.request).catch(async function () {
            const paginaOffline = await caches.match(OFFLINE_URL);

            if (paginaOffline) {
                return paginaOffline;
            }

            return new Response(
                "Sem ligação ao Profisabores.",
                {
                    status: 503,
                    headers: {
                        "Content-Type": "text/plain; charset=utf-8"
                    }
                }
            );
        })
    );
});

// ==========================================
// NOTIFICAÇÕES PUSH
// ==========================================

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

// ==========================================
// CLIQUE NAS NOTIFICAÇÕES
// ==========================================

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
