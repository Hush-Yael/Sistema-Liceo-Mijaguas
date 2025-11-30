from django import forms
from .models import Año, Materia, Lapso
from datetime import date


class FormAño(forms.ModelForm):
    class Meta:
        model = Año
        fields = ("numero", "nombre", "nombre_corto")
        labels = {
            "numero": "Número del año",
            "nombre": "Nombre completo del año",
            "nombre_corto": "Nombre corto del año",
        }

        widgets = {
            "numero": forms.NumberInput(attrs={"min": 1}),
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Primer año"}),
            "nombre_corto": forms.TextInput(attrs={"placeholder": "Ej: 1ero"}),
        }


class FormLapso(forms.ModelForm):
    class Meta:
        model = Lapso
        fields = ("numero", "nombre", "fecha_inicio", "fecha_fin")
        labels = {
            "numero": "Número",
            "nombre": "Nombre",
            "fecha_inicio": "Fecha de inicio",
            "fecha_fin": "Fecha de fin",
        }

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


class FormMateria(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asignaciones"].label_from_instance = lambda obj: obj.nombre_corto

    asignaciones = forms.ModelMultipleChoiceField(
        queryset=Año.objects.all().order_by("numero"),
        widget=forms.CheckboxSelectMultiple(attrs={"id": "materia"}),
        required=False,
    )

    class Meta:
        model = Materia
        fields = ("nombre", "asignaciones")
        labels = {
            "nombre": "Nombre de la materia",
        }

        widgets = {
            "nombre": forms.TextInput,
        }
