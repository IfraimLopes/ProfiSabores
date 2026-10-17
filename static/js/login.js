document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("loginForm");
    const mensagem = document.getElementById("mensagem");

    if (!form) {
        console.error("Formulário de login não encontrado.");
        return;
    }

    form.addEventListener("submit", async (event) => {

        event.preventDefault();

        mensagem.textContent = "";

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        if (!email || !password) {
            mensagem.textContent = "Preencha o e-mail e a palavra-passe.";
            return;
        }

        const dados = new FormData();

        dados.append("email", email);
        dados.append("password", password);

        try {

            const resposta = await fetch(
                "/utilizadores/api/login/",
                {
                    method: "POST",
                    body: dados
                }
            );

            const resultado = await resposta.json();

            if (!resposta.ok) {
                mensagem.textContent =
                    resultado.erro || "Erro ao iniciar sessão.";
                return;
            }

            sessionStorage.setItem(
                "login_email",
                resultado.email
            );

            window.location.href =
                "/utilizadores/verificar-login/";

        } catch (erro) {

            console.error(erro);

            mensagem.textContent =
                "Não foi possível contactar o servidor.";
        }
    });

});