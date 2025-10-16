from django import forms
from .models import Materia, Profesor


campos_a_evitar = ("id", "profesormateria", "esta_activo", "usuario")

_campos_para_buscar = filter(
    lambda f: f.name not in campos_a_evitar,
    Profesor._meta.get_fields(),
)

opciones_busqueda = [
    (f.name, f.verbose_name)  # type: ignore
    for f in _campos_para_buscar
    if hasattr(f, "verbose_name")  # type: ignore
]


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


opciones_materias = [("", "Todas")] + [
    (m[0], m[1]) for m in Materia.objects.values_list("id", "nombre_materia")
]


class FormularioNotasBusqueda(forms.Form):
    materia_id = forms.ChoiceField(
        label="Mostrar por asignatura",
        choices=opciones_materias,
        initial="",
        required=False,
    )
    maximo = forms.FloatField(
        label="Nota máxima",
        min_value=0,
        max_value=20,
        initial=20,
    )
    minimo = forms.FloatField(
        label="Nota mínima",
        min_value=0,
        max_value=20,
        initial=0,
    )
