from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from estudios.modelos.gestion.personas import (
    Matricula,
    Profesor,
    ProfesorMateria,
    Estudiante,
    Seccion,
)
from estudios.modelos.parametros import Lapso, Materia


class TipoTarea(models.Model):
    nombre = models.CharField(max_length=64, unique=True)
    descripcion = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        db_table = "tipos_tareas"
        verbose_name = "tipo de tarea"
        verbose_name_plural = "tipos de tareas"

    def __str__(self):
        return self.nombre


class Tarea(models.Model):
    nombre = models.CharField(max_length=64)
    descripcion = models.TextField()
    fecha_añadida = models.DateTimeField(default=timezone.now)
    tipo = models.ForeignKey(TipoTarea, on_delete=models.CASCADE)
    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tareas_profesor",
    )

    class Meta:
        db_table = "tareas"

    def __str__(self):
        return f"{self.nombre} - {self.profesor}"


class TareaProfesorMateria(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE)
    profesormateria = models.ForeignKey(ProfesorMateria, on_delete=models.CASCADE)

    class Meta:
        db_table = "tareas_profesormateria"
        unique_together = ["tarea", "profesormateria"]
        verbose_name = "asignación tarea - materia"
        verbose_name_plural = "asignaciones tareas - materias"

    def __str__(self):
        return f"{self.tarea.nombre} - {self.profesormateria.materia.nombre} ({self.profesormateria.seccion.nombre})"


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    valor = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    fecha = models.DateTimeField(default=timezone.now)
    tarea_profesormateria = models.ForeignKey(
        TareaProfesorMateria, on_delete=models.CASCADE
    )

    class Meta:
        db_table = "notas"

    def __str__(self):
        tarea: TareaProfesorMateria = self.tarea_profesormateria
        materia_impartida: ProfesorMateria = tarea.profesormateria
        materia: Materia = materia_impartida.materia

        return f"{self.estudiante} - {self.seccion.nombre} - {materia.nombre} - {self.valor}"

    @property
    def estudiante(self) -> Estudiante:
        matricula: Matricula = self.matricula
        return matricula.estudiante

    @estudiante.setter
    def estudiante(self, estudiante):
        self._estudiante = estudiante

    @property
    def seccion(self) -> Seccion:
        matricula: Matricula = self.matricula
        return matricula.seccion

    @seccion.setter
    def seccion(self, seccion):
        self._seccion = seccion

    @property
    def lapso(self) -> Lapso:
        matricula: Matricula = self.matricula
        return matricula.lapso

    @lapso.setter
    def lapso(self, lapso):
        self._lapso = lapso
