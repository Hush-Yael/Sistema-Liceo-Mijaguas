from estudios.management.commands import BaseComandos
from estudios.management.commands.gestion import ArgumentosGestionMixin
from estudios.management.commands.parametros import ArgumentosParametrosMixin
from estudios.modelos.gestion.personas import (
    Bachiller,
    Profesor,
    Estudiante,
    ProfesorMateria,
    Matricula,
)
from estudios.modelos.gestion.calificaciones import Nota
from estudios.modelos.parametros import (
    Lapso,
)
from django.db import connection


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
        self.año_id = options.get("año", False)
        self.limpiar_todo = options.get("limpiar_todo", False)
        self.limpiar_modelo = options.get("limpiar", False)
        self.hacer_todo = options.get("todo", False)

        if self.limpiar_todo:
            self.limpiar_datos()
        elif self.limpiar_modelo is not None:
            self.limpiar_por_tipo(self.limpiar_modelo)

        # Determinar qué acciones ejecutar
        self.acciones = {
            "profesores": options.get("profesores", False),
            "estudiantes": options.get("estudiantes", False),
            "lapsos": options.get("lapsos", False),
            "asignar_materias": options.get("asignar_materias", False),
            "matriculas": options.get("matriculas", False),
            "notas": options.get("notas", False),
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

        self.handle_parametros(options)
        self.handle_gestion(options)

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
