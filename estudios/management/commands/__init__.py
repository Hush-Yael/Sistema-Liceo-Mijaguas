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
from unicodedata import normalize


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

    def obtener_año_id(self, año_id: "int | None"):
        if año_id is None:
            return self.stdout.write(
                self.style.ERROR(
                    "Debes proporcionar el número del año objetivo para esta operación."
                )
            )

        try:
            return ModelosParametros.Año.objects.get(id=año_id)
        except ModelosParametros.Año.DoesNotExist:
            return self.stdout.write(
                self.style.ERROR(
                    f"No existe el año número {año_id}. "
                    f"Ejecuta primero poblar_datos_estudios para crear los años por defecto."
                )
            )

    def obtener_lapso_objetivo(self, lapso_objetivo: "int | None"):
        if lapso_objetivo is None:
            return self.stdout.write(
                self.style.ERROR("No se proporcionó un lapso para la operación.")
            )

        try:
            return ModelosParametros.Lapso.objects.get(pk=lapso_objetivo)
        except ModelosParametros.Lapso.DoesNotExist:
            return self.stdout.write(
                self.style.ERROR("No se encontró el lapso con el id proporcionado.")
            )


def obtener_modelos_modulo(modulo: ModuleType) -> "tuple[models.Model, ...]":
    return tuple(
        obj
        for _, obj in inspect.getmembers(modulo)
        if isinstance(obj, models.base.ModelBase)  # type: ignore - si se usa models.Model no funciona
        and not getattr(obj._meta, "abstract")  # type: ignore - no recuperar modelos abstractos
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


def quitar_diacriticos(texto):
    # Normaliza la cadena en forma descompuesta (NFD)
    texto_nfd = normalize("NFD", texto)
    # Elimina los caracteres diacríticos (rangos U+0300 a U+036F)
    texto_sin_diacriticos = "".join(
        char for char in texto_nfd if ord(char) < 0x0300 or ord(char) > 0x036F
    )
    # Vuelve a normalizar a forma compuesta (NFC)
    return normalize("NFC", texto_sin_diacriticos)
