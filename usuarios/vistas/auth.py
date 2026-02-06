from django.http import HttpRequest
from django.urls import reverse_lazy
from app.vistas import VistaParaNoLogueados
from usuarios.forms.auth import (
    CambiarContraseñaForm,
    RecuperarContraseñaForm,
)
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


class Login(VistaParaNoLogueados, LoginView):
    template_name = "auth/login.html"


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
    )(request)


@login_required
def cambiar_contraseña(request: HttpRequest):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)  # type: ignore
        if form.is_valid():
            user = form.save()
            # actualizar la sesión
            update_session_auth_hash(request, user)
            return redirect("perfil")
    else:
        form = PasswordChangeForm(request.user)  # type: ignore

    return PasswordChangeView.as_view(
        form_class=CambiarContraseñaForm,
        template_name="auth/cambiar-contraseña.html",
    )(request)


class RecuperarContraseña(VistaParaNoLogueados, PasswordResetView):
    template_name = "auth/recuperar-contraseña.html"
    form_class = RecuperarContraseñaForm
    success_url = reverse_lazy("correo_recuperacion_enviado")


class CorreoRecuperacionEnviado(VistaParaNoLogueados, PasswordResetDoneView):
    template_name = "auth/correo-recuperacion-enviado.html"


class RestablecerContraseña(VistaParaNoLogueados, PasswordResetConfirmView):
    template_name = "auth/restablecer-contraseña.html"

    def render_to_response(self, context, **response_kwargs):
        r = super().render_to_response(context, **response_kwargs)

        if not context["validlink"]:
            r.template_name = "auth/enlace-invalido.html"  # type: ignore

        return r


class ContraseñaRestablecida(VistaParaNoLogueados, PasswordResetCompleteView):
    template_name = "auth/contraseña-restablecida.html"
