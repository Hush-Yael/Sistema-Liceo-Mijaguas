from typing import TypedDict
from django.core.management.base import BaseCommand
from faker import Faker
from types import ModuleType
from django.db import models
import estudios.modelos.gestion.personas as ModelosPersonas
import estudios.modelos.gestion.calificaciones as ModelosCalificaciones
import estudios.modelos.parametros as ModelosParametros
import usuarios.models as ModelosUsuarios
import inspect
import itertools


class Acciones(TypedDict):
    profesores: bool
    estudiantes: bool
    lapsos: bool
    asignar_materias: bool
    matriculas: bool
    notas: bool


class BaseComandos(BaseCommand):
    limpiar_todo: bool
    limpiar_modelo: str
    hacer_todo: bool
    año_id: int
    acciones: Acciones

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker("es_ES")  # Español de España
        self.faker.seed_instance(1234)  # Para resultados consistentes

    def si_accion(self, accion: str) -> bool:
        return self.hacer_todo or self.acciones[accion]


def obtener_modelos_modulo(modulo: ModuleType) -> "tuple[models.Model, ...]":
    return tuple(
        obj
        for _, obj in inspect.getmembers(modulo)
        if isinstance(obj, models.base.ModelBase)  # type: ignore - si se usa models.Model no funciona
        and obj.__module__ == modulo.__name__
    )


def obtener_todos_los_modelos():
    lista_tuplas_modelos = tuple(
        obtener_modelos_modulo(modulo)
        for modulo in (
            ModelosCalificaciones,
            ModelosUsuarios,
            ModelosParametros,
            ModelosPersonas,
        )
    )

    return tuple(
        itertools.chain.from_iterable(
            modelo for modelo in (modelos for modelos in lista_tuplas_modelos)
        )
    )
