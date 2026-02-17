import random
from typing import Any
from estudios.management.commands import BaseComandos
from estudios.modelos.gestion.calificaciones import Nota
from estudios.modelos.parametros import Materia
from estudios.modelos.gestion.personas import Estudiante, Matricula


class ArgumentosCalificacionesMixin(BaseComandos):
    def añadir_argumentos_gestion(self, parser):
        parser.add_argument(
            "--notas",
            type=int,
            help="Crear solo notas",
        )

    def handle_calificaciones(self, options: "dict[str, Any]") -> None:
        if self.si_accion("notas"):
            estudiantes = Estudiante.objects.all()

            if estudiantes.first() is None:
                return self.stdout.write(
                    self.style.ERROR("No se han añadido estudiantes")
                )

            cantidad = options["notas"]
            self.crear_notas(estudiantes, cantidad, options["lapso"])

    def crear_notas(self, estudiantes, cantidad_notas: int, lapso_objetivo: int):
        self.stdout.write("Creando notas por sección...")

        if (año := self.obtener_año_id(self.año_id)) is None or (
            lapso := self.obtener_lapso_objetivo(lapso_objetivo)
        ) is None:
            return

        materias = Materia.objects.all()
        notas_creadas = 0
        no_matriculados = 0

        for estudiante in estudiantes:
            # Obtener la matrícula del estudiante para saber su sección
            try:
                matricula = Matricula.objects.get(
                    estudiante=estudiante,
                    seccion__año=año,
                    lapso=lapso,
                )
            except Matricula.DoesNotExist:
                no_matriculados += 1
                continue

            for materia in materias:
                for _ in range(cantidad_notas):
                    # Generar calificación realista
                    if random.random() < 0.1:  # 10% de probabilidad de nota baja
                        nota = round(random.uniform(1.0, 9.0), 1)
                    else:
                        nota = round(random.uniform(10.0, 20.0), 1)

                    Nota.objects.create(
                        matricula=matricula,
                        materia=materia,
                        valor=nota,
                    )

                    notas_creadas += 1

                    if notas_creadas % 100 == 0:  # Mostrar progreso
                        self.stdout.write(f"✓ Creadas {notas_creadas} notas...")

        if no_matriculados > 0:
            mensaje = f"No se pudieron crear notas para los {no_matriculados} estudiantes, pues no se encontraron matriculados con los parámetros proporcionados."
            self.stdout.write(
                self.style.ERROR(mensaje)
                if notas_creadas < 1
                else self.style.WARNING(mensaje)
            )

        if notas_creadas > 0:
            self.stdout.write(f"✓ Total notas creadas: {notas_creadas}")
