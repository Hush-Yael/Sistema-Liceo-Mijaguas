from django import forms
from .models import User


def validarTamaño(foto: forms.ImageField):
    if foto.size > 5242880:  # type: ignore
        raise forms.ValidationError("El archivo es demasiado grande.")
    return foto


class FormularioPerfil(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "foto_perfil"]

    email = forms.EmailField(required=False, label="Correo")
    foto_perfil = forms.ImageField(
        required=False, widget=forms.FileInput(), validators=[validarTamaño]
    )
