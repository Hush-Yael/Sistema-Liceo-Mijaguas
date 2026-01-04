from django import forms
from .models import Año, Materia, Lapso, AñoMateria
from datetime import date


class FormAño(forms.ModelForm):
    class Meta:
        model = Año
        fields = ("nombre", "nombre_corto")
        labels = {
            "nombre": "Nombre completo del año",
            "nombre_corto": "Nombre corto del año",
        }

        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Primer año"}),
            "nombre_corto": forms.TextInput(attrs={"placeholder": "Ej: 1ero"}),
        }


class FormLapso(forms.ModelForm):
    class Meta:
        model = Lapso
        fields = "__all__"

        widgets = {
            "numero": forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "Ej: 3",
                }
            ),
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": f"Ej: {date.today().year}-III",
                }
            ),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }


asignaciones_campo = forms.ModelMultipleChoiceField(
    queryset=Año.objects.all(),
    widget=forms.CheckboxSelectMultiple(attrs={"id": "materia"}),
    initial=[],
    required=False,
)


class FormMateria(forms.ModelForm):
    asignaciones = asignaciones_campo

    class Meta:
        model = Materia
        fields = ("nombre", "asignaciones")
        labels = {
            "nombre": "Nombre de la materia",
        }

        widgets = {
            "nombre": forms.TextInput,
        }


class FormAsignaciones(forms.ModelForm):
    asignaciones = asignaciones_campo

    class Meta:
        model = AñoMateria
        fields = ("asignaciones",)
