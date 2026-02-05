from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.forms import ValidationError
from django.utils import timezone


def obtener_lapso_actual():
    return Lapso.objects.last()


class Año(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        error_messages={"unique": "Ya existe otro año con ese nombre."},
    )
    nombre_corto = models.CharField(
        max_length=20,
        verbose_name="nombre corto",
        unique=True,
        error_messages={"unique": "Ya existe otro año con ese nombre corto."},
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de creación"
    )

    class Meta:
        db_table = "años"

    def __str__(self):
        return self.nombre


class Lapso(models.Model):
    numero = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="número",
    )
    nombre = models.CharField(max_length=50, unique=True)
    fecha_inicio = models.DateField(verbose_name="fecha de inicio")
    fecha_fin = models.DateField(verbose_name="fecha de fin")

    class Meta:
        db_table = "lapsos"

    def __str__(self):
        return f"{self.nombre} - {self.fecha_inicio} / {self.fecha_fin}"


class Seccion(models.Model):
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    letra = models.CharField(
        max_length=1,
        validators=[
            RegexValidator("^[a-zA-Z]$", "El valor debe ser una letra del alfabeto.")
        ],
    )
    nombre = models.CharField(max_length=100)
    capacidad = models.IntegerField(default=30)
    vocero = models.ForeignKey(
        "estudios.Estudiante",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secciones_vocero",
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de creación"
    )

    class Meta:
        ordering = ["año", "letra"]
        db_table = "secciones"
        unique_together = ["año", "letra"]
        verbose_name_plural = "secciones"

    def unique_error_message(self, model_class, unique_check, *args, **kwargs):
        if model_class is type(self) and unique_check == ("año", "letra"):
            raise ValidationError(
                "Ya existe una sección con el año y letra indicados", code="unique"
            )
        else:
            return super().unique_error_message(model_class, unique_check)

    def __str__(self):
        return f"{self.año.nombre} - Sección {self.letra}"

    def clean_letra(self):
        super().clean()

        if isinstance(self.letra, str) and self.letra:
            self.letra = self.letra.upper()


class Materia(models.Model):
    nombre = models.CharField(
        max_length=200,
        unique=True,
        error_messages={"unique": "Ya existe una materia con ese nombre."},
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de creación"
    )

    class Meta:
        ordering = ["nombre"]
        db_table = "materias"

    def __str__(self):
        return f"{self.nombre}"


class AñoMateria(models.Model):
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)

    class Meta:
        db_table = "años_materias"
        unique_together = ["año", "materia"]
        verbose_name = "materia asignada a año"
        verbose_name_plural = "asignaciones de años a materias"

    def unique_error_message(self, model_class, unique_check, *args, **kwargs):
        if model_class is type(self) and unique_check == ("año", "materia"):
            raise ValidationError(
                "La materia ya está asignada en el año seleccionado",
                code="unique",
            )
        else:
            return super().unique_error_message(model_class, unique_check)

    def __str__(self):
        return f"{self.año.nombre} - {self.materia.nombre}"
