from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError
from django.utils import timezone


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


class Seccion(models.Model):
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    letra = models.CharField(max_length=1)
    nombre = models.CharField(max_length=100)
    capacidad = models.IntegerField(default=30)
    vocero = models.ForeignKey(
        "Estudiante",
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
        "usuarios.User",
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

    class Meta:
        ordering = ["apellidos", "nombres"]
        db_table = "estudiantes"

    def __str__(self):
        return f"{self.cedula} - {self.nombres} {self.apellidos}"


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


class Matricula(models.Model):
    ESTADOS = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE)
    fecha_añadida = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADOS, default="activo")
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
