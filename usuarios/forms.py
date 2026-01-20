from django import forms
from .models import Grupo, Usuario


tamaño_minimo = 350


def validarTamaño(foto: forms.ImageField):
    if foto.size > 5242880:  # type: ignore
        raise forms.ValidationError("El archivo es demasiado grande.")

    alto = foto.image.height  # type: ignore
    ancho = foto.image.width  # type: ignore

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
        model = Usuario
        fields = ["username", "email", "foto_perfil"]

    email = forms.EmailField(required=False, label="Correo")
    foto_perfil = forms.ImageField(
        required=False, widget=forms.FileInput(), validators=[validarTamaño]
    )


class FormGrupo(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["permissions"].label = "Permisos asignados"

    class Meta:
        model = Grupo
        fields = "__all__"

        widgets = {
            "descripcion": forms.Textarea(),
        }
