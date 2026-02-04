from estudios.management.commands.poblar_datos_ejemplo import BaseComandos
from estudios.modelos.parametros import Lapso
from datetime import date


class ArgumentosParametrosMixin(BaseComandos):
    def add_arguments(self, parser):
        parser.add_argument(
            "--profesores",
            action="store_true",
            help="Crear solo profesores",
        )

        parser.add_argument(
            "--estudiantes",
            action="store_true",
            help="Crear solo estudiantes",
        )

        parser.add_argument(
            "--matriculas",
            action="store_true",
            help="Crear solo matrículas",
        )

        parser.add_argument(
            "--notas",
            action="store_true",
            help="Crear solo notas",
        )

        parser.add_argument(
            "--cantidad-notas",
            type=int,
            default=1,
            help="Cantidad de notas a crear (por defecto: 1)",
        )

        parser.add_argument(
            "--cantidad-estudiantes",
            type=int,
            default=20,
            help="Cantidad de estudiantes a crear (por defecto: 20)",
        )

        parser.add_argument(
            "--cantidad-profesores",
            type=int,
            default=8,
            help="Cantidad de profesores a crear (por defecto: 8)",
        )

    def crear_lapsos(self, año):
        lapsos_data = [
            (1, f"{año}-I", date(año, 1, 9), date(año, 3, 31)),
            (
                2,
                f"{año}-II",
                date(año, 4, 1),
                date(año, 5, 28),
            ),
            (
                3,
                f"{año}-III",
                date(año, 5, 29),
                date(año, 6, 30),
            ),
        ]

        lapsos_creados = 0
        for num, nombre, inicio, fin in lapsos_data:
            _, creado = Lapso.objects.get_or_create(
                numero=num,
                defaults={
                    "nombre": nombre,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                },
            )
            if creado:
                lapsos_creados += 1
                self.stdout.write(f"✓ Creado lapso: {nombre}")

        self.stdout.write(f"✓ Total lapsos creados: {lapsos_creados}")

    def handle(self, *args, **options):
        if self.si_accion("lapsos"):
            self.crear_lapsos(options["lapsos_año"])
