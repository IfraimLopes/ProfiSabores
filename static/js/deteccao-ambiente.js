(function () {
    "use strict";

    var ua = navigator.userAgent || "";
    var plataforma = "desktop";
    var navegador = "outro";
    var standalone = false;
    var tipoExecucao = "navegador";

    var capacitor = window.Capacitor;

    if (capacitor) {
        try {
            if (
                typeof capacitor.isNativePlatform === "function" &&
                capacitor.isNativePlatform()
            ) {
                tipoExecucao = "capacitor";
            }
        } catch (_) {}

        try {
            if (typeof capacitor.getPlatform === "function") {
                var p = capacitor.getPlatform();
                if (p === "ios" || p === "android") {
                    plataforma = p;
                }
            }
        } catch (_) {}
    }

    var ios = /iPhone|iPad|iPod/i.test(ua) ||
        (navigator.platform === "MacIntel" &&
         navigator.maxTouchPoints > 1);

    var android = /Android/i.test(ua);

    if (plataforma === "desktop") {
        if (ios) plataforma = "ios";
        else if (android) plataforma = "android";
    }

    standalone =
        window.matchMedia("(display-mode: standalone)").matches ||
        window.matchMedia("(display-mode: fullscreen)").matches ||
        navigator.standalone === true;

    if (tipoExecucao !== "capacitor" && standalone) {
        tipoExecucao = "pwa";
    }

    if (/Edg\//i.test(ua)) {
        navegador = "edge";
    } else if (/CriOS\//i.test(ua)) {
        navegador = "chrome";
    } else if (/FxiOS\//i.test(ua) || /Firefox\//i.test(ua)) {
        navegador = "firefox";
    } else if (/OPR\//i.test(ua)) {
        navegador = "opera";
    } else if (/Chrome\//i.test(ua) && !/Edg\//i.test(ua)) {
        navegador = "chrome";
    } else if (/Safari\//i.test(ua)) {
        navegador = "safari";
    }

    window.ProfisaboresAmbiente = {
        plataforma: plataforma,
        navegador: navegador,
        tipoExecucao: tipoExecucao,
        standalone: standalone
    };
})();
