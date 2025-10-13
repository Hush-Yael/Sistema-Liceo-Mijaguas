from django import forms
from .models import Profesor


campos_a_evitar = ("id", "profesormateria", "esta_activo", "usuario")

_campos_para_buscar = filter(
    lambda f: f.name not in campos_a_evitar,
    Profesor._meta.get_fields(),
)

opciones_busqueda = [(f.name, f.verbose_name) for f in _campos_para_buscar]  # type: ignore


class FormularioProfesorBusqueda(forms.Form):
    busqueda = forms.CharField(label="Buscar", max_length=100, required=False)

    tipo_busqueda = forms.ChoiceField(
        label="Tipo de busqueda",
        choices=[
            ("__iexact", "Exacta"),
            ("__contains", "Contiene"),
            ("__startswith", "Empieza con"),
            ("__endswith", "Termina con"),
        ],
        required=False,
    )

    columna_buscada = forms.ChoiceField(
        label="Columna a buscar",
        choices=opciones_busqueda,
        required=False,
    )

    ordenar_por = forms.ChoiceField(
        label="Ordenar por",
        choices=opciones_busqueda,
        required=False,
    )

    direccion_de_orden = forms.ChoiceField(
        label="Dirección de orden",
        choices=[("asc", "Ascendente"), ("desc", "Descendente")],
        required=False,
    )
