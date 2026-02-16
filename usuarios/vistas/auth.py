from django.http import HttpRequest
from django.urls import reverse_lazy
from app.vistas.auth import VistaParaNoLogueadosMixin
from usuarios.forms.auth import (
    RegistroForm,
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
from django.views.generic import CreateView
from django.contrib.messages.views import SuccessMessageMixin


class Login(VistaParaNoLogueadosMixin, LoginView):
    template_name = "auth/login.html"


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
    )(request)


class Registro(VistaParaNoLogueadosMixin, SuccessMessageMixin, CreateView):
    form_class = RegistroForm
    template_name = "auth/registro.html"
    success_url = reverse_lazy("inicio")
    success_message = "Registrado correctamente, ahora puedes iniciar sesión"


class RecuperarContraseña(VistaParaNoLogueadosMixin, PasswordResetView):
    template_name = "auth/recuperar-contraseña.html"
    form_class = RecuperarContraseñaForm
    success_url = reverse_lazy("correo_recuperacion_enviado")


class CorreoRecuperacionEnviado(VistaParaNoLogueadosMixin, PasswordResetDoneView):
    template_name = "auth/correo-recuperacion-enviado.html"


class RestablecerContraseña(VistaParaNoLogueadosMixin, PasswordResetConfirmView):
    template_name = "auth/restablecer-contraseña.html"

    def render_to_response(self, context, **response_kwargs):
        r = super().render_to_response(context, **response_kwargs)

        if not context["validlink"]:
            r.template_name = "auth/enlace-invalido.html"  # type: ignore

        return r


class ContraseñaRestablecida(VistaParaNoLogueadosMixin, PasswordResetCompleteView):
    template_name = "auth/contraseña-restablecida.html"
