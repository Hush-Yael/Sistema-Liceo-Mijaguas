from django.contrib import admin
from .models import (
    Año,
    Materia,
    Profesor,
    Estudiante,
    Lapso,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Nota,
)


@admin.register(Año)
class AñoAdmin(admin.ModelAdmin):
    list_display = ["numero_año", "nombre_año", "fecha_creacion"]
    list_filter = ["numero_año"]
    search_fields = ["nombre_año", "numero_año"]


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ["nombre_materia", "fecha_creacion"]
    search_fields = ["nombre_materia"]


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = [
        "nombres",
        "apellidos",
        "esta_activo",
    ]
    list_filter = ["esta_activo"]
    search_fields = ["nombres", "apellidos"]


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = [
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "estado",
    ]
    list_filter = ["estado"]
    search_fields = ["nombres", "apellidos"]


@admin.register(Lapso)
class LapsoAdmin(admin.ModelAdmin):
    list_display = ["año", "numero_lapso", "nombre_lapso", "fecha_inicio", "fecha_fin"]
    list_filter = ["año"]
    search_fields = ["nombre_lapso"]


@admin.register(AñoMateria)
class AñoMateriaAdmin(admin.ModelAdmin):
    list_display = ["año", "materia", "horas_semanales"]
    list_filter = ["año", "materia"]
    search_fields = ["materia__nombre_materia"]


@admin.register(ProfesorMateria)
class ProfesorMateriaAdmin(admin.ModelAdmin):
    list_display = ["profesor", "materia", "año", "es_profesor_principal"]
    list_filter = ["año", "es_profesor_principal"]
    search_fields = ["profesor__nombre", "materia__nombre_materia"]


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ["estudiante", "año", "fecha_matricula"]
    list_filter = ["año"]
    search_fields = ["estudiante__nombre", "estudiante__apellido"]


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = [
        "estudiante",
        "materia",
        "lapso",
        "valor_nota",
        "fecha_nota",
    ]
    list_filter = ["lapso", "materia"]
    search_fields = ["estudiante__nombre", "materia__nombre_materia"]
