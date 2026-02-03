from enum import Enum
from django import forms
from app.forms import (
    BusquedaFormMixin,
    ConjuntoOpcionesForm,
    OrdenFormMixin,
)
from app.campos import (
    OPCIONES_TIPO_BUSQUEDA_CANTIDADES,
    CampoBooleanoONulo,
    FiltrosConjuntoOpciones,
)
from .models import (
    Estudiante,
    Lapso,
    Materia,
    Matricula,
    MatriculaEstados,
    Seccion,
    Año,
)
import sys

MIGRANDO = "makemigrations" in sys.argv or "migrate" in sys.argv


class LapsoYSeccionFormMixin(BusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore
        self.fields["lapsos"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    secciones = forms.ModelMultipleChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra")
        if not MIGRANDO
        else None,
        required=False,
    )

    lapsos = forms.ModelMultipleChoiceField(
        label="Lapso",
        queryset=Lapso.objects.all().order_by("-id") if not MIGRANDO else None,
        required=False,
    )


class NotasBusquedaForm(LapsoYSeccionFormMixin):
    class Campos:
        MATERIAS = "materias"
        LAPSOS = "lapsos"
        SECCIONES = "secciones"

    campos_prefijo_cookie = "notas"
    columnas_busqueda = (
        {
            "columna_db": f"{Matricula._meta.verbose_name}__{Estudiante._meta.verbose_name}__{Estudiante.nombres.field.name}",
            "nombre_campo": "nombres",
        },
        {
            "columna_db": f"{Matricula._meta.verbose_name}__{Estudiante._meta.verbose_name}__{Estudiante.apellidos.field.name}",
            "nombre_campo": "apellidos",
        },
        {
            "columna_db": f"{Matricula._meta.verbose_name}__{Estudiante._meta.verbose_name}__{Estudiante.cedula.field.name}",
            "nombre_campo": "cedula",
        },
    )

    materias = forms.ModelMultipleChoiceField(
        label="Materia",
        queryset=Materia.objects.all().order_by("nombre") if not MIGRANDO else None,
        required=False,
    )


class OpcionesFormSeccion:
    class ColumnasTexto(Enum):
        NOMBRE = (
            "nombre",
            "Nombre",
        )
        NOMBRE_VOCERO = (
            "vocero_nombre_y_apellidos",
            "Nombre del vocero",
        )
        CEDULA_VOCERO = (
            "vocero__cedula",
            "Cédula del vocero",
        )

    class ColumnasNumericas(Enum):
        CAPACIDAD = (
            "capacidad",
            "Capacidad",
        )
        CANTIDAD = (
            "cantidad_matriculas",
            "Cantidad de alumnos",
        )

    class Disponibilidad(Enum):
        LLENA = "llena", "Llena"
        DISPONIBLE = "no_llena", "No llena"
        VACIA = "vacia", "Vacia"


class SeccionBusquedaForm(BusquedaFormMixin, forms.Form):
    class Campos:
        LETRA = "letra"
        ANIO = "anio"
        VOCERO = "tiene_vocero"
        DISPONIBILIDAD = "disponibilidad"

    columnas_busqueda = (
        {
            "columna_db": Seccion.nombre.field.name,
            "nombre_campo": "nombre",
        },
        {
            "columna_db": Seccion.capacidad.field.name,
            "nombre_campo": "capacidad",
        },
        {
            "columna_db": "cantidad_matriculas",
            "nombre_campo": "cantidad_alumnos",
            "label_campo": "Cantidad de alumnos",
            "opciones_tipo_busqueda": OPCIONES_TIPO_BUSQUEDA_CANTIDADES,
        },
    )
    campos_prefijo_cookie = "secciones"

    anio = forms.ModelMultipleChoiceField(
        label="Año",
        initial=None,
        queryset=Año.objects.all() if not MIGRANDO else None,
        required=False,
    )

    letra = forms.MultipleChoiceField(
        label="Letra",
        initial=None,
        choices=(
            (
                (letra, letra)
                for letra in Seccion.objects.values_list("letra", flat=True)
                .order_by("letra")
                .distinct()
            )
            if not MIGRANDO
            else ()
        ),
        required=False,
    )

    tiene_vocero = CampoBooleanoONulo(
        label="¿Debe tener vocero?",
        label_no_escogido="Sin vocero",
        label_si_escogido="Con vocero",
    )

    disponibilidad = forms.ChoiceField(
        label="Disponibilidad",
        initial=None,
        choices=(opcion.value for opcion in OpcionesFormSeccion.Disponibilidad),
        required=False,
    )


class MatriculaBusquedaForm(OrdenFormMixin, LapsoYSeccionFormMixin):
    columnas_busqueda = (
        {
            "columna_db": f"{Estudiante._meta.verbose_name}__{Estudiante.nombres.field.name}",
            "nombre_campo": "nombres",
        },
        {
            "columna_db": f"{Estudiante._meta.verbose_name}__{Estudiante.apellidos.field.name}",
            "nombre_campo": "apellidos",
        },
        {
            "columna_db": f"{Estudiante._meta.verbose_name}__{Estudiante.cedula.field.name}",
            "nombre_campo": "cedula",
        },
    )
    opciones_orden = (
        (
            f"{Estudiante._meta.verbose_name}__{Estudiante.nombres.field.name}",
            "Nombres",
        ),
        (
            f"{Estudiante._meta.verbose_name}__{Estudiante.apellidos.field.name}",
            "Apellidos",
        ),
        (
            f"{Estudiante._meta.verbose_name}__{Estudiante.cedula.field.name}",
            "Cedula",
        ),
    )
    campos_prefijo_cookie = "matriculas"

    estado = forms.ChoiceField(
        label="Estado",
        initial=None,
        choices=MatriculaEstados.choices,
        required=False,
    )


class MateriaBusquedaForm(ConjuntoOpcionesForm, BusquedaFormMixin):
    class Campos:
        ANIOS_ASIGNADOS = "anios"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["anios"].label_from_instance = (  # type: ignore
            lambda obj: obj.nombre_corto
        )

    campos_opciones = (
        (
            Campos.ANIOS_ASIGNADOS,
            forms.ModelMultipleChoiceField(
                label="Años",
                queryset=Año.objects.all() if not MIGRANDO else None,
                required=False,
            ),
        ),
    )
    campos_prefijo_cookie = "materias"
    columnas_busqueda = (
        {
            "columna_db": Materia.nombre.field.name,
            "nombre_campo": "nombre",
        },
    )

    FiltrosConjuntoOpciones = tuple(opcion.value for opcion in FiltrosConjuntoOpciones)


class LapsoBuscarOpciones(Enum):
    NOMBRE = (
        "nombre",
        "Nombre",
    )
    NUMERO = "numero", "Número"


class LapsoBusquedaForm(BusquedaFormMixin):
    columnas_busqueda = (
        {
            "columna_db": "nombre",
            "nombre_campo": "nombre",
        },
        {
            "columna_db": "numero",
            "nombre_campo": "numero",
        },
    )
    campos_prefijo_cookie = "lapsos"
