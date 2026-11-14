from django.shortcuts import render


def erro_404(request, exception):
    return render(request, "404.html", status=404)


def politica_privacidade(request):
    return render(request, "politica_privacidade.html")


def termos_servico(request):
    return render(request, "termos_servico.html")
