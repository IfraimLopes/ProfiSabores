"use strict";

(function () {
    const CHAVE_INSTALACAO = "profisabores_instalacao_confirmada_v2";
    const CHAVE_NOTIFICACOES = "profisabores_notificacoes_prompt_visto_v2";

    const CAMINHO_INICIO = "/inicio/";
    const CAMINHO_PERFIL = "/utilizadores/perfil/";

    let pedidoInstalacao = null;

    window.addEventListener("beforeinstallprompt", function (evento) {
        evento.preventDefault();
        pedidoInstalacao = evento;
    });

    const emStandalone =
        window.matchMedia("(display-mode: standalone)").matches ||
        window.navigator.standalone === true;

    const eApple =
        /iPhone|iPad|iPod/.test(navigator.userAgent) ||
        (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

    function criarModal(titulo, conteudo, botoes) {
        document.getElementById("profisabores-onboarding")?.remove();

        const fundo = document.createElement("div");
        fundo.id = "profisabores-onboarding";
        fundo.className = "prof-onboarding-fundo";
        fundo.innerHTML = `
            <section class="prof-onboarding-modal"
                     role="dialog"
                     aria-modal="true"
                     aria-labelledby="prof-onboarding-titulo">
                <div class="prof-onboarding-simbolo">P</div>
                <h2 id="prof-onboarding-titulo"></h2>
                <div class="prof-onboarding-conteudo"></div>
                <div class="prof-onboarding-botoes"></div>
                <p class="prof-onboarding-estado" aria-live="polite"></p>
            </section>
        `;

        fundo.querySelector("h2").textContent = titulo;
        fundo.querySelector(".prof-onboarding-conteudo").innerHTML = conteudo;

        const zonaBotoes = fundo.querySelector(".prof-onboarding-botoes");

        botoes.forEach(function (definicao) {
            const botao = document.createElement("button");
            botao.type = "button";
            botao.textContent = definicao.texto;
            botao.className = definicao.principal
                ? "prof-onboarding-botao principal"
                : "prof-onboarding-botao secundario";

            botao.addEventListener("click", async function () {
                botao.disabled = true;

                try {
                    await definicao.acao(
                        fundo.querySelector(".prof-onboarding-estado")
                    );
                } catch (erro) {
                    console.error("Profisabores onboarding:", erro);
                    fundo.querySelector(".prof-onboarding-estado").textContent =
                        "Ocorreu um erro. Tenta novamente.";
                } finally {
                    if (botao.isConnected) botao.disabled = false;
                }
            });

            zonaBotoes.appendChild(botao);
        });

        document.body.appendChild(fundo);
        return fundo;
    }

    function irParaPerfil() {
        window.location.href = CAMINHO_PERFIL + "?ativar_notificacoes=1";
    }

    function mostrarModalInstalacao() {
        let instrucoes;

        if (eApple) {
            instrucoes = `
                <p>Para teres o Profisabores no ecrã principal do iPhone ou iPad:</p>
                <ol>
                    <li>Abre este site no <strong>Safari</strong>.</li>
                    <li>Toca no botão <strong>Partilhar</strong>.</li>
                    <li>Escolhe <strong>Adicionar ao ecrã principal</strong>.</li>
                    <li>Confirma a operação e abre o ícone criado.</li>
                </ol>
                <p>Depois, regressa aqui e seleciona a opção para continuar.</p>
            `;
        } else {
            instrucoes = `
                <p>Adiciona o Profisabores ao ecrã principal para o abrires como uma aplicação.</p>
                <ol>
                    <li>Se aparecer a opção de instalação, seleciona-a.</li>
                    <li>Caso contrário, abre o menu do navegador.</li>
                    <li>Procura <strong>Instalar aplicação</strong> ou
                        <strong>Adicionar ao ecrã principal</strong>.</li>
                    <li>Confirma e, quando terminares, regressa aqui.</li>
                </ol>
            `;
        }

        const modal = criarModal(
            "Prepara o teu Profisabores",
            instrucoes,
            [
                {
                    texto: "Instalar o Profisabores",
                    principal: true,
                    acao: async function (estado) {
                        if (!pedidoInstalacao) {
                            estado.textContent = eApple
                                ? "Segue as instruções acima no Safari e depois seleciona «Já adicionei, continuar»."
                                : "Abre o menu do navegador e procura a opção de instalação. Depois regressa aqui.";
                            return;
                        }

                        const pedido = pedidoInstalacao;
                        pedidoInstalacao = null;

                        await pedido.prompt();
                        const resultado = await pedido.userChoice;

                        if (resultado && resultado.outcome === "accepted") {
                            localStorage.setItem(CHAVE_INSTALACAO, "1");
                            irParaPerfil();
                        } else {
                            estado.textContent =
                                "A instalação não foi concluída. Podes tentar novamente.";
                        }
                    }
                },
                {
                    texto: "Já adicionei, continuar",
                    principal: false,
                    acao: function () {
                        localStorage.setItem(CHAVE_INSTALACAO, "1");
                        irParaPerfil();
                    }
                }
            ]
        );

        // Em navegadores sem instalação direta, a primeira opção explica
        // como proceder; a confirmação continua a ser feita pelo utilizador.
        if (!pedidoInstalacao) {
            const botaoInstalar = modal.querySelector(
                ".prof-onboarding-botoes .prof-onboarding-botao"
            );

            if (botaoInstalar) {
                botaoInstalar.textContent = "Como instalar";
                botaoInstalar.addEventListener("click", function () {
                    const estado = modal.querySelector(".prof-onboarding-estado");
                    if (estado && !estado.textContent) {
                        estado.textContent = eApple
                            ? "No Safari: Partilhar → Adicionar ao ecrã principal."
                            : "No menu do navegador, procura «Instalar aplicação» ou «Adicionar ao ecrã principal».";
                    }
                });
            }
        }
    }

    function mostrarModalNotificacoes() {
        if (localStorage.getItem(CHAVE_NOTIFICACOES) === "1") return;

        criarModal(
            "Ativa as notificações",
            `
                <p>Recebe avisos importantes sobre as tuas reservas e os respetivos pagamentos.</p>
                <p>Seleciona <strong>Ativar notificações</strong> e autoriza o navegador quando te pedir permissão.</p>
                <p class="prof-onboarding-nota">A autorização depende das definições do teu dispositivo e navegador.</p>
            `,
            [
                {
                    texto: "Ativar notificações",
                    principal: true,
                    acao: async function (estado) {
                        if (typeof window.profIsaboresAtivarNotificacoes === "function") {
                            await window.profIsaboresAtivarNotificacoes();
                        } else {
                            const botao = document.getElementById("webPushButton");

                            if (botao) {
                                botao.click();
                            } else {
                                estado.textContent =
                                    "Não foi possível encontrar o controlo de notificações nesta página.";
                                return;
                            }
                        }

                        // O fecho automático acontece quando o Web Push confirma
                        // a subscrição. Se não for possível, o utilizador pode
                        // escolher continuar sem a ativação.
                    }
                },
                {
                    texto: "Continuar mais tarde",
                    principal: false,
                    acao: function () {
                        localStorage.setItem(CHAVE_NOTIFICACOES, "1");
                        document.getElementById("profisabores-onboarding")?.remove();
                    }
                }
            ]
        );
    }

    window.addEventListener("profisabores:notificacoes-ativadas", function () {
        localStorage.setItem(CHAVE_NOTIFICACOES, "1");
        document.getElementById("profisabores-onboarding")?.remove();
    });

    const caminho = window.location.pathname;

    // O tutorial de instalação foi desativado.
    // Mantemos a deteção da aplicação instalada e as notificações no perfil.
    if (caminho === CAMINHO_INICIO && emStandalone) {
        localStorage.setItem(CHAVE_INSTALACAO, "1");

        if (localStorage.getItem(CHAVE_NOTIFICACOES) !== "1") {
            irParaPerfil();
        }
    }

    if (caminho === CAMINHO_PERFIL) {
        mostrarModalNotificacoes();
    }
})();
