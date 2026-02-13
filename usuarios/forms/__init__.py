from typing import Any
from django import forms
from app.util import nc
from usuarios.models import Grupo, Usuario


tamaño_minimo = 350


class FormUsuarioFotoMixin(forms.Form):
    cleaned_data: "dict[str, Any]"

    foto_perfil = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": "image/*",
            }
        ),
    )

    foto_perfil_limpiar = forms.BooleanField(required=False)

    def clean_foto_perfil(self):
        foto: forms.FileField = self.cleaned_data[nc(Usuario.foto_perfil)]  # type: ignore - Sí se obtiene el nombre del campo

        if not hasattr(foto, "image") or not foto:
            return

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

    def save(self, commit: bool = True):
        # Se indicó eliminar la foto
        if self.cleaned_data.get(f"{nc(Usuario.foto_perfil)}_limpiar"):  # type: ignore - Sí se obtiene el nombre del campo
            usuario: Usuario = self.instance  # type: ignore - Sí se obtiene la instancia

            usuario.foto_perfil.delete(save=False)  # type: ignore
            usuario.miniatura_foto.delete(save=False)  # type: ignore

            setattr(usuario, "foto_perfil", None)  # type: ignore
            setattr(usuario, "miniatura_foto", None)  # type: ignore
            setattr(self, "foto_eliminada", True)
        # Se subió una foto, indicar actualizar
        elif self.cleaned_data.get(nc(Usuario.foto_perfil)):  # type: ignore - Sí se obtiene el nombre del campo
            setattr(self, "foto_actualizada", True)

        return super().save(commit)  # type: ignore - sí existe el método


class FormularioDatosUsuario(FormUsuarioFotoMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("username", "email", "foto_perfil")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[nc(Usuario.username)].help_text = ""

        if not kwargs["instance"].email:
            self.fields[
                nc(Usuario.email)
            ].help_text = "Es importante que tenga un correo, para poder restablecer su contraseña en caso de olvido"

    email = forms.EmailField(required=False, label="Correo")


class FormUsuario(FormUsuarioFotoMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = (
            "username",
            "email",
            "password",
            "is_active",
            "grupos",
            "user_permissions",
            "foto_perfil",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            nc(Usuario.username)
        ].help_text = "Solo letras, números, puntos, @, +, -"

        self.fields["grupos"].label = "Grupos asignados"
        self.fields["user_permissions"].label = "Permisos asignados"

        # al editar, no se requiere la contraseña
        if self.instance.pk:
            self.fields["password"].required = False

    field_order = (
        nc(Usuario.username),
        nc(Usuario.password),
        nc(Usuario.email),
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
