from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def login_funcionarios(request):

    if request.user.is_authenticated:
        if request.user.groups.filter(name="Secretaria").exists():
            return redirect("/secretaria/")

        if request.user.groups.filter(name="Cozinha").exists():
            return redirect("/cozinha/")

        if request.user.is_superuser:
            return redirect("/admin/")

    erro = None

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        utilizador = authenticate(
            request,
            username=username,
            password=password
        )

        if utilizador is not None:

            if (
                utilizador.is_superuser
                or utilizador.groups.filter(
                    name__in=["Secretaria", "Cozinha"]
                ).exists()
            ):
                login(request, utilizador)

                if utilizador.is_superuser:
                    return redirect("/admin/")

                if utilizador.groups.filter(
                    name="Secretaria"
                ).exists():
                    return redirect("/secretaria/")

                if utilizador.groups.filter(
                    name="Cozinha"
                ).exists():
                    return redirect("/cozinha/")

            else:
                erro = "Esta conta não tem acesso às áreas de funcionários."

        else:
            erro = "Utilizador ou palavra-passe incorretos."

    return render(
        request,
        "funcionarios/login.html",
        {"erro": erro}
    )


def logout_funcionarios(request):
    logout(request)
    return redirect("/funcionarios/login/")