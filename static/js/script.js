
document.addEventListener("DOMContentLoaded", () => {

    // ==========================================
    // ERROS JAVASCRIPT
    // ==========================================

    window.addEventListener("error", (event) => {
        console.error(
            "🔥 ERRO JS:",
            event.message,
            "arquivo:",
            event.filename,
            "linha:",
            event.lineno,
            "coluna:",
            event.colno
        );
    });

    window.addEventListener("unhandledrejection", (event) => {
        console.error(
            "🔥 PROMISE ERROR:",
            event.reason
        );
    });


    // ==========================================
    // ELEMENTOS DO MODAL DE RESERVA
    // ==========================================

    const modal = document.getElementById("reservaModal");
    const fecharModal = document.getElementById("fecharModal");
    const form = document.getElementById("reservaForm");

    const nomeReserva = document.getElementById("nomeReserva");
    const telemovelReserva = document.getElementById("telemovelReserva");
    const dadosVisitante = document.getElementById("dadosVisitante");


    // Seletor internacional de telemóvel para reservas de visitantes.
    let seletorTelemovel = null;

    if (
        telemovelReserva &&
        typeof window.intlTelInput === "function"
    ) {
        seletorTelemovel = window.intlTelInput(
            telemovelReserva,
            {
                initialCountry: "pt",
                separateDialCode: true,
                nationalMode: true,
                onlyCountries: [
                    "al", "de", "ad", "am", "at", "az",
                    "be", "by", "ba", "bg", "cz", "cy",
                    "hr", "dk", "sk", "si", "es", "ee",
                    "fi", "fr", "ge", "gr", "hu", "ie",
                    "is", "it", "lv", "li", "lt", "lu",
                    "mk", "mt", "md", "mc", "me", "no",
                    "nl", "pl", "pt", "gb", "ro", "ru",
                    "sm", "rs", "se", "ch", "tr", "ua",
                    "va", "xk"
                ],

                loadUtils: () =>
                    import(
                        "https://cdn.jsdelivr.net/npm/intl-tel-input@25.10.1/build/js/utils.js"
                    )
            }
        );
    }


    const pratoInput = document.getElementById("prato");
    const precoReserva = document.getElementById("precoReserva");
    const totalElement = document.getElementById("total");
    const mensagem = document.getElementById("mensagem");
    const dataPrato = document.getElementById("dataPrato");
    const alergiasInput = document.getElementById("alergias");

    const modalEntrada = document.getElementById("modalEntrada");
    const modalPratoPrincipal = document.getElementById("modalPratoPrincipal");
    const extrasLista = document.getElementById("extrasLista");

    let precoAtual = 0;
    let tipoItemAtual = "";
    let nomeItemAtual = "";
    let idItemAtual = null;
    let extrasSelecionados = [];

    // Controlar o modal e o scroll da página de fundo.
    const alternarModalReserva = (aberto) => {
        if (!modal) return;

        modal.classList.toggle("mostrar", aberto);
        document.body.classList.toggle("modal-reserva-aberto", aberto);
    };


    // ==========================================
    // ABRIR MODAL DE RESERVA
    // ==========================================

    document.querySelectorAll(".reserva-link").forEach((botao) => {

        botao.addEventListener("click", (event) => {

            event.preventDefault();

            const ementaId = botao.dataset.ementaId || "";
            const nomeEmenta = botao.dataset.prato || "";
            const data = botao.dataset.data || "";

            if (!ementaId) {
                console.error("O botão não contém data-ementa-id.");
                mostrarErro("Não foi possível identificar a ementa.");
                return;
            }

            tipoItemAtual = "ementa";
            nomeItemAtual = nomeEmenta;
            idItemAtual = ementaId;

            // Obter o preço-base apresentado no cartão.
            const cartao = botao.closest(".ementa-card");

            const elementoPreco = cartao
                ? cartao.querySelector(".ementa-preco")
                : null;

            let precoTexto = botao.dataset.preco || "";

            if (!precoTexto && elementoPreco) {
                precoTexto = elementoPreco.textContent;
            }

            const preco = parseFloat(
                String(precoTexto)
                    .replace(/[^\d,.-]/g, "")
                    .replace(/\.(?=.*\.)/g, "")
                    .replace(",", ".")
            );

            precoAtual = Number.isFinite(preco) ? preco : 0;

            if (modalEntrada) {
                modalEntrada.textContent = botao.dataset.entrada || "—";
            }

            if (modalPratoPrincipal) {
                modalPratoPrincipal.textContent =
                    botao.dataset.pratoPrincipal || "—";
            }

            // Ler os extras disponíveis para esta ementa.
            let extrasDaEmenta = [];

            try {
                extrasDaEmenta = JSON.parse(
                    botao.dataset.extras || "[]"
                );

                if (!Array.isArray(extrasDaEmenta)) {
                    extrasDaEmenta = [];
                }

            } catch (erro) {
                console.error(
                    "Não foi possível ler os extras da ementa.",
                    erro
                );
            }

            // Recuperar os extras selecionados no cartão.
            const cartaoAtual = botao.closest(".ementa-card");

            const extrasMarcadosNoCartao = new Set(
                cartaoAtual
                    ? [
                        ...cartaoAtual.querySelectorAll(
                            ".extra-checkbox-card:checked"
                        )
                    ].map((checkbox) => String(checkbox.dataset.extraId))
                    : []
            );

            renderizarExtras(
                extrasDaEmenta,
                ementaId,
                extrasMarcadosNoCartao
            );

            extrasSelecionados = [];

            // ==========================================
            // IDENTIFICAR O TIPO DE UTILIZADOR
            // ==========================================

            const autenticado =
                form?.dataset.autenticado === "true";

            // Mostrar os campos pessoais apenas a visitantes.
            if (dadosVisitante) {
                dadosVisitante.style.display =
                    autenticado ? "none" : "block";
            }

            if (nomeReserva) {
                nomeReserva.required = !autenticado;

                if (autenticado) {
                    nomeReserva.value = "";
                }
            }

            if (telemovelReserva) {
                telemovelReserva.required = !autenticado;

                if (autenticado) {
                    telemovelReserva.value = "";
                }
            }

            // Preencher os dados da ementa.
            if (pratoInput) {
                pratoInput.value = nomeItemAtual;
            }

            if (dataPrato) {
                dataPrato.value = data;
            }

            if (precoReserva) {
                precoReserva.textContent =
                    `€ ${precoAtual.toFixed(2).replace(".", ",")}`;
            }

            if (alergiasInput) {
                alergiasInput.value = "";
            }

            limparMensagem();
            atualizarTotal();

            if (modal) {
                alternarModalReserva(true);
            }
        });
    });


    // ==========================================
    // FECHAR MODAL DE RESERVA
    // ==========================================

    if (fecharModal) {
        fecharModal.addEventListener("click", () => {
            if (modal) {
                alternarModalReserva(false);
            }
        });
    }

    if (modal) {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                alternarModalReserva(false);
            }
        });
    }


    // ==========================================
    // RENDERIZAR EXTRAS
    // ==========================================

    function renderizarExtras(
        extras,
        ementaId,
        extrasMarcados = new Set()
    ) {
        if (!extrasLista) return;

        extrasLista.replaceChildren();

        if (!extras.length) {
            const aviso = document.createElement("p");

            aviso.textContent =
                "Não existem extras disponíveis para esta ementa.";

            extrasLista.appendChild(aviso);
            return;
        }

        extras.forEach((extra) => {

            const label = document.createElement("label");
            label.className = "extra-item";

            const checkbox = document.createElement("input");

            checkbox.type = "checkbox";
            checkbox.className = "extra-checkbox";
            checkbox.name = "extras";
            checkbox.value = String(extra.id);
            checkbox.dataset.ementaId = String(ementaId);
            checkbox.dataset.preco = String(extra.preco ?? "0");
            checkbox.checked = extrasMarcados.has(String(extra.id));

            const conteudo = document.createElement("span");
            conteudo.className = "extra-conteudo";

            const nome = document.createElement("strong");

            nome.textContent = extra.tipo
                ? `${extra.tipo}: ${extra.nome}`
                : String(extra.nome || "Extra");

            conteudo.appendChild(nome);

            if (extra.descricao) {
                const descricao = document.createElement("small");
                descricao.textContent = extra.descricao;
                conteudo.appendChild(descricao);
            }

            if (extra.alergenios) {
                const alergenios = document.createElement("small");

                alergenios.className = "ementa-alergenios";
                alergenios.textContent =
                    `Alergénios: ${extra.alergenios}`;

                conteudo.appendChild(alergenios);
            }

            const preco = Number.parseFloat(
                String(extra.preco ?? "0").replace(",", ".")
            );

            const precoTexto = document.createElement("span");

            precoTexto.className = "extra-preco";
            precoTexto.textContent =
                `+${(
                    Number.isFinite(preco) ? preco : 0
                ).toFixed(2).replace(".", ",")} €`;

            label.append(checkbox, conteudo, precoTexto);
            extrasLista.appendChild(label);
        });
    }


    // ==========================================
    // ATUALIZAR TOTAL
    // ==========================================

    function atualizarTotal() {
        if (!totalElement) return;

        const checkboxes = extrasLista
            ? [
                ...extrasLista.querySelectorAll(
                    ".extra-checkbox:checked"
                )
            ]
            : [];

        extrasSelecionados = checkboxes.map((checkbox) => {

            const valor = Number.parseFloat(
                String(checkbox.dataset.preco || "0").replace(",", ".")
            );

            return {
                id: checkbox.value,
                preco: Number.isFinite(valor) ? valor : 0
            };
        });

        const totalExtras = extrasSelecionados.reduce(
            (soma, extra) => soma + extra.preco,
            0
        );

        totalElement.textContent =
            `€ ${(precoAtual + totalExtras).toFixed(2).replace(".", ",")}`;
    }


    // ==========================================
    // LIMPAR MENSAGEM
    // ==========================================

    function limparMensagem() {
        if (!mensagem) return;

        mensagem.textContent = "";
        mensagem.className = "";
    }


    // ==========================================
    // MOSTRAR ERRO
    // ==========================================

    function mostrarErro(texto) {
        if (!mensagem) return;

        mensagem.textContent = texto;
        mensagem.className = "erro";
    }


 
    // ==========================================
    // CRIAR RESERVA — PROTEÇÃO CONTRA DUPLICADOS
    // ==========================================

    if (form) {

        let aEnviarReserva = false;

        const botaoEnviar = form.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

        const estadoOriginalBotao = botaoEnviar
            ? botaoEnviar.disabled
            : false;

        form.addEventListener("submit", async (event) => {

            event.preventDefault();

            // Impedir submissões repetidas.
            if (aEnviarReserva) {
                console.warn(
                    "Envio ignorado: já existe uma reserva em processamento."
                );
                return;
            }

            limparMensagem();

            // ----------------------------------
            // VERIFICAR ITEM
            // ----------------------------------

            if (!idItemAtual) {
                mostrarErro(
                    "Não foi possível identificar o item escolhido."
                );
                return;
            }

            // ----------------------------------
            // VERIFICAR DATA
            // ----------------------------------

            const dataInput = form.querySelector('[name="data"]');

            if (!dataInput || !dataInput.value) {
                mostrarErro("A data da reserva é obrigatória.");
                return;
            }

            // ----------------------------------
            // PREPARAR FORM DATA
            // ----------------------------------

            const dados = new FormData();

            // ----------------------------------
            // DADOS DO UTILIZADOR
            // ----------------------------------

            const autenticado =
                form.dataset.autenticado === "true";

            if (!autenticado) {

                const nome = nomeReserva?.value.trim() || "";
                const telemovel =
                    telemovelReserva?.value.trim() || "";

                if (!nome || !telemovel) {
                    mostrarErro(
                        "Preenche o teu nome completo e o telemóvel."
                    );
                    return;
                }

                                // Validar o nome: letras, acentos, espaços,
                // hífen e apóstrofos.
                const nomeValido =
                    /^[\p{L}]+(?:[ '\u2019-][\p{L}]+)*$/u.test(nome);

                if (!nomeValido) {
                    mostrarErro(
                        "O nome só pode conter letras, espaços, hífen ou apóstrofo."
                    );
                    return;
                }

                // Validar o número internacional selecionado.
                if (!seletorTelemovel) {
                    mostrarErro(
                        "O seletor de país não foi carregado. "
                        + "Atualiza a página e tenta novamente."
                    );
                    return;
                }

                try {
                    if (seletorTelemovel.promise) {
                        await seletorTelemovel.promise;
                    }
                } catch (erro) {
                    console.error(
                        "Erro ao carregar a validação telefónica:",
                        erro
                    );
                    mostrarErro(
                        "Não foi possível validar o telemóvel. "
                        + "Verifica a ligação à Internet."
                    );
                    return;
                }

                if (!seletorTelemovel.isValidNumber()) {
                    mostrarErro(
                        "Introduz um número de telemóvel válido "
                        + "para o país selecionado."
                    );
                    return;
                }

                const telemovelInternacional =
                    seletorTelemovel.getNumber();

                if (
                    !/^\+[1-9]\d{6,14}$/.test(
                        telemovelInternacional
                    )
                ) {
                    mostrarErro(
                        "O número de telemóvel internacional é inválido."
                    );
                    return;
                }

                if (
                    nome.length > 100 ||
                    telemovelInternacional.length > 20
                ) {
                    mostrarErro(
                        "O nome ou o telemóvel excede o tamanho permitido."
                    );
                    return;
                }

                dados.append("nome", nome);
                dados.append("telemovel", telemovelInternacional);
            }

            // ----------------------------------
            // EMENTA E EXTRAS
            // ----------------------------------

            dados.append("ementa_id", idItemAtual);

            extrasSelecionados.forEach((extra) => {
                dados.append("extras", extra.id);
            });

            // ----------------------------------
            // DATA
            // ----------------------------------

            dados.append("data", dataInput.value);

            // ----------------------------------
            // ALERGIAS
            // ----------------------------------

            dados.append(
                "alergias",
                alergiasInput
                    ? alergiasInput.value.trim()
                    : ""
            );

            // ----------------------------------
            // BLOQUEAR NOVOS ENVIOS
            // ----------------------------------

            aEnviarReserva = true;

            if(botaoEnviar) {
                botaoEnviar.disabled = true;
                botaoEnviar.classList.add("carregando");
                botaoEnviar.setAttribute("aria-busy", "true");
            }

            let reservaCriada = false;

            // ----------------------------------
            // ENVIAR PARA DJANGO
            // ----------------------------------

            try {

                const resposta = await fetch(
                    "/reservas/criar/",
                    {
                        method: "POST",
                        body: dados
                    }
                );

                // ----------------------------------
                // LER RESPOSTA
                // ----------------------------------

                let resultado;

                try {
                    resultado = await resposta.json();

                } catch (erroJSON) {

                    console.error(
                        "O servidor devolveu uma resposta inválida.",
                        erroJSON
                    );

                    mostrarErro(
                        "O servidor devolveu uma resposta inválida."
                    );

                    return;
                }

                // ----------------------------------
                // ERRO DO SERVIDOR
                // ----------------------------------

                if (!resposta.ok) {

                    if (resposta.status === 401) {

                        if (autenticado) {

                            window.location.href =
                                "/utilizadores/login/";

                        } else {

                            mostrarErro(
                                resultado.erro ||
                                "Não foi possível autorizar a reserva do visitante."
                            );
                        }

                        return;
                    }

                    mostrarErro(
                        resultado.erro ||
                        "Ocorreu um erro ao criar a reserva."
                    );

                    return;
                }

                // ----------------------------------
                // SUCESSO
                // ----------------------------------

                reservaCriada = true;

                if (mensagem) {
                    mensagem.textContent =
                        "Reserva realizada com sucesso!";

                    mensagem.className = "sucesso";
                }

                // ----------------------------------
                // REDIRECIONAR
                // ----------------------------------

                setTimeout(() => {

                    if (modal) {
                        alternarModalReserva(false);
                    }

                    form.reset();
                    limparMensagem();

                    window.location.href = "/reservas/";

                }, 1000);

            } catch (erro) {

                console.error(
                    "Erro ao criar reserva:",
                    erro
                );

                mostrarErro(
                    "Não foi possível contactar o servidor. " +
                    "Verifica se a reserva foi criada antes de tentar novamente."
                );
            } finally {

                // Em caso de falha, permitir nova tentativa.
                // Em caso de sucesso, manter o bloqueio
                // até ao redirecionamento.
                if (!reservaCriada) {
                    aEnviarReserva = false;

                    if (botaoEnviar) {
                        botaoEnviar.disabled = estadoOriginalBotao;
                        botaoEnviar.classList.remove("carregando");
                        botaoEnviar.removeAttribute("aria-busy");
                    }
                }
            }
        });
    }


    // ==========================================
    // CANCELAR RESERVA
    // ==========================================

    const botoesCancelar =
        document.querySelectorAll(".cancelar-btn");

    botoesCancelar.forEach((botao) => {

        botao.addEventListener("click", async () => {

            const reservaId = botao.dataset.reservaId;

            if (!reservaId) {
                alert("ID da reserva não encontrado.");
                return;
            }

            const confirmar = confirm(
                "Tens a certeza que queres cancelar esta reserva?"
            );

            if (!confirmar) return;

            try {

                const resposta = await fetch(
                    `/reservas/cancelar/${reservaId}/`,
                    {
                        method: "POST"
                    }
                );

                const resultado = await resposta.json();

                // ----------------------------------
                // ERRO
                // ----------------------------------

                if (!resposta.ok) {

                    if (resposta.status === 401) {
                        window.location.href =
                            "/utilizadores/login/";

                        return;
                    }

                    alert(
                        resultado.erro ||
                        "Não foi possível cancelar a reserva."
                    );

                    return;
                }

                // ----------------------------------
                // REMOVER CARTÃO
                // ----------------------------------

                const card = botao.closest(".reserva-card");

                if (card) {
                    card.remove();
                }

                // ----------------------------------
                // VERIFICAR SE A LISTA FICOU VAZIA
                // ----------------------------------

                const cardsRestantes =
                    document.querySelectorAll(".reserva-card");

                if (cardsRestantes.length === 0) {

                    const lista = document.querySelector(".pagina");

                    if (lista) {

                        const mensagemVazia =
                            document.createElement("div");

                        mensagemVazia.className = "infocard";

                        mensagemVazia.innerHTML = `
                            <span class="info-icon">
                                🍽️
                            </span>

                            <div>
                                <strong>
                                    Ainda não tens reservas
                                </strong>

                                <p>
                                    Escolhe uma ementa no menu e faz a tua primeira reserva.
                                </p>
                            </div>
                        `;

                        const novaReserva =
                            document.querySelector(".nova-reserva-btn");

                        if (novaReserva) {
                            lista.insertBefore(
                                mensagemVazia,
                                novaReserva
                            );
                        } else {
                            lista.appendChild(mensagemVazia);
                        }
                    }
                }

            } catch (erro) {

                console.error("Erro ao cancelar:", erro);

                alert(
                    "Não foi possível contactar o servidor."
                );
            }
        });
    });


    // ==========================================
    // AMPLIAR IMAGENS
    // ==========================================

    const imagemModal =
        document.getElementById("imagemModal");

    const imagemAmpliada =
        document.getElementById("imagemAmpliada");

    const fecharImagem =
        document.getElementById("fecharImagem");

    document.querySelectorAll(
        ".imgcomida img, " +
        ".sobremesa-imagem img, " +
        ".menu-card-imagem img"
    ).forEach((imagem) => {

        imagem.addEventListener("click", (event) => {

            event.stopPropagation();

            if (!imagemModal || !imagemAmpliada) {
                return;
            }

            imagemAmpliada.src = imagem.src;
            imagemAmpliada.alt = imagem.alt;

            imagemModal.classList.add("ativo");
        });
    });


    // ==========================================
    // ATUALIZAR TOTAL AO ALTERAR EXTRAS
    // ==========================================

    if (extrasLista) {

        extrasLista.addEventListener("change", (event) => {

            if (!event.target.matches(".extra-checkbox")) {
                return;
            }

            const checkboxModal = event.target;
            const extraId = String(checkboxModal.value);
            const ementaId = String(
                checkboxModal.dataset.ementaId
            );

            const botaoReserva = [
                ...document.querySelectorAll(".reserva-link")
            ].find((botao) =>
                String(botao.dataset.ementaId) === ementaId
            );

            const cartao = botaoReserva
                ? botaoReserva.closest(".ementa-card")
                : null;

            const checkboxCartao = cartao
                ? [
                    ...cartao.querySelectorAll(".extra-checkbox-card")
                ].find((checkbox) =>
                    String(checkbox.dataset.extraId) === extraId
                )
                : null;

            if (checkboxCartao) {
                checkboxCartao.checked = checkboxModal.checked;
            }

            atualizarTotal();
        });
    }


    // ==========================================
    // FECHAR MODAL DE IMAGEM
    // ==========================================

    function fecharModalImagem() {

        if (!imagemModal) return;

        imagemModal.classList.remove("ativo");

        if (imagemAmpliada) {
            imagemAmpliada.src = "";
        }
    }

    if (fecharImagem) {
        fecharImagem.addEventListener(
            "click",
            fecharModalImagem
        );
    }

    if (imagemModal) {

        imagemModal.addEventListener("click", (event) => {

            if (event.target === imagemModal) {
                fecharModalImagem();
            }
        });
    }


    // ==========================================
    // ESC FECHA IMAGEM
    // ==========================================

    document.addEventListener("keydown", (event) => {

        if (event.key === "Escape") {
            fecharModalImagem();
        }
    });


    // ==========================================
    // CARROSSÉIS
    // ==========================================

    function iniciarCarrossel(id) {
        const carousel = document.getElementById(id);
        if (!carousel) return;

        const slides = carousel.querySelectorAll(".banner-slide");
        const dots = carousel.querySelectorAll(".banner-dot");

        if (slides.length === 0) return;

        let indiceAtual = 0;
        let inicioX = 0;
        let inicioY = 0;
        let gestoHorizontal = false;

        function mostrarSlide(index) {
            indiceAtual = (index + slides.length) % slides.length;

            slides.forEach((slide, i) => {
                slide.classList.toggle("ativo", i === indiceAtual);
            });

            dots.forEach((dot, i) => {
                dot.classList.toggle("ativo", i === indiceAtual);
            });
        }

        dots.forEach((dot, index) => {
            dot.addEventListener("click", () => {
                mostrarSlide(index);
            });
        });

        carousel.addEventListener("touchstart", (event) => {
            if (event.touches.length !== 1) return;

            inicioX = event.touches[0].clientX;
            inicioY = event.touches[0].clientY;
            gestoHorizontal = false;
        }, { passive: true });

        carousel.addEventListener("touchmove", (event) => {
            if (event.touches.length !== 1) return;

            const diferencaX = event.touches[0].clientX - inicioX;
            const diferencaY = event.touches[0].clientY - inicioY;

            if (Math.abs(diferencaX) > 12 &&
                Math.abs(diferencaX) > Math.abs(diferencaY)) {
                gestoHorizontal = true;
            }
        }, { passive: true });

        carousel.addEventListener("touchend", (event) => {
            if (!gestoHorizontal || !event.changedTouches.length) return;

            const diferencaX = event.changedTouches[0].clientX - inicioX;

            if (Math.abs(diferencaX) >= 45) {
                if (diferencaX < 0) {
                    mostrarSlide(indiceAtual + 1);
                } else {
                    mostrarSlide(indiceAtual - 1);
                }
            }

            gestoHorizontal = false;
        }, { passive: true });

        mostrarSlide(0);
    }


    // ==========================================
    // INICIAR CARROSSÉIS
    // ==========================================

    iniciarCarrossel("bannerTopo");
    iniciarCarrossel("bannerFim");


    // ==========================================
    // LOADING DE NAVEGAÇÃO — PROFISABORES
    // ==========================================

    const loadingScreen =
        document.getElementById("loading-screen");

    const botoesNavegacao =
        document.querySelectorAll(".bottom-nav .nav-btn");

    if (loadingScreen) {

        botoesNavegacao.forEach((botao) => {

            botao.addEventListener("click", (event) => {

                // Se já estamos nesta página, não mostrar loading.
                if (botao.classList.contains("active")) {
                    return;
                }

                event.preventDefault();

                const destino = botao.getAttribute("href");

                if (!destino) return;

                loadingScreen.classList.add("loading-active");

                setTimeout(() => {
                    window.location.href = destino;
                }, 1500);
            });
        });
    }
});
