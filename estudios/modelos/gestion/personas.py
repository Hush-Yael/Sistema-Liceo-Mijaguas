from django.db import models
from django.core.validators import MinValueValidator
from django.forms import ValidationError
from django.utils import timezone
from app import settings
from estudios.modelos.parametros import Seccion, Materia, Lapso


class Profesor(models.Model):
    cedula = models.IntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        primary_key=True,
        verbose_name="cédula",
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="teléfono"
    )
    fecha_ingreso = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de ingreso"
    )
    esta_activo = models.BooleanField(default=True, verbose_name="está activo")
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        db_table = "profesores"
        verbose_name_plural = "profesores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Estudiante(models.Model):
    cedula = models.IntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        verbose_name="cédula",
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(verbose_name="fecha de nacimiento")
    fecha_ingreso = models.DateField(
        default=timezone.now, verbose_name="fecha de ingreso"
    )

    @property
    def edad(self):
        return abs(timezone.now().year - self.fecha_nacimiento.year)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    class Meta:
        ordering = ["apellidos", "nombres"]
        db_table = "estudiantes"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class ProfesorMateria(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    seccion = models.ForeignKey(
        Seccion,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "profesores_materias"
        unique_together = ["profesor", "materia", "seccion"]
        verbose_name = "materia impartida por profesor"
        verbose_name_plural = "materias impartidas por profesores"

    def unique_error_message(self, model_class, unique_check, *args, **kwargs):
        if model_class is type(self) and unique_check == (
            "profesor",
            "materia",
            "seccion",
        ):
            raise ValidationError(
                "El profesor ya imparte la materia en la sección seleccionada",
                code="unique",
            )
        else:
            return super().unique_error_message(model_class, unique_check)

    def __str__(self):
        seccion_info = (
            f" - {self.seccion}" if self.seccion else " - Todas las secciones"
        )
        return f"{self.profesor} - {self.materia}{seccion_info}"


class MatriculaEstados(models.TextChoices):
    ACTIVO = "A", "Activo"
    INACTIVO = "I", "Inactivo"


class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE)
    fecha_añadida = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=10, choices=MatriculaEstados.choices, default=MatriculaEstados.ACTIVO
    )
    lapso = models.ForeignKey(
        Lapso,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "matriculas"
        unique_together = ["estudiante", "lapso"]

    def unique_error_message(self, model_class, unique_check, *args, **kwargs):
        if model_class is type(self) and unique_check == ("estudiante", "lapso"):
            raise ValidationError(
                "El estudiante ya se encuentra matriculado en el lapso actual",
                code="unique",
            )
        else:
            return super().unique_error_message(model_class, unique_check)

    # Imponer la validación de la cantidad de estudiantes de la sección al matricular
    def clean(self):
        super().clean()

        if not self.pk and hasattr(self, "seccion"):
            matriculas_existentes = Matricula.objects.filter(
                seccion=self.seccion, lapso=self.lapso
            )

            cantidad_matriculas = matriculas_existentes.count()
            capacidad_maxima = self.seccion.capacidad

            if cantidad_matriculas >= capacidad_maxima:
                raise ValidationError(
                    f"La sección {self.seccion.nombre} está llena (capacidad: {self.seccion.capacidad} alumnos)"
                )

    def save(self, *args, **kwargs):
        # Ejecutar validación
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.estudiante} - {self.seccion} ({self.lapso.nombre})"


class Bachiller(models.Model):
    promocion = models.CharField(max_length=50, verbose_name="promoción")
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE)
    fecha_graduacion = models.DateField(
        default=timezone.now, verbose_name="fecha de graduación"
    )

    class Meta:
        db_table = "bachilleres"
        verbose_name = "bachiller"
        verbose_name_plural = "bachilleres"

    def __str__(self):
        return f"Bachiller {self.estudiante} - promo. {self.promocion} ({self.fecha_graduacion.strftime('%d/%m/%Y')})"
