from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView,
)
from django.http import HttpRequest

from liceo.forms import FormularioRegistro


@login_required
def inicio(request: HttpRequest):
    return render(request, "inicio.html")


def login(request: HttpRequest):
    if not request.user.is_authenticated:
        return LoginView.as_view(
            template_name="auth/login.html",
        )(request)
    else:
        return redirect("/")


def registro(request: HttpRequest):
    if request.method == "POST":
        user_form = FormularioRegistro(request.POST)

        if user_form.is_valid():
            nuevo_usuario = user_form.save(commit=False)
            nuevo_usuario.set_password(user_form.cleaned_data["password"])
            nuevo_usuario.save()

            return render(request, "auth/registrado.html", {"new_user": nuevo_usuario})
    else:
        user_form = FormularioRegistro()
    return render(request, "auth/registro.html", {"form": user_form})


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
    )(request)


@login_required
def cambiar_contraseña(request: HttpRequest):
    return PasswordChangeView.as_view(
        template_name="auth/cambiar-contraseña.html",
    )(request)


@login_required
def contraseña_cambiada(request: HttpRequest):
    return PasswordChangeDoneView.as_view(
        template_name="auth/contraseña-cambiada.html",
    )(request)
