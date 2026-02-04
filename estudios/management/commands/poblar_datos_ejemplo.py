from typing import TypedDict
from django.core.management.base import BaseCommand
from estudios.management.commands.gestion import ArgumentosGestionMixin
from estudios.management.commands.parametros import ArgumentosParametrosMixin
from estudios.modelos.gestion import (
    Bachiller,
    Profesor,
    Estudiante,
    ProfesorMateria,
    Matricula,
    Nota,
)
from estudios.modelos.parametros import (
    Lapso,
)
from faker import Faker
from django.db import connection


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


class Command(ArgumentosParametrosMixin, ArgumentosGestionMixin, BaseComandos):
    help = "LLena la base de datos con datos de ejemplo usando Faker"

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--limpiar-todo",
            action="store_true",
            help="Eliminar todos los datos de ejemplo existentes",
        )

        parser.add_argument(
            "--limpiar",
            type=str,
            help="Eliminar todos los datos del modelo indicado",
        )

        parser.add_argument(
            "--todo",
            action="store_true",
            help="Crear todos los datos de ejemplo (por defecto si no se especifica nada)",
        )

    def handle(self, *args, **options):
        self.año_id = options["año"]
        self.limpiar_todo = options["limpiar_todo"]
        self.limpiar_modelo = options["limpiar"]
        self.hacer_todo = options["todo"]

        if self.limpiar_todo:
            self.limpiar_datos()
        elif self.limpiar_modelo is not None:
            self.limpiar_por_tipo(self.limpiar_modelo)

        # Determinar qué acciones ejecutar
        self.acciones = {
            "profesores": options["profesores"],
            "estudiantes": options["estudiantes"],
            "lapsos": options["lapsos"],
            "asignar_materias": options["asignar_materias"],
            "matriculas": options["matriculas"],
            "notas": options["notas"],
        }

        # no se indicaron acciones
        if (
            not self.limpiar_todo
            and self.limpiar_modelo is None
            and self.hacer_todo is None
            and not any(self.acciones.values())
        ):
            return self.stdout.write(
                self.style.ERROR("No se especificaron acciones a ejecutar.")
            )

        super().handle(*args, **options)

    def limpiar_datos(self):
        self.stdout.write("Eliminando todos los datos dinámicos existentes...")

        modelos_a_limpiar = [
            Nota,
            Matricula,
            ProfesorMateria,
            Lapso,
            Estudiante,
            Profesor,
            Bachiller,
        ]

        self.eliminar_usuarios_profesores()

        for modelo in modelos_a_limpiar:
            count, _ = modelo.objects.all().delete()
            if count > 0:
                self.stdout.write(
                    f"✓ Eliminados {count} registros de {modelo.__name__}"
                )

            connection.cursor().execute(
                f"UPDATE SQLITE_SEQUENCE SET seq=0 WHERE name='{modelo._meta.db_table}';",
            )

    def limpiar_por_tipo(self, nombre_modelo: str):
        modelos = {
            "profesores": Profesor,
            "estudiantes": Estudiante,
            "lapsos": Lapso,
            "profesores-materias": ProfesorMateria,
            "matriculas": Matricula,
            "notas": Nota,
            "bachilleres": Bachiller,
        }

        if nombre_modelo in modelos:
            modelo = modelos[nombre_modelo]

            if nombre_modelo == "profesores":
                self.eliminar_usuarios_profesores()

            cantidad, _ = modelo.objects.all().delete()

            if cantidad > 0:
                self.stdout.write(
                    f"✓ Eliminados {cantidad} registros de {modelo.__name__}"
                )

            connection.cursor().execute(
                f"UPDATE SQLITE_SEQUENCE SET seq=0 WHERE name='{modelo._meta.db_table}';",
            )
        else:
            self.stdout.write(
                self.style.ERROR("No se encontró un modelo para el tipo indicado.")
            )
