from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm


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
