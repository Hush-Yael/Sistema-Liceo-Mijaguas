# forms.py
import json
from typing import TypedDict
from typing_extensions import NotRequired
from django import forms
from enum import Enum

from app.campos import (
    OPCIONES_TIPO_BUSQUEDA_TEXTUAL,
    FiltrosConjuntoOpciones,
)


class CookieFormMixin:
    """Mixin para manejar valores de formulario en cookies"""

    campos_prefijo_cookie: str
    campos_sin_cookies: "list[str] | tuple[str, ...]"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request and self.request.method == "GET":
            self.cargar_desde_cookies()

    def cargar_desde_cookies(self):
        """Cargar valores iniciales desde cookies"""
        hay_excepciones = hasattr(self, "campos_sin_cookies")
        for campo_nombre, field in self.fields.items():  # type: ignore
            if hay_excepciones and campo_nombre in self.campos_sin_cookies:
                continue

            nombre_cookie = f"{self.campos_prefijo_cookie}_{campo_nombre}"
            cookie_valor = self.request.COOKIES.get(nombre_cookie)

            if cookie_valor:
                try:
                    # Convertir según el tipo de campo
                    valor_inicial = self.deserializar_campo(field, cookie_valor)
                    if valor_inicial is not None:
                        self.initial[campo_nombre] = valor_inicial  # type: ignore
                # Si hay error, usar valor por defecto
                except (ValueError, json.JSONDecodeError):
                    # print(f"Err {err}", nombre_cookie, cookie_valor)
                    pass

    def deserializar_campo(self, field, cookie_valor):
        """Deserializar valor de cookie según tipo de campo"""
        if isinstance(field, forms.ModelMultipleChoiceField):
            try:
                data = json.loads(cookie_valor)
                if isinstance(data, list):
                    return [str(item) for item in data if item]
                return []
            except (json.JSONDecodeError, TypeError):
                return []

        elif (
            isinstance(field, forms.ChoiceField)
            and field.widget.allow_multiple_selected
        ):
            try:
                return json.loads(cookie_valor)
            except (json.JSONDecodeError, TypeError):
                return []

        elif isinstance(field, forms.DateField):
            from datetime import datetime

            try:
                return datetime.strptime(cookie_valor, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        elif isinstance(field, forms.BooleanField):
            return cookie_valor.lower() == "true"
        else:
            return cookie_valor

    def guardar_en_cookies(self, response):
        """Guardar valores del formulario en cookies"""
        hay_excepciones = hasattr(self, "campos_sin_cookies")
        for campo_nombre, valor in self.cleaned_data.items():  # type: ignore
            if hay_excepciones and campo_nombre in self.campos_sin_cookies:
                continue

            if valor is not None:
                nombre_cookie = f"{self.campos_prefijo_cookie}_{campo_nombre}"
                cookie_valor = self.serializar_campo(self.fields[campo_nombre], valor)  # type: ignore

                # Establecer cookie (válida por 30 días)
                if cookie_valor is not None:
                    response.set_cookie(
                        nombre_cookie,
                        cookie_valor,
                        max_age=30 * 24 * 60 * 60,  # 30 días
                        httponly=True,
                        secure=True,
                        samesite="Lax",
                    )

    def serializar_campo(self, field, valor):
        """Serializar valor para cookie según tipo de campo"""
        if isinstance(field, forms.ModelMultipleChoiceField):
            if hasattr(valor, "values_list"):  # QuerySet
                ids = list(valor.values_list("pk", flat=True))
            elif isinstance(valor, list):
                ids = [str(item.pk if hasattr(item, "pk") else item) for item in valor]
            else:
                ids = []
            return json.dumps(ids) if ids else ""

        elif (
            isinstance(field, forms.ChoiceField)
            and field.widget.allow_multiple_selected
        ):
            if isinstance(valor, list):
                return json.dumps([str(v) for v in valor])
            return json.dumps([])

        elif isinstance(field, forms.DateField):
            return valor.strftime("%Y-%m-%d") if valor else ""

        elif isinstance(field, forms.BooleanField):
            return "true" if valor else "false"

        elif isinstance(field, forms.ModelChoiceField):
            return str(valor.pk) if valor else ""

        else:
            return str(valor) if valor is not None else ""


class PaginacionFormMixin(forms.Form):
    cantidad_por_pagina = forms.IntegerField(
        label="Cantidad por página",
        min_value=1,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "style": "max-width: 6ch;",
                "hx-trigger": "input changed delay:600ms",
                "hx-post": "",
            }
        ),
    )


class ColumnaBusqueda(TypedDict):
    columna_db: str
    nombre_campo: str
    label_campo: NotRequired[str]
    opciones_tipo_busqueda: NotRequired["tuple[tuple[str, str], ...]"]


class BusquedaFormMixin(CookieFormMixin, PaginacionFormMixin):
    """Crea un formulario para realizar búsquedas. Genera los campos de búsqueda automáticamente a partir de las columnas indicadas"""

    def __init__(self, *args, **kwargs):
        # Indicar los campos que no se guardan en cookies antes de llamar al constructor CookieFormMixin, ya que si no, no se ignoran
        self.campos_sin_cookies = tuple(
            f"q_{columna['nombre_campo']}" for columna in self.columnas_busqueda
        )

        super().__init__(*args, **kwargs)

        _campos_busqueda = []

        for columna in self.columnas_busqueda:
            _nombre_campo = f"q_{columna['nombre_campo']}"
            label = columna.get("label_campo", columna["nombre_campo"].capitalize())
            _campo = forms.CharField(label=label, required=False)

            # se usa al momento de indicar el nombre de la columna en la base de datos al filtrar
            setattr(_campo, "nombre_columna_db", columna["columna_db"])

            self.fields[_nombre_campo] = _campo
            self.base_fields[_nombre_campo] = _campo

            opciones: "tuple[tuple[str, str], ...]" = columna.get(
                "opciones_tipo_busqueda", OPCIONES_TIPO_BUSQUEDA_TEXTUAL
            )

            _campo_tipo_q = forms.ChoiceField(
                required=False,
                choices=opciones,
            )
            _nombre_campo_tipo_q = f"tipo_{_nombre_campo}"

            self.fields[_nombre_campo_tipo_q] = _campo_tipo_q
            self.base_fields[_nombre_campo_tipo_q] = _campo_tipo_q

            _campos_busqueda.append(
                (
                    {"name": _nombre_campo, "campo": _campo},
                    {"name": _nombre_campo_tipo_q, "campo": _campo_tipo_q},
                )
            )

        self.campos_busqueda = _campos_busqueda

    columnas_busqueda: "tuple[ColumnaBusqueda, ...]"


class DireccionesOrden(Enum):
    DESC = "1", "Descendente"
    ASC = "2", "Ascendente"


class OrdenFormMixin:
    opciones_orden: "tuple[tuple[str, str], ...]"
    campos_orden: "list[forms.ChoiceField]"

    orden_ascendente = DireccionesOrden.ASC.value[0]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        direcciones = tuple(opcion.value for opcion in DireccionesOrden)
        campos_orden = []

        for _nombre, label in self.opciones_orden:
            nombre = f"{_nombre}-orden"
            campo = forms.ChoiceField(
                label=label,
                required=False,
                choices=direcciones,
            )

            self.base_fields[nombre] = campo  # type: ignore
            self.fields[nombre] = campo  # type: ignore
            campos_orden.append((nombre, campo))

        self.campos_orden = campos_orden


class ConjuntoOpcionesForm(forms.Form):
    campos_opciones: "list[tuple[str, forms.MultipleChoiceField | forms.ModelMultipleChoiceField]] | tuple[tuple[str, forms.MultipleChoiceField | forms.ModelMultipleChoiceField], ...]"
    sufijo_tipo_q = "_tipo_q"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for nombre, campo in self.campos_opciones:
            self.fields[nombre] = campo  # type: ignore
            self.base_fields[nombre] = campo  # type: ignore

            _n = f"{nombre}{self.sufijo_tipo_q}"
            campo_tipo_q = forms.ChoiceField(
                required=False,
                choices=(opcion.value for opcion in FiltrosConjuntoOpciones),
            )
            self.fields[_n] = campo_tipo_q  # type: ignore
            self.base_fields[_n] = campo_tipo_q  # type: ignore
