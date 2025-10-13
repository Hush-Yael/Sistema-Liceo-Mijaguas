from django.contrib import admin
from .models import (
    Seccion,
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


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = [
        "nombre_seccion",
        "año",
        "letra_seccion",
        "tutor",
        "capacidad_maxima",
    ]
    list_filter = ["año", "letra_seccion"]
    search_fields = ["nombre_seccion", "letra_seccion"]
    autocomplete_fields = ["tutor"]


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
    autocomplete_fields = ["usuario"]


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
    autocomplete_fields = ["materia"]


@admin.register(ProfesorMateria)
class ProfesorMateriaAdmin(admin.ModelAdmin):
    list_display = ["profesor", "materia", "año", "seccion", "es_profesor_principal"]
    list_filter = ["año", "es_profesor_principal", "seccion"]
    search_fields = ["profesor__nombre", "materia__nombre_materia"]
    autocomplete_fields = ["profesor", "materia", "año", "seccion"]


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ["estudiante", "año", "seccion", "fecha_matricula"]
    list_filter = ["año", "seccion"]
    search_fields = ["estudiante__nombre", "estudiante__apellido"]
    autocomplete_fields = ["estudiante", "seccion"]


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = [
        "estudiante",
        "materia",
        "lapso",
        "seccion",
        "valor_nota",
        "fecha_nota",
    ]
    list_filter = ["lapso", "materia", "seccion"]
    search_fields = ["estudiante__nombre", "materia__nombre_materia"]
    autocomplete_fields = ["estudiante", "materia", "lapso", "seccion"]
