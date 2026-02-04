from django import forms
from django.db.models import Exists, OuterRef

from app.settings import MIGRANDO
from estudios.modelos.gestion import (
    Estudiante,
    Matricula,
)
from estudios.modelos.parametros import (
    Lapso,
    Seccion,
    obtener_lapso_actual,
)


def obtener_matriculas_de_lapso(lapso: Lapso):
    """filtra los estudiantes y devuelve aquellos matriculados en un lapso específico"""
    return Matricula.objects.filter(estudiante=OuterRef("pk"), lapso=lapso)


class FormMatricula(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["seccion"].label_from_instance = lambda obj: obj.nombre  # type: ignore

        lapso_actual = self.lapso_actual = obtener_lapso_actual()

        # cambiar las opciones del campo "estudiante" por los estudiantes NO matriculados en el lapso actual
        if lapso_actual is not None:
            matriculas_lapso_actual = obtener_matriculas_de_lapso(lapso_actual)

            # al editar, conservar al estudiante de la matricula actual
            if self.instance.pk:
                matriculas_lapso_actual = matriculas_lapso_actual.exclude(
                    pk=self.instance.pk
                )

            self.fields["estudiante"].queryset = (  # type: ignore
                Estudiante.objects.annotate(
                    matriculado_actualmente=Exists(matriculas_lapso_actual)
                )
                .filter(matriculado_actualmente=False, bachiller__isnull=True)
                .order_by("apellidos", "nombres")
            )

            self.fields["lapso"].choices = (("", lapso_actual.nombre),)  # type: ignore

    class Meta:
        model = Matricula
        fields = ("estudiante", "seccion", "estado", "lapso")

    lapso_actual: "Lapso | None" = None

    estudiante = forms.ModelChoiceField(
        label="Estudiante",
        queryset=Estudiante.objects.none() if not MIGRANDO else None,
    )

    seccion = forms.ModelChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra")
        if not MIGRANDO
        else None,
    )

    lapso = forms.ChoiceField(
        label="Lapso",
        required=False,
    )

    def clean_estudiante(self):
        if estudiante := self.cleaned_data.get("estudiante"):
            matriculas_lapso_actual = Matricula.objects.filter(
                estudiante=estudiante, lapso=self.lapso_actual
            )

            if matriculas_lapso_actual.exists():
                raise forms.ValidationError("El estudiante ya se encuentra matriculado")

        return estudiante

    def clean_seccion(self):
        if seccion := self.cleaned_data.get("seccion"):
            # al crear, verificar que la sección no este llena
            if self.instance.pk is None:
                cantidad_actual = Matricula.objects.filter(
                    seccion=seccion, lapso=obtener_lapso_actual()
                ).count()

                if cantidad_actual >= seccion.capacidad:
                    raise forms.ValidationError(
                        "La sección seleccionada se encuentra llena"
                    )

        return seccion

    def clean_lapso(self):
        lapso = self.lapso_actual

        if lapso is None:
            raise forms.ValidationError("No se encontró un lapso actual")

        return lapso
