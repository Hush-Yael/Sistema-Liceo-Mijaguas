import random
from typing import Any
from app.util import nc
from estudios.management.commands import BaseComandos
from estudios.modelos.gestion.calificaciones import (
    Nota,
    Tarea,
    TareaProfesorMateria,
    TipoTarea,
)
from estudios.modelos.parametros import Materia
from estudios.modelos.gestion.personas import (
    Estudiante,
    Matricula,
    Profesor,
    ProfesorMateria,
)


class ArgumentosCalificacionesMixin(BaseComandos):
    def añadir_argumentos_gestion(self, parser):
        parser.add_argument(
            "--notas",
            action="store_true",
            help="Crear solo notas",
        )

        parser.add_argument(
            "--tareas",
            type=int,
            help="Crear solo tareas",
        )

    def handle_calificaciones(self, options: "dict[str, Any]") -> None:
        if self.si_accion("tareas"):
            if not Profesor.objects.exists():
                return self.stdout.write(
                    self.style.ERROR("Crear tareas: No se han añadido profesores")
                )
            elif not ProfesorMateria.objects.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Crear tareas: No se han asignado materias a profesores"
                    )
                )

            elif not TipoTarea.objects.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Crear tareas: No se han creado los tipos de tareas"
                    )
                )

            self.crear_tareas(options["tareas"], options["lapso"])

        if self.si_accion("notas"):
            if not Materia.objects.exists():
                return self.stdout.write(
                    self.style.ERROR("Crear notas: No se han añadido materias")
                )
            elif not ProfesorMateria.objects.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Crear notas: No se han asignado materias a profesores"
                    )
                )
            elif not Tarea.objects.exists():
                return self.stdout.write(
                    self.style.ERROR("Crear notas: No se han creado tareas")
                )

            elif not TareaProfesorMateria.objects.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Crear notas: No se han asignado tareas a profesores"
                    )
                )

            elif not Estudiante.objects.exists():
                return self.stdout.write(
                    self.style.ERROR("Crear notas: No se han añadido estudiantes")
                )

            elif not Matricula.objects.exists():
                return self.stdout.write(
                    self.style.ERROR("Crear notas: No se han matriculado estudiantes")
                )

            self.crear_notas(options["lapso"], options["seccion"])

    def crear_notas(
        self,
        lapso_objetivo: int,
        seccion_objetivo: "int | None" = None,
    ):
        self.stdout.write("Creando notas...")

        if (lapso := self.obtener_lapso_objetivo(lapso_objetivo)) is None:
            return self.stdout.write(
                self.style.ERROR("Crear notas: No se escogió un lapso")
            )

        matriculas = Matricula.objects.filter(**{nc(Matricula.lapso): lapso}).all()

        if not matriculas.count():
            return self.stdout.write(
                self.style.ERROR(
                    "Crear notas: No se han matriculado estudiantes con el lapso proporcionado"
                )
            )

        tpms = TareaProfesorMateria.objects.filter(tarea__lapso=lapso).all()

        if not tpms.count():
            return self.stdout.write(
                self.style.ERROR(
                    "Crear notas: No se han asignado tareas al lapso proporcionado"
                )
            )

        todos = input(
            "Desea asignar los notas a los estudiantes de todas las secciones? (s/n): "
        ).lower()

        # asignar notas a los estudiantes de una sección específica
        if todos != "s":
            if (seccion := self.obtener_seccion_objetivo(seccion_objetivo)) is None:
                return self.stdout.write(
                    self.style.ERROR("Crear notas: No se escogió una sección")
                )

            matriculas = matriculas.filter(**{nc(Matricula.seccion): seccion})

            if not matriculas.count():
                return self.stdout.write(
                    self.style.ERROR(
                        "Crear notas: No se han matriculado estudiantes con la sección proporcionada"
                    )
                )

            tpms = tpms.filter(profesormateria__seccion=seccion)

            if not tpms.count():
                return self.stdout.write(
                    self.style.ERROR(
                        "Crear notas: No se han asignado tareas a la sección proporcionada"
                    )
                )

        notas_creadas = 0

        for tpm in tpms:
            notas = Nota.objects.bulk_create(
                tuple(
                    Nota(
                        **{
                            nc(Nota.matricula): matricula,
                            nc(Nota.tarea_profesormateria): tpm,
                            nc(Nota.valor): round(random.uniform(1.0, 9.0), 1)
                            if random.random() < 0.1
                            else round(random.uniform(10.0, 20.0), 1),
                        }
                    )
                    for matricula in matriculas
                )
            )

            notas_creadas += len(notas)

        self.stdout.write(
            f"✓ {notas_creadas} notas creadas para {matriculas.count()} estudiantes"
        )

    def crear_tareas(self, cantidad_tareas: int, lapso_objetivo: int):
        self.stdout.write(f"Creando {cantidad_tareas} tareas para cada profesor...")

        lapso = self.obtener_lapso_objetivo(lapso_objetivo)

        if lapso is None:
            return self.stdout.write(
                self.style.ERROR("Crear tareas: No se indicó un lapso")
            )

        profesores = Profesor.objects.filter(**{nc(Profesor.activo): True}).all()

        tipos_tareas_ids = tuple(TipoTarea.objects.values_list("id", flat=True))

        for profesor in profesores:
            pms_ids = tuple(
                ProfesorMateria.objects.values_list("id", flat=True).filter(
                    **{nc(ProfesorMateria.profesor): profesor}
                )
            )

            if not pms_ids:
                self.stdout.write(
                    self.style.ERROR(
                        f"Crear tareas: No se han asignado materias a {profesor}"
                    )
                )
                continue

            tareas = Tarea.objects.bulk_create(
                Tarea(
                    **{
                        nc(Tarea.profesor): profesor,
                        f"{nc(Tarea.tipo)}_id": self.faker.random_element(
                            tipos_tareas_ids
                        ),
                        nc(Tarea.lapso): lapso,
                    }
                )
                for _ in range(cantidad_tareas)
            )

            TareaProfesorMateria.objects.bulk_create(
                TareaProfesorMateria(
                    tarea=tarea, profesormateria_id=self.faker.random_element(pms_ids)
                )
                for tarea in tareas
            )

        self.stdout.write(
            f"✓ Total tareas creadas: {cantidad_tareas * profesores.count()}"
        )
