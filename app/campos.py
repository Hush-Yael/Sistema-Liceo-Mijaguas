from enum import Enum
from django import forms


OPCIONES_TIPO_BUSQUEDA_TEXTUAL = (
    ("contains", "contiene"),
    ("iexact", "igual a"),
    ("startswith", "empieza con"),
    ("endswith", "termina con"),
)


OPCIONES_TIPO_BUSQUEDA_CANTIDADES = (
    ("lt", "menor a"),
    ("lte", "menor o igual a"),
    ("gt", "mayor a"),
    ("gte", "mayor o igual a"),
    ("exact", "igual a"),
)

OPCIONES_TIPO_BUSQUEDA_FECHA = (
    ("date", "Exacta"),
    ("lt", "Antes de"),
    ("gt", "Después de"),
)


class TextosBooleanos(Enum):
    NULO = ""
    VERDADERO = "1"
    FALSO = "0"


def CampoBooleanoONulo(
    label: str,
    label_si: str = "Sí",
    label_no: str = "No",
    label_si_escogido: str = "",
    label_no_escogido: str = "",
) -> forms.ChoiceField:
    campo = forms.ChoiceField(
        label=label,
        widget=forms.RadioSelect,
        required=False,
        choices=(
            (TextosBooleanos.NULO.value, ""),
            (TextosBooleanos.VERDADERO.value, label_si),
            (TextosBooleanos.FALSO.value, label_no),
        ),
    )

    setattr(
        campo,
        "labels_escogidos",
        {
            TextosBooleanos.VERDADERO.value: label_si_escogido or label_si,
            TextosBooleanos.FALSO.value: label_no_escogido or label_no,
        },
    )

    setattr(campo, "valor_opcion_nula", TextosBooleanos.NULO.value)

    return campo


# Opciones para el tipo de filtro de conjuntos de opciones
class FiltrosConjuntoOpciones(Enum):
    CONTIENE_TODAS = "*", "Debe incluir TODAS las opciones"
    NO_CONTIENE_TODAS = "!*", "NO debe incluir TODAS las opciones"
    CONTIENE_ALGUNA = "-", "Debe incluir ALGUNA de las opciones seleccionadas"
    NO_CONTIENE_ALGUNA = "!-", "NO debe incluir ALGUNA de las opciones seleccionadas"
