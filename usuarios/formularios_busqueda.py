from django import forms
from app.campos import CampoBooleanoONulo
from app.forms import (
    BusquedaFormMixin,
    OrdenFormMixin,
)
from .models import Grupo, Usuario


class UsuarioBusquedaForm(OrdenFormMixin, BusquedaFormMixin):
    class Campos:
        TIENE_EMAIL = "tiene_email"
        ACTIVO = "activo"
        GRUPOS = "grupos"

    campos_prefijo_cookie = "usuarios"
    columnas_busqueda = (
        {
            "columna_db": Usuario.username.field.name,
            "nombre_campo": "nombre",
        },
        {
            "columna_db": Usuario.email.field.name,
            "nombre_campo": "correo",
        },
    )
    opciones_orden = (
        (Usuario.username.field.name, "Nombre"),
        (Usuario.email.field.name, "Correo"),
        (Usuario.date_joined.field.name, "Fecha de añadido"),
        (Usuario.last_login.field.name, "Último inicio de sesión"),
    )

    activo = CampoBooleanoONulo(
        label="Por estado",
        label_si="Solo activos",
        label_no="Solo inactivos",
    )

    tiene_email = CampoBooleanoONulo(
        label="Tiene correo",
        label_si_escogido="Con correo",
        label_no_escogido="Sin correo",
    )

    cantidad_por_pagina = forms.IntegerField(
        label="Cantidad por página",
        min_value=1,
        initial=50,
        required=False,
    )

    grupos = forms.ModelMultipleChoiceField(
        label="Grupos",
        queryset=Grupo.objects.all().order_by("name"),
        required=False,
    )
