from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class AñoAcademico(models.Model):
    numero_año = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Número"
    )
    nombre_año = models.CharField(max_length=100, verbose_name="Nombre")
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de creación"
    )

    class Meta:
        db_table = "años"
        verbose_name_plural = "Años académicos"

    def __str__(self):
        return self.nombre_año


class Materia(models.Model):
    nombre_materia = models.CharField(
        max_length=200, unique=True, verbose_name="Nombre"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de creación"
    )

    class Meta:
        db_table = "materias"

    def __str__(self):
        return f"{self.nombre_materia}"


class Profesor(models.Model):
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    correo_electronico = models.EmailField(unique=True, verbose_name="Correo")
    telefono = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Teléfono"
    )
    fecha_ingreso = models.DateField(
        default=timezone.now, verbose_name="Fecha de ingreso"
    )
    esta_activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "profesores"
        verbose_name_plural = "Profesores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Estudiante(models.Model):
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    correo_electronico = models.EmailField(blank=True, null=True, verbose_name="Correo")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    fecha_matricula = models.DateField(
        default=timezone.now, verbose_name="Fecha de matricula"
    )
    esta_activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "estudiantes"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class LapsoAcademico(models.Model):
    año = models.ForeignKey(AñoAcademico, on_delete=models.CASCADE, verbose_name="Año")
    numero_lapso = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name="Número",
    )
    nombre_lapso = models.CharField(max_length=100, verbose_name="Nombre")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de fin")

    class Meta:
        db_table = "lapsos"
        unique_together = ["año", "numero_lapso"]
        verbose_name = "lapso académico"
        verbose_name_plural = "Lapsos académicos"

    def __str__(self):
        return f"{self.año.nombre_año} - {self.nombre_lapso}"


class AñoMateria(models.Model):
    año = models.ForeignKey(AñoAcademico, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    horas_semanales = models.IntegerField(default=4)

    class Meta:
        db_table = "años_materias"
        unique_together = ["año", "materia"]
        verbose_name = "año y materia"
        verbose_name_plural = "Años y materias"

    def __str__(self):
        return f"{self.año.nombre_año} - {self.materia.nombre_materia}"


class ProfesorMateria(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    año = models.ForeignKey(AñoAcademico, on_delete=models.CASCADE)
    es_profesor_principal = models.BooleanField(default=False)

    class Meta:
        db_table = "profesores_materias"
        unique_together = ["profesor", "materia", "año"]
        verbose_name = "profesor y materia"
        verbose_name_plural = "Profesores y materias"

    def __str__(self):
        tipo = "Principal" if self.es_profesor_principal else "Secundario"
        return f"{self.profesor} - {self.materia} ({tipo})"


class Matricula(models.Model):
    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("graduado", "Graduado"),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    año = models.ForeignKey(AñoAcademico, on_delete=models.CASCADE)
    fecha_matricula = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="activo")

    class Meta:
        db_table = "matriculas"
        unique_together = ["estudiante", "año"]

    def __str__(self):
        return f"{self.estudiante} - {self.año}"


class Calificacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    lapso = models.ForeignKey(LapsoAcademico, on_delete=models.CASCADE)
    valor_calificacion = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    fecha_calificacion = models.DateField(default=timezone.now)
    comentarios = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "calificaciones"
        unique_together = ["estudiante", "materia", "lapso"]
        verbose_name_plural = "Calificaciones"

    def __str__(self):
        return f"{self.estudiante} - {self.materia} - {self.valor_calificacion}"
