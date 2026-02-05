from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from estudios.modelos.gestion.personas import (
    Matricula,
)
from estudios.modelos.parametros import Materia


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    valor = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    fecha = models.DateTimeField(default=timezone.now)

    @property
    def estudiante(self):
        return self.matricula.estudiante

    @estudiante.setter
    def estudiante(self, estudiante):
        self._estudiante = estudiante

    @property
    def seccion(self):
        return self.matricula.seccion

    @seccion.setter
    def seccion(self, seccion):
        self._seccion = seccion

    @property
    def lapso(self):
        return self.matricula.lapso

    @lapso.setter
    def lapso(self, lapso):
        self._lapso = lapso

    class Meta:
        db_table = "notas"

    def __str__(self):
        return (
            f"{self.estudiante} - {self.seccion.nombre} - {self.materia} - {self.valor}"
        )
