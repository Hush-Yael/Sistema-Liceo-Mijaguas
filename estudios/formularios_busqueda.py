from django import forms

from app.forms import BusquedaFormMixin
from .models import Lapso, Materia, Seccion


class NotasBusquedaForm(BusquedaFormMixin):
    seccion_prefijo_cookie = "notas"
    opciones_columna_buscar = (
        ("nombres_y_apellidos", "Nombres y apellidos"),
        ("matricula__estudiante__nombres", "Nombres"),
        ("matricula__estudiante__apellidos", "Apellidos"),
        ("matricula__estudiante__cedula", "Cédula"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notas_secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore
        self.fields["notas_lapsos"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    notas_materias = forms.ModelMultipleChoiceField(
        label="Asignatura",
        queryset=Materia.objects.all().order_by("nombre"),
        required=False,
    )

    notas_secciones = forms.ModelMultipleChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra"),
        required=False,
    )

    notas_lapsos = forms.ModelMultipleChoiceField(
        label="Lapso",
        queryset=Lapso.objects.all().order_by("-id"),
        required=False,
    )

    notas_valor_maximo = forms.FloatField(
        label="Máxima",
        min_value=1,
        max_value=20,
        initial=20,
        step_size=0.1,
        required=False,
    )

    notas_valor_minimo = forms.FloatField(
        label="Mínima",
        min_value=0,
        max_value=20,
        initial=0,
        step_size=0.1,
        required=False,
    )
