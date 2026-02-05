from django import forms
from django.db.models import OuterRef
from estudios.modelos.gestion.personas import Matricula
from estudios.modelos.parametros import Lapso, obtener_lapso_actual


class LapsoActualForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lapso_actual = obtener_lapso_actual()

    lapso = forms.ChoiceField(
        label="Lapso",
        required=False,
    )

    def clean_lapso(self):
        lapso = self.lapso_actual

        if lapso is None:
            raise forms.ValidationError("No se encontró un lapso actual")

        return lapso


def obtener_matriculas_de_lapso(lapso: Lapso):
    """filtra los estudiantes y devuelve aquellos matriculados en un lapso específico"""
    return Matricula.objects.filter(estudiante=OuterRef("pk"), lapso=lapso)
