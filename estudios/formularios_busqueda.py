from django import forms
from .models import Lapso, Materia, Profesor, Seccion


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

opciones_tipo_busqueda = [
    ("contains", "Contiene"),
    ("iexact", "Exacta"),
    ("startswith", "Empieza con"),
    ("endswith", "Termina con"),
]


class FormularioProfesorBusqueda(forms.Form):
    busqueda = forms.CharField(label="Buscar", max_length=100, required=False)

    tipo_busqueda = forms.ChoiceField(
        label="Tipo de busqueda",
        choices=opciones_tipo_busqueda,
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
    (m[0], m[1]) for m in Materia.objects.values_list("id", "nombre")
]


class FormularioNotasBusqueda(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notas_secciones"].label_from_instance = lambda obj: obj.nombre
        self.fields["notas_lapsos"].label_from_instance = lambda obj: obj.nombre

    opciones_columna_buscada = [
        ("nombres_apellidos", "Nombres y apellidos"),
        ("matricula__estudiante__nombres", "Nombres"),
        ("matricula__estudiante__apellidos", "Apellidos"),
        ("matricula__estudiante__cedula", "Cédula"),
    ]

    notas_materias = forms.ModelMultipleChoiceField(
        label="Asignatura",
        queryset=Materia.objects.all().order_by("nombre"),
        widget=forms.CheckboxSelectMultiple,
    )

    notas_secciones = forms.ModelMultipleChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra"),
        widget=forms.CheckboxSelectMultiple,
    )

    notas_lapsos = forms.ModelMultipleChoiceField(
        label="Lapso",
        queryset=Lapso.objects.all().order_by("-id"),
        widget=forms.CheckboxSelectMultiple,
    )

    notas_columna_buscada = forms.ChoiceField(
        label="Buscar por",
        initial=opciones_columna_buscada[0][0],
        choices=opciones_columna_buscada,
    )

    notas_tipo_busqueda = forms.ChoiceField(
        label="Tipo de búsqueda",
        initial=opciones_tipo_busqueda[0][0],
        choices=opciones_tipo_busqueda,
    )

    notas_valor_maximo = forms.FloatField(
        label="Máxima",
        min_value=1,
        max_value=20,
        initial=20,
        step_size=0.1,
    )

    notas_valor_minimo = forms.FloatField(
        label="Mínima",
        min_value=0,
        max_value=20,
        initial=0,
        step_size=0.1,
    )

    notas_cantidad_paginas = forms.IntegerField(
        label="Cantidad por página",
        min_value=1,
        initial=50,
    )
