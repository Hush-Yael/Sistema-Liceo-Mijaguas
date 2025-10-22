from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError
from django.utils import timezone


class Año(models.Model):
    numero_año = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="número",
        unique=True,
    )
    nombre_año = models.CharField(max_length=100, verbose_name="nombre", unique=True)
    nombre_año_corto = models.CharField(
        max_length=20, verbose_name="nombre corto", unique=True
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de creación"
    )

    class Meta:
        db_table = "años"
        verbose_name_plural = "Años"

    def __str__(self):
        return self.nombre_año


class Seccion(models.Model):
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    letra_seccion = models.CharField(max_length=1, verbose_name="letra")
    nombre_seccion = models.CharField(max_length=100, verbose_name="nombre")
    capacidad_maxima = models.IntegerField(default=30)
    vocero = models.ForeignKey(
        "Estudiante",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secciones_vocero",
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["año", "letra_seccion"]
        db_table = "secciones"
        unique_together = ["año", "letra_seccion"]
        verbose_name_plural = "Secciones"

    def unique_error_message(self, model_class, unique_check, *args, **kwargs):
        if model_class is type(self) and unique_check == ("año", "letra_seccion"):
            raise ValidationError(
                "Ya existe una sección con el año y letra indicados", code="unique"
            )
        else:
            return super().unique_error_message(model_class, unique_check)

    def __str__(self):
        return f"{self.año.nombre_año} - Sección {self.letra_seccion}"


class Materia(models.Model):
    nombre_materia = models.CharField(
        max_length=200, unique=True, verbose_name="nombre"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="descripción")
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de creación"
    )

    class Meta:
        ordering = ["nombre_materia"]
        db_table = "materias"

    def __str__(self):
        return f"{self.nombre_materia}"


class Profesor(models.Model):
    cedula = models.IntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        primary_key=True,
        verbose_name="cédula",
    )
    nombres = models.CharField(max_length=100, verbose_name="nombres")
    apellidos = models.CharField(max_length=100, verbose_name="apellidos")
    telefono = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="teléfono"
    )
    fecha_ingreso = models.DateTimeField(
        default=timezone.now, verbose_name="fecha de ingreso"
    )
    esta_activo = models.BooleanField(default=True, verbose_name="activo")
    usuario = models.OneToOneField(
        "usuarios.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="usuario",
    )

    class Meta:
        db_table = "profesores"
        verbose_name_plural = "Profesores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Estudiante(models.Model):
    cedula = models.IntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        primary_key=True,
        verbose_name="cédula",
    )
    nombres = models.CharField(max_length=100, verbose_name="nombres")
    apellidos = models.CharField(max_length=100, verbose_name="apellidos")
    fecha_nacimiento = models.DateField(verbose_name="fecha de nacimiento")
    fecha_ingreso = models.DateField(
        default=timezone.now, verbose_name="fecha de matricula"
    )

    class Meta:
        ordering = ["apellidos", "nombres"]
        db_table = "estudiantes"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Lapso(models.Model):
    numero_lapso = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name="número",
    )
    nombre_lapso = models.CharField(max_length=50, verbose_name="nombre", unique=True)
    fecha_inicio = models.DateField(verbose_name="fecha de inicio")
    fecha_fin = models.DateField(verbose_name="fecha de fin")

    class Meta:
        db_table = "lapsos"
        verbose_name = "lapso"
        verbose_name_plural = "Lapsos"

    def __str__(self):
        return f"{self.nombre_lapso} - {self.fecha_inicio} / {self.fecha_fin}"


class AñoMateria(models.Model):
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)

    class Meta:
        db_table = "años_materias"
        unique_together = ["año", "materia"]
        verbose_name = "materia asignada a año"
        verbose_name_plural = "Materias asignadas por años"

    def unique_error_message(self, model_class, unique_check, *args, **kwargs):
        if model_class is type(self) and unique_check == ("año", "materia"):
            raise ValidationError(
                "La materia ya está asignada en el año seleccionado",
                code="unique",
            )
        else:
            return super().unique_error_message(model_class, unique_check)

    def __str__(self):
        return f"{self.año.nombre_año} - {self.materia.nombre_materia}"


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
        verbose_name_plural = "Materias impartidas por profesores"

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
    fecha_matricula = models.DateTimeField(default=timezone.now)
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
        return f"{self.estudiante} - {self.seccion} ({self.lapso.nombre_lapso})"


class Bachiller(models.Model):
    promocion = models.CharField(max_length=50, verbose_name="promoción")
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE)
    fecha_graduacion = models.DateField(default=timezone.now)

    class Meta:
        db_table = "bachilleres"
        verbose_name = "bachiller"
        verbose_name_plural = "Bachilleres"

    def __str__(self):
        return f"Bachiller {self.estudiante} - promo. {self.promocion} ({self.fecha_graduacion.strftime('%d/%m/%Y')})"


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    valor_nota = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    fecha_nota = models.DateTimeField(default=timezone.now)
    comentarios = models.TextField(blank=True, null=True)

    @property
    def estudiante(self):
        return self.matricula.estudiante

    @property
    def seccion(self):
        return self.matricula.seccion

    @property
    def lapso(self):
        return self.matricula.lapso

    class Meta:
        db_table = "notas"
        verbose_name_plural = "Notas"

    def __str__(self):
        return f"{self.estudiante} - {self.seccion.nombre_seccion} - {self.materia} - {self.valor_nota}"
