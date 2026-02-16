from django import forms
from django.contrib.auth.forms import (
    PasswordChangeForm,
    PasswordResetForm,
)
from usuarios.forms import FormUsuarioFotoMixin
from usuarios.models import Usuario


class CambiarContraseñaForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["old_password"].label = "Contraseña actual"
        self.fields["new_password2"].label = "Confirmar nueva contraseña"


class RecuperarContraseñaForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].label = "Ingrese el correo de su usuario:"
        self.fields[
            "email"
        ].help_text = "Se le enviará un enlace para restablecer su contraseña"


class RegistroForm(FormUsuarioFotoMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("foto_perfil", "username", "email", "password")

    field_order = (
        "username",
        "password",
        "email",
    )

    email = forms.EmailField(
        required=False,
        label="Correo",
        help_text="Es importante que tenga un correo, para poder restablecer su contraseña en caso de olvido",
    )

    def save(self, commit=False):
        usuario: Usuario = super().save(commit)

        usuario.set_password(self.cleaned_data["password"])
        usuario.save()
        self.save_m2m()

        return usuario
