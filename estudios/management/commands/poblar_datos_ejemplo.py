import argparse
from app import settings
from estudios.management.commands import BaseComandos, obtener_todos_los_modelos
from estudios.management.commands.calificaciones import ArgumentosCalificacionesMixin
from estudios.management.commands.parametros import ArgumentosParametrosMixin
from estudios.management.commands.personas import ArgumentosPersonasMixin
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


class GuardarPresencia(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest + "_presente", True)


class Command(
    ArgumentosParametrosMixin,
    ArgumentosPersonasMixin,
    ArgumentosCalificacionesMixin,
    BaseComandos,
):
    help = "LLena la base de datos con datos de ejemplo usando Faker"

    def add_arguments(self, parser):
        super().añadir_argumentos_parametros(parser)
        super().añadir_argumentos_personas(parser)
        super().añadir_argumentos_gestion(parser)

        parser.add_argument(
            "--limpiar-todo",
            action="store_true",
            help="Eliminar todos los datos de ejemplo existentes",
        )

        parser.add_argument(
            "--limpiar",
            type=str,
            nargs="?",
            action=GuardarPresencia,
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
        self.modelo_a_limpiar = options["limpiar"]
        hay_modelo_a_limpiar = options.get("limpiar_presente", False)
        self.hacer_todo = options["todo"]

        if self.limpiar_todo:
            self.limpiar_datos()
        elif hay_modelo_a_limpiar:
            self.limpiar_por_tipo(
                self.modelo_a_limpiar if self.modelo_a_limpiar != "-" else ""
            )

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
            and not hay_modelo_a_limpiar
            and not self.hacer_todo
            and not any(self.acciones.values())
        ):
            return self.stdout.write(
                self.style.ERROR("No se especificaron acciones a ejecutar.")
            )

        self.handle_parametros(options)
        self.handle_personas(options)
        self.handle_calificaciones(options)

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
        modelos = obtener_todos_los_modelos()

        # Mostrar los nombres de los modelos en consola para escoger
        if not nombre_modelo:
            self.stdout.write(
                "No se proporcionó el nombre específico de un modelo. Escoge uno:"
            )

            for i in range(len(modelos)):
                self.stdout.write(f"{i}: {modelos[i].__name__}")

            n_modelo = input("Presiona ENTER para cancelar:")

            if not n_modelo.isdigit():
                return self.stdout.write(
                    self.style.ERROR("No se escogió una opción válida.")
                )

            n_modelo = int(n_modelo)

            if n_modelo < 0 or n_modelo >= len(modelos):
                return self.stdout.write(
                    self.style.ERROR("No se escogió una opcion valida.")
                )
            else:
                modelo = modelos[n_modelo]
        else:
            nombre_modelo = nombre_modelo.lower()
            modelo = next(
                (
                    modelo
                    for modelo in modelos
                    if modelo.__name__.lower() == nombre_modelo
                ),
                None,
            )

            if modelo is None:
                return self.stdout.write(
                    self.style.ERROR("No se encontró un modelo con el nombre indicado.")
                )

        if modelo.__name__ == Profesor.__name__:
            self.eliminar_usuarios_profesores()

        cantidad, _ = modelo.objects.all().delete()

        if cantidad > 0:
            self.stdout.write(f"✓ Eliminados {cantidad} registros de {modelo.__name__}")

        if settings.DEBUG:
            connection.cursor().execute(
                f"UPDATE SQLITE_SEQUENCE SET seq=0 WHERE name='{modelo._meta.db_table}';",
            )
