from typing import Any
from estudios.management.commands import BaseComandos
from estudios.modelos.parametros import Lapso
from datetime import date


class ArgumentosParametrosMixin(BaseComandos):
    def add_arguments(self, parser):
        parser.add_argument(
            "--año",
            type=int,
            help="Número del año objetivo, al cual asignar datos específicos",
        )

        parser.add_argument(
            "--lapsos",
            action="store_true",
            help="Crear solo lapsos",
        )

        parser.add_argument(
            "--lapsos-año",
            type=int,
            # año actual
            default=date.today().year,
            help="El año (fecha) para crear los lapsos",
        )

        parser.add_argument(
            "--lapso",
            type=int,
            help="Indicar el id del lapso para las acciones que lo requieran",
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

    def handle_gestion(self, options: "dict[str, Any]"):
        if self.si_accion("lapsos"):
            self.crear_lapsos(options["lapsos_año"])
