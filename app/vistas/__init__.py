from typing import Literal, Type
from django.db import models
from django.urls import path
from django.views.generic import View
from app.vistas.auth import VistaProtegidaMixin


def nombre_url_crear_auto(modelo: Type[models.Model]) -> str:
    return f"crear_{modelo._meta.model_name}"


def nombre_url_editar_auto(modelo: Type[models.Model]) -> str:
    return f"editar_{modelo._meta.model_name}"


def nombre_url_lista_auto(modelo: Type[models.Model]) -> str:
    return str(modelo._meta.model_name)


def crear_crud_urls(
    modelo: Type[models.Model],
    vista_lista: Type[View],
    vista_crear: Type[View],
    vista_actualizar: Type[View],
):
    nombre_objeto_plural = f"{modelo._meta.verbose_name_plural}/"

    """Crear urls para el CRUD de un modelo"""
    return (
        path(
            nombre_objeto_plural,
            vista_lista.as_view(),
            name=nombre_url_lista_auto(modelo),
        ),
        path(
            f"{nombre_objeto_plural}crear/",
            vista_crear.as_view(),
            name=nombre_url_crear_auto(modelo),
        ),
        path(
            f"{nombre_objeto_plural}editar/<int:pk>/",
            vista_actualizar.as_view(),
            name=nombre_url_editar_auto(modelo),
        ),
    )


class VistaLocalizadaMixin:
    """Mixin para vistas que muestran información localizada acerca del modelo usado."""

    model: Type[models.Model]
    nombre_objeto: str
    nombre_objeto_plural: str
    genero_sustantivo_objeto: "Literal['M', 'F']" = "M"
    articulo_sustantivo: str
    articulo_sustantivo_plural: str
    vocal_del_genero: Literal["a", "o"]

    def __init__(self):
        """Establece los atributos de la clase con los valores obtenidos de la información del modelo."""

        self.nombre_objeto = str(self.model._meta.verbose_name)
        self.nombre_objeto_plural = str(self.model._meta.verbose_name_plural)

        genero = self.genero_sustantivo_objeto

        if genero == "M":
            self.articulo_sustantivo = "el"
            self.articulo_sustantivo_plural = "los"
            self.vocal_del_genero = "o"

        elif genero == "F":
            self.articulo_sustantivo = "la"
            self.articulo_sustantivo_plural = "las"
            self.vocal_del_genero = "a"


class Vista(VistaProtegidaMixin, VistaLocalizadaMixin):
    """Vista genérica que combina el mixin de vistas localizadas y de vistas protegidas."""
