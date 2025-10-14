from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Año(models.Model):
    numero_año = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Número"
    )
    nombre_año = models.CharField(max_length=100, verbose_name="Nombre")
    nombre_año_corto = models.CharField(max_length=20, verbose_name="Nombre corto")
    fecha_creacion = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de creación"
    )

    class Meta:
        db_table = "años"
        verbose_name_plural = "Años"

    def __str__(self):
        return self.nombre_año


class Seccion(models.Model):
    """Representa las secciones A, B, C, etc. de cada año"""

    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    letra_seccion = models.CharField(max_length=1)  # A, B, C, etc.
    nombre_seccion = models.CharField(max_length=100)  # Ej: "Primero A"
    capacidad_maxima = models.IntegerField(default=30)
    tutor = models.ForeignKey(
        "Profesor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secciones_tutor",
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "secciones"
        unique_together = ["año", "letra_seccion"]
        verbose_name_plural = "Secciones"

    def __str__(self):
        return f"{self.año.nombre_año} - Sección {self.letra_seccion}"


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
    telefono = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Teléfono"
    )
    fecha_ingreso = models.DateField(
        default=timezone.now, verbose_name="Fecha de ingreso"
    )
    esta_activo = models.BooleanField(default=True, verbose_name="Activo")
    usuario = models.OneToOneField(
        "usuarios.User", on_delete=models.CASCADE, verbose_name="Usuario"
    )

    class Meta:
        db_table = "profesores"
        verbose_name_plural = "Profesores"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Estudiante(models.Model):
    ESTADOS = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("graduado", "Graduado"),
    ]

    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    fecha_matricula = models.DateField(
        default=timezone.now, verbose_name="Fecha de matricula"
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default="activo")

    class Meta:
        db_table = "estudiantes"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Lapso(models.Model):
    numero_lapso = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name="Número",
    )
    nombre_lapso = models.CharField(max_length=100, verbose_name="Nombre")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de fin")

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
        verbose_name = "año y materia"
        verbose_name_plural = "Años y materias"

    def __str__(self):
        return f"{self.año.nombre_año} - {self.materia.nombre_materia}"


class ProfesorMateria(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    seccion = models.ForeignKey(
        Seccion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Si no se especifica, se indicará que el profesor imparte la materia a todas las secciones del año",
    )
    es_profesor_principal = models.BooleanField(default=False)

    class Meta:
        db_table = "profesores_materias"
        unique_together = ["profesor", "materia", "año", "seccion"]
        verbose_name_plural = "Profesores materias"

    def __str__(self):
        tipo = "Principal" if self.es_profesor_principal else "Secundario"
        seccion_info = (
            f" - {self.seccion}" if self.seccion else " - Todas las secciones"
        )
        return f"{self.profesor} - {self.materia}{seccion_info} ({tipo})"


class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    año = models.ForeignKey(Año, on_delete=models.CASCADE)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE)
    fecha_matricula = models.DateField(default=timezone.now)

    class Meta:
        db_table = "matriculas"
        unique_together = ["estudiante", "año"]

    def __str__(self):
        return f"{self.estudiante} - {self.año} - {self.seccion.letra_seccion}"


class Nota(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    lapso = models.ForeignKey(Lapso, on_delete=models.CASCADE)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE)
    valor_nota = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    fecha_nota = models.DateField(default=timezone.now)
    comentarios = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "notas"
        unique_together = ["estudiante", "materia", "lapso"]
        verbose_name_plural = "Notas"

    def __str__(self):
        return f"{self.estudiante} - {self.materia} - {self.valor_nota}"
