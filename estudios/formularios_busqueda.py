from django import forms

from app.forms import BusquedaFormMixin
from .models import Lapso, Materia, Seccion


class NotasBusquedaForm(BusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore
        self.fields["lapsos"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    campos_prefijo_cookie = "notas"
    opciones_columna_buscar = (
        ("nombres_y_apellidos", "Nombres y apellidos"),
        ("matricula__estudiante__nombres", "Nombres"),
        ("matricula__estudiante__apellidos", "Apellidos"),
        ("matricula__estudiante__cedula", "Cédula"),
    )

    secciones = forms.ModelMultipleChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra"),
        required=False,
    )

    lapsos = forms.ModelMultipleChoiceField(
        label="Lapso",
        queryset=Lapso.objects.all().order_by("-id"),
        required=False,
    )

    materias = forms.ModelMultipleChoiceField(
        label="Asignatura",
        queryset=Materia.objects.all().order_by("nombre"),
        required=False,
    )

    valor_maximo = forms.FloatField(
        label="Valor máximo",
        min_value=1,
        max_value=20,
        initial=20,
        step_size=0.1,
        required=False,
    )

    valor_minimo = forms.FloatField(
        label="Valor mínimo",
        min_value=0,
        max_value=20,
        initial=0,
        step_size=0.1,
        required=False,
    )
