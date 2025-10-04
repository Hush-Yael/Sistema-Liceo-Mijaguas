from django import forms
from django.contrib.auth.models import User


class FormularioRegistro(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Repita la contraseña", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["username"]

    def clean_password2(self):
        datos = self.cleaned_data
        if datos["password"] != datos["password2"]:
            return forms.ValidationError("Las contraseñas no son iguales")
        return datos["password2"]
