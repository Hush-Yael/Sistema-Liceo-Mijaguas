# forms.py
import json
from django import forms


class CookieFormMixin:
    """Mixin para manejar valores de formulario en cookies"""

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request and self.request.method == "GET":
            self.cargar_desde_cookies()

    def cargar_desde_cookies(self):
        """Cargar valores iniciales desde cookies"""
        for campo_nombre, field in self.fields.items():  # type: ignore
            nombre_cookie = campo_nombre
            cookie_valor = self.request.COOKIES.get(nombre_cookie)

            if cookie_valor:
                try:
                    # Convertir según el tipo de campo
                    valor_inicial = self.deserializar_campo(field, cookie_valor)
                    if valor_inicial is not None:
                        self.initial[campo_nombre] = valor_inicial  # type: ignore
                except (ValueError, json.JSONDecodeError) as err:
                    # print(f"Err {err}", nombre_cookie, cookie_valor)
                    # Si hay error, usar valor por defecto
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
        for campo_nombre, valor in self.cleaned_data.items():  # type: ignore
            if valor is not None:
                nombre_cookie = campo_nombre
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


opciones_tipo_busqueda = [
    ("contains", "Contiene"),
    ("iexact", "Exacta"),
    ("startswith", "Empieza con"),
    ("endswith", "Termina con"),
]


class BusquedaFormMixin(CookieFormMixin, forms.Form):
    seccion_prefijo_cookie: str
    opciones_columna_buscar: "list[tuple[str, str]]"
    columnas_a_evitar: "set[str]" = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[f"{self.seccion_prefijo_cookie}_cantidad_por_pagina"] = (
            forms.IntegerField(
                label="Cantidad por página",
                min_value=1,
                initial=50,
                required=False,
            )
        )

        self.fields[f"{self.seccion_prefijo_cookie}_tipo_busqueda"] = forms.ChoiceField(
            label="Tipo de búsqueda",
            initial=opciones_tipo_busqueda[0][0],
            choices=opciones_tipo_busqueda,
            required=False,
        )

        if not self.opciones_columna_buscar:
            self.opciones_columna_buscar = [
                (f.name, f.verbose_name)
                for f in self.model._meta.fields  # type: ignore
                if f.name not in self.columnas_a_evitar
            ]

        self.fields[f"{self.seccion_prefijo_cookie}_columna_buscada"] = (
            forms.ChoiceField(
                label="Buscar por",
                initial=self.opciones_columna_buscar[0][0],
                choices=self.opciones_columna_buscar,
                required=False,
            )
        )
