from django import forms
from app.campos import CampoBooleanoONulo
from app.forms import (
    BusquedaFormMixin,
    OrdenFormMixin,
)
from app.util import nc
from usuarios.models import Grupo, Usuario


class UsuarioBusquedaForm(OrdenFormMixin, BusquedaFormMixin):
    class Campos:
        TIENE_EMAIL = "tiene_email"
        ACTIVO = "activo"
        GRUPOS = "grupos"

    campos_prefijo_cookie = "usuarios"
    columnas_busqueda = (
        {
            "columna_db": nc(Usuario.username),
            "nombre_campo": "nombre",
        },
        {
            "columna_db": nc(Usuario.email),
            "nombre_campo": "correo",
        },
    )
    opciones_orden = (
        (nc(Usuario.username), "Nombre"),
        (nc(Usuario.email), "Correo"),
        (nc(Usuario.date_joined), "Fecha de añadido"),
        (nc(Usuario.last_login), "Último inicio de sesión"),
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
