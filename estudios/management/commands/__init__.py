from typing import Type, TypedDict
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
from app.util import nc


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
    acciones: Acciones

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker("es_MX")

    def si_accion(self, accion: str) -> bool:
        return self.hacer_todo or self.acciones[accion]

    def obtener_modelo_objetivo(
        self,
        modelo: Type[models.Model],
        objeto_id: "int | None",
        campos: "tuple[str, str]",
        orden: "list[str] | tuple[str, ...]" = (),
        nulo=False,
    ):
        if not modelo.objects.exists():
            return self.stdout.write(
                self.style.ERROR(
                    f"No hay objetos para el modelo f{modelo._meta.verbose_name}. "
                )
            )

        if objeto_id is not None:
            try:
                return modelo.objects.get(id=objeto_id)
            except modelo.DoesNotExist:
                return self.stdout.write(
                    self.style.ERROR(
                        f"No existe {modelo._meta.verbose_name} con el id: {objeto_id}. "
                    )
                )
        elif not nulo:
            # Si no se proporciona un objeto, mostrar los objetos disponibles y continuar
            self.stdout.write("\n")
            self.stdout.write(
                f"No se proporcionó un {modelo._meta.verbose_name} especifico. Escoge uno:"
            )

            objetos = modelo.objects.values_list(*campos).order_by(*orden)

            for pk, nombre in objetos:
                self.stdout.write(f"{pk}: {nombre}")
            self.stdout.write("\n")

            pk_seccion = input("Presiona ENTER para cancelar:")

            if not pk_seccion.isdigit():
                return self.stdout.write(
                    self.style.ERROR("No se escogió una opcion valida.")
                )

            return modelo.objects.get(pk=int(pk_seccion))

    def obtener_seccion_objetivo(self, seccion_id: "int | None" = None, nula=False):
        return self.obtener_modelo_objetivo(
            ModelosParametros.Seccion,
            seccion_id,
            ("pk", nc(ModelosParametros.Seccion.nombre)),
            ("año__pk",),
            nula,
        )

    def obtener_lapso_objetivo(self, id_lapso: "int | None" = None, nulo=False):
        return self.obtener_modelo_objetivo(
            ModelosParametros.Lapso,
            id_lapso,
            ("pk", nc(ModelosParametros.Lapso.nombre)),
            ("pk",),
            nulo,
        )

    def obtener_año_objetivo(self, id_año: "int | None" = None, nulo=False):
        return self.obtener_modelo_objetivo(
            ModelosParametros.Año,
            id_año,
            ("pk", nc(ModelosParametros.Año.nombre)),
            ("pk",),
            nulo,
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
