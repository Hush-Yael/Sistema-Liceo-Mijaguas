from enum import Enum
import re
from django import forms
from app.forms import (
    BusquedaFormMixin,
    CookieFormMixin,
    PaginacionFormMixin,
    busqueda_campo,
    opciones_tipo_busqueda,
)
from .models import Lapso, Materia, MatriculaEstados, Seccion, Año
import sys

MIGRANDO = "makemigrations" in sys.argv or "migrate" in sys.argv


class LapsoYSeccionBusquedaFormMixin(BusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore
        self.fields["lapsos"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    secciones = forms.ModelMultipleChoiceField(
        label="Sección:",
        queryset=Seccion.objects.all().order_by("año", "letra")
        if not MIGRANDO
        else None,
        required=False,
    )

    lapsos = forms.ModelMultipleChoiceField(
        label="Lapso:",
        queryset=Lapso.objects.all().order_by("-id") if not MIGRANDO else None,
        required=False,
    )


OPCION_BUSCAR_NOMBRES_Y_APELLIDOS = ("nombres_y_apellidos", "Nombres y apellidos")


class NotasBusquedaForm(LapsoYSeccionBusquedaFormMixin):
    campos_prefijo_cookie = "notas"
    opciones_columna_buscar = (
        OPCION_BUSCAR_NOMBRES_Y_APELLIDOS,
        ("matricula__estudiante__nombres", "Nombres"),
        ("matricula__estudiante__apellidos", "Apellidos"),
        ("matricula__estudiante__cedula", "Cédula"),
    )

    materias = forms.ModelMultipleChoiceField(
        label="Asignatura",
        queryset=Materia.objects.all().order_by("nombre") if not MIGRANDO else None,
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

    class Vocero(Enum):
        SIN_VOCERO = "no", "No"
        CON_VOCERO = "si", "Sí"

    class Disponibilidad(Enum):
        LLENA = "llena", "Llena"
        DISPONIBLE = "no_llena", "No llena"
        VACIA = "vacia", "Vacia"


class SeccionBusquedaForm(CookieFormMixin, PaginacionFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        opciones_texto = tuple(
            option.value[0] for option in OpcionesFormSeccion.ColumnasTexto
        ).__str__()[1:-1]

        self.fields["q"].widget.attrs.update(
            {
                ":type": "!opcionesBusquedaTexto.includes(columnaBuscada) ? 'number' : 'search'",
                "x-init": "establecerPlaceholderBusqueda()",
            }
        )

        self.campos_contenedor_x_data = re.sub(
            r"\s{2,}|\ng",
            "",
            f"""{{
                    opcionesBusquedaTexto: [{opciones_texto}],
                    placeholderBusqueda: '',

                    columnaBuscada: $el.$('[name=columna_buscada]').selectedOptions[0].textContent,

                    establecerPlaceholderBusqueda() {{
                      const inputColumna = $el.$('[name=columna_buscada]');
                      const columnaBuscada = inputColumna.selectedOptions[0].textContent;

                      const inputTipoBTexto = $el.$('[name=tipo_busqueda_texto]');
                      const inputTipoBNum = $el.$('[name=tipo_busqueda_numerica]');

                      const tipoBusqueda = this.opcionesBusquedaTexto.includes(inputColumna.value)
                          ? inputTipoBTexto
                          : inputTipoBNum;

                      return this.placeholderBusqueda =
                      `Buscar por: ${{columnaBuscada}}, ${{tipoBusqueda.options[tipoBusqueda.selectedIndex].textContent}}`
                    }}
                  }}
                """,
        )

    campos_prefijo_cookie = "secciones"
    campos_sin_cookies = ("q",)
    opciones_tipo_busqueda_cantidades = (
        ("lt", "menor a"),
        ("lte", "menor o igual a"),
        ("gt", "mayor a"),
        ("gte", "mayor o igual a"),
        ("exact", "igual a"),
    )

    q = busqueda_campo(attrs={":placeholder": "placeholderBusqueda"})

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

    tiene_vocero = forms.ChoiceField(
        label="¿Debe tener vocero?",
        initial=None,
        choices=(
            OpcionesFormSeccion.Vocero.CON_VOCERO.value,
            OpcionesFormSeccion.Vocero.SIN_VOCERO.value,
        ),
        required=False,
    )

    disponibilidad = forms.ChoiceField(
        label="Disponibilidad",
        initial=None,
        choices=(opcion.value for opcion in OpcionesFormSeccion.Disponibilidad),
        required=False,
    )

    columna_buscada = forms.ChoiceField(
        label="Columna de búsqueda",
        initial=None,
        choices=(
            *(opcion.value for opcion in OpcionesFormSeccion.ColumnasTexto),
            *(opcion.value for opcion in OpcionesFormSeccion.ColumnasNumericas),
        ),
        required=False,
    )

    tipo_busqueda_texto = forms.ChoiceField(
        label="Tipo de búsqueda por texto",
        initial=None,
        choices=opciones_tipo_busqueda,
        required=False,
    )

    tipo_busqueda_numerica = forms.ChoiceField(
        label="Tipo de búsqueda numérica",
        initial=None,
        choices=opciones_tipo_busqueda_cantidades,
        required=False,
    )


class MatriculaBusquedaForm(LapsoYSeccionBusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    campos_prefijo_cookie = "matriculas"
    opciones_columna_buscar = (
        OPCION_BUSCAR_NOMBRES_Y_APELLIDOS,
        ("estudiante__nombres", "Nombres"),
        ("estudiante__apellidos", "Apellidos"),
        ("estudiante__cedula", "Cédula"),
    )

    estado = forms.ChoiceField(
        label="Estado:",
        initial=None,
        choices=MatriculaEstados.choices,
        required=False,
    )


class AsignacionesBuscarTipoOpciones(Enum):
    TODOS = "1", "Asignada en los seleccionados"
    NO_TODOS = "2", "No asignada en ninguno de los seleccionados"
    ALGUNOS = "3", "Asignada en alguno de los seleccionados"
    NO_ALGUNOS = "4", "No asignada en ninguno de los seleccionados"


class MateriaBusquedaForm(CookieFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["anios_asignados"].label_from_instance = (  # type: ignore
            lambda obj: obj.nombre_corto
        )

        self.campos_contenedor_x_data = "{ tipoBusqueda: $el.$('[name=tipo_busqueda]').selectedOptions[0].textContent }"

    campos_sin_cookies = ("q",)

    campos_prefijo_cookie = "materias"

    q = busqueda_campo(
        attrs={
            "placeholder": "Buscar por: Nombre",
            ":placeholder": "'Buscar por: Nombre, ' + tipoBusqueda ",
        }
    )

    tipo_busqueda = forms.ChoiceField(
        label="Tipo de búsqueda por nombre",
        initial=None,
        choices=opciones_tipo_busqueda,
        required=False,
        widget=forms.Select(
            attrs={
                "@change": "tipoBusqueda = $event.target.selectedOptions[0].textContent"
            }
        ),
    )

    tipo_busqueda_anios = forms.ChoiceField(
        label="Condición de búsqueda:",
        choices=(opcion.value for opcion in AsignacionesBuscarTipoOpciones),
        required=False,
        initial=AsignacionesBuscarTipoOpciones.TODOS.value,
    )

    anios_asignados = forms.ModelMultipleChoiceField(
        label="Búsqueda por años:",
        queryset=Año.objects.all() if not MIGRANDO else None,
        initial=(),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={":class": '{"opacity-0.5": sin_asignaciones}'}
        ),
    )


class LapsoBuscarOpciones(Enum):
    NOMBRE = (
        "nombre",
        "Nombre",
    )
    NUMERO = "numero", "Número"


class LapsoBusquedaForm(BusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["q"].widget.attrs.update(
            {
                ":type": f"columnaBuscada === '{LapsoBuscarOpciones.NUMERO.value[1]}' ? 'number' : 'search'"
            }
        )

    campos_prefijo_cookie = "lapsos"
    opciones_columna_buscar = tuple((opcion.value for opcion in LapsoBuscarOpciones))

    campos_contenedor_x_data = """{
      columnaBuscada: $el.$('[name=columna_buscada]').selectedOptions[0].textContent,
      tipoBusqueda: $el.$('[name=tipo_busqueda]').selectedOptions[0].textContent
    }"""
