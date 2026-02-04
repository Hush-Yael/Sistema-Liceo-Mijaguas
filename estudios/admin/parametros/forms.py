from datetime import datetime
from django import forms

from estudios.modelos.parametros import Lapso


class LapsoAdminForm(forms.ModelForm):
    class Meta:
        model = Lapso
        fields = "__all__"

    def clean_fecha_inicio(self):
        fecha = self.cleaned_data.get("fecha_inicio")

        if fecha is None:
            return

        if fecha < datetime.now().date():
            raise forms.ValidationError(
                "La fecha de inicio debe ser mayor o igual a la fecha actual"
            )

        return fecha

    def clean_fecha_fin(self):
        fecha = self.cleaned_data.get("fecha_fin")

        if fecha is None:
            return

        if fecha < datetime.now().date():
            raise forms.ValidationError(
                "La fecha de fin debe ser mayor o igual al año actual"
            )

        fecha_inicio = self.cleaned_data.get("fecha_inicio")

        if fecha_inicio is None:
            return fecha

        if fecha <= fecha_inicio:
            raise forms.ValidationError(
                "La fecha de fin debe ser mayor o igual a la fecha de inicio"
            )

        return fecha
