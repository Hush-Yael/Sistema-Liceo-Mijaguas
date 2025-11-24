from django import forms
from .models import User


tamaño_minimo = 350


def validarTamaño(foto: forms.ImageField):
    if foto.size > 5242880:  # type: ignore
        raise forms.ValidationError("El archivo es demasiado grande.")

    alto = foto.image.height
    ancho = foto.image.width

    if alto < tamaño_minimo:
        raise forms.ValidationError(
            f"La imagen no cumple con la altura requerida ({tamaño_minimo}px)"
        )
    elif ancho < tamaño_minimo:
        raise forms.ValidationError(
            f"La imagen no cumple con el ancho requerido ({tamaño_minimo}px)"
        )

    return foto


class FormularioPerfil(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "foto_perfil"]

    email = forms.EmailField(required=False, label="Correo")
    foto_perfil = forms.ImageField(
        required=False, widget=forms.FileInput(), validators=[validarTamaño]
    )
