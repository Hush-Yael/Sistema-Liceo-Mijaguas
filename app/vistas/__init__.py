from typing import Literal, Type
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import models
from django.urls import path
from django.views.generic import View


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


class Vista(PermissionRequiredMixin):
    """Vista básica para todas las vistas de la app. Se encarga de validar los permisos pertinentes al modelo de la vista y de obtener datos relacionados al nombre de sus objetos."""

    tipo_permiso: Literal["add", "change", "delete", "view"]
    nombre_modelo: str
    nombre_app_modelo: str
    nombre_objeto: str
    nombre_objeto_plural: str
    genero_sustantivo_objeto: "Literal['M', 'F']" = "M"
    articulo_sustantivo: str
    articulo_sustantivo_plural: str
    vocal_del_genero: Literal["a", "o"]
    model: Type[models.Model]

    def __init__(self):
        self.nombre_modelo = self.model._meta.model_name  # type: ignore
        self.nombre_app_modelo = self.model._meta.app_label
        self.nombre_objeto = self.model._meta.verbose_name  # type: ignore
        self.nombre_objeto_plural = self.model._meta.verbose_name_plural  # type: ignore

        genero = self.genero_sustantivo_objeto

        if genero == "M":
            self.articulo_sustantivo = "el"
            self.articulo_sustantivo_plural = "los"
            self.vocal_del_genero = "o"

        elif genero == "F":
            self.articulo_sustantivo = "la"
            self.articulo_sustantivo_plural = "las"
            self.vocal_del_genero = "a"

        self.permission_required = (
            f"{self.nombre_app_modelo}.{self.tipo_permiso}_{self.nombre_modelo}"
        )

        super().__init__()
