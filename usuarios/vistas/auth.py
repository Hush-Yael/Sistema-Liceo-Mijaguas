from django.http import HttpRequest
from django.urls import reverse_lazy
from app.vistas import VistaParaNoLogueados
from usuarios.forms.auth import (
    RecuperarContraseñaForm,
)
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)


class Login(VistaParaNoLogueados, LoginView):
    template_name = "auth/login.html"


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
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
