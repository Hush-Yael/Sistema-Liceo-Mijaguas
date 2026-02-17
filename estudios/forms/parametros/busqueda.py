from enum import Enum
from django import forms
from app.campos import OPCIONES_TIPO_BUSQUEDA_CANTIDADES, CampoBooleanoONulo
from app.forms import BusquedaFormMixin, ConjuntoOpcionesForm
from app.util import nc
from estudios.modelos.parametros import Lapso, Materia, Seccion, Año
from app.campos import FiltrosConjuntoOpciones
from app.settings import MIGRANDO


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
        VOCERO = "tiene_vocero"
        DISPONIBILIDAD = "disponibilidad"

    columnas_busqueda = (
        (
            {
                "columna_db": nc(Seccion.nombre),
                "nombre_campo": "nombre",
            },
            {
                "columna_db": nc(Seccion.capacidad),
                "nombre_campo": "capacidad",
            },
            {
                "columna_db": "cantidad_matriculas",
                "nombre_campo": "cantidad_alumnos",
                "label_campo": "Cantidad de alumnos",
                "opciones_tipo_busqueda": OPCIONES_TIPO_BUSQUEDA_CANTIDADES,
            },
        )
        if not MIGRANDO
        else ()
    )

    campos_prefijo_cookie = "secciones"

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
        (
            {
                "columna_db": nc(Materia.nombre),
                "nombre_campo": "nombre",
            },
        )
        if not MIGRANDO
        else ()
    )

    FiltrosConjuntoOpciones = tuple(opcion.value for opcion in FiltrosConjuntoOpciones)
