from django.shortcuts import render


def erro_404(request, exception):
    return render(request, "404.html", status=404)
