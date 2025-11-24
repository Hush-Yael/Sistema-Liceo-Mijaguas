from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)
from django.http import HttpRequest, HttpResponse

from usuarios.forms import FormularioPerfil


def login(request: HttpRequest):
    if not request.user.is_authenticated:
        return LoginView.as_view(
            template_name="login.html",
        )(request)
    else:
        return redirect("/")


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
    )(request)


@login_required
def perfil(request: HttpRequest):
    if request.method == "DELETE":
        try:
            request.user.foto_perfil.delete()  # type: ignore
            request.user.miniatura_foto.delete()  # type: ignore
            return render(request, "sin-fotos.html")
        except Exception as e:
            print("Error al eliminar la foto", e)
            return HttpResponse("Error al eliminar la foto", status=204)
    else:
        # se guarda, para evitar que se muestre uno cambiado, a pesar de fallar la validación
        usuario = request.user.username

        if request.method == "POST":
            form = FormularioPerfil(request.POST, request.FILES, instance=request.user)  # type: ignore

            if form.is_valid():
                form.save()
                # se asegura de que se actualice el nombre de usuario
                usuario = request.user.username
        else:
            form = FormularioPerfil(instance=request.user)  # type: ignore

        return render(
            request,
            "perfil.html",
            {"form": form, "usuario": usuario},
        )
