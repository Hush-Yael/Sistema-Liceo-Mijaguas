# forms.py
import json
from django import forms
from django.db import models


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


opciones_tipo_busqueda = (
    ("contains", "Contiene"),
    ("iexact", "Exacta"),
    ("startswith", "Empieza con"),
    ("endswith", "Termina con"),
)


def busqueda_campo(placeholder="Buscar", attrs: "dict[str, str] | None" = None):
    _attrs = {
        "placeholder": placeholder,
        "id": "q",
        "name": "q",
        "type": "search",
        "hx-post": "",
        "hx-trigger": "input changed delay:600ms",
    }

    if attrs is not None:
        _attrs.update(attrs)

    return forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs=_attrs),
    )


class BusquedaFormMixin(CookieFormMixin, forms.Form):
    opciones_columna_buscar: "tuple[tuple[str, str], ...]"
    opciones_tipo_busqueda = opciones_tipo_busqueda
    columnas_a_evitar: "set[str]"
    campos_sin_cookies = ("q",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if (
            not hasattr(self, "opciones_columna_buscar")
            or not self.opciones_columna_buscar
        ):
            campos: "list[models.Field]" = self.model._meta.fields  # type: ignore

            if hasattr(self, "columnas_a_evitar"):
                self.opciones_columna_buscar = [
                    (f.name, f.verbose_name)  # type: ignore
                    for f in campos
                    if f.name not in self.columnas_a_evitar
                ]
            else:
                self.opciones_columna_buscar = [
                    (f.name, f.verbose_name)  # type: ignore
                    for f in campos
                ]

        if not self.fields["columna_buscada"].choices:  # type: ignore
            self.fields["columna_buscada"].choices = self.opciones_columna_buscar  # type: ignore

        if not self.fields["columna_buscada"].initial:
            self.fields["columna_buscada"].initial = self.opciones_columna_buscar[0][0]

        if not self.fields["tipo_busqueda"].choices:  # type: ignore
            self.fields["tipo_busqueda"].choices = self.opciones_tipo_busqueda  # type: ignore

        if not self.fields["tipo_busqueda"].initial:
            self.fields["tipo_busqueda"].initial = self.opciones_tipo_busqueda[0][0]

    cantidad_por_pagina = forms.IntegerField(
        label="Cantidad por página",
        min_value=1,
        initial=50,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "style": "max-width: 6ch;",
                "hx-trigger": "input changed delay:600ms",
                "hx-post": "",
            }
        ),
    )

    tipo_busqueda = forms.ChoiceField(
        label="Tipo de búsqueda",
        required=False,
    )

    columna_buscada = forms.ChoiceField(
        label="Buscar por",
        required=False,
    )

    q = busqueda_campo()
