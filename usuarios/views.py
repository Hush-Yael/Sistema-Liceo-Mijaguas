from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from django.http import HttpRequest, HttpResponse
from django.utils.html import json

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
            return HttpResponse("Error al eliminar la foto", status=204)  # type: ignore
    else:
        form = FormularioPerfil(instance=request.user)  # type: ignore
        # se guardan los datos iniciales, para evitar que usar los que se intentaron cambiar al fallar la validación
        datos_iniciales = json.dumps(
            {
                **form.initial,
                "foto_perfil": request.user.foto_perfil.url,  # type: ignore
            }
        )

        if request.method == "POST":
            form = FormularioPerfil(request.POST, request.FILES, instance=request.user)  # type: ignore

            if form.is_valid():
                form.save()

        return render(
            request,
            "perfil.html",
            {
                "form": form,
                "datos_iniciales": datos_iniciales,
            },
        )


@login_required
def cambiar_contraseña(request: HttpRequest):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # actualizar la sesión
            update_session_auth_hash(request, user)
            return redirect("perfil")
    else:
        form = PasswordChangeForm(request.user)

    return PasswordChangeView.as_view(
        template_name="cambiar-contraseña.html",
    )(request)
