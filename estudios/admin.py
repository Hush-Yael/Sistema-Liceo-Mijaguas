from django.contrib import admin
from unfold.admin import ModelAdmin
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
class AñoAdmin(ModelAdmin):
    list_display = ["numero_año", "nombre_año", "fecha_creacion"]
    list_filter = ["numero_año"]
    search_fields = ["nombre_año", "numero_año"]
    readonly_fields = ["fecha_creacion"]


@admin.register(Seccion)
class SeccionAdmin(ModelAdmin):
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
    readonly_fields = ["fecha_creacion"]


@admin.register(Materia)
class MateriaAdmin(ModelAdmin):
    list_display = ["nombre_materia", "fecha_creacion"]
    search_fields = ["nombre_materia"]
    readonly_fields = ["fecha_creacion"]


@admin.register(Profesor)
class ProfesorAdmin(ModelAdmin):
    list_display = [
        "nombres",
        "apellidos",
        "esta_activo",
    ]
    list_filter = ["esta_activo"]
    search_fields = ["nombres", "apellidos"]
    autocomplete_fields = ["usuario"]
    list_editable = ["esta_activo"]
    readonly_fields = ["fecha_ingreso"]


@admin.register(Estudiante)
class EstudianteAdmin(ModelAdmin):
    list_display = [
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "estado",
    ]
    list_filter = ["estado"]
    search_fields = ["nombres", "apellidos"]


@admin.register(Lapso)
class LapsoAdmin(ModelAdmin):
    list_display = ["numero_lapso", "nombre_lapso", "fecha_inicio", "fecha_fin"]
    list_filter = ["numero_lapso"]
    search_fields = ["nombre_lapso"]


@admin.register(AñoMateria)
class AñoMateriaAdmin(ModelAdmin):
    list_display = ["año", "materia"]
    list_filter = ["año", "materia"]
    search_fields = ["materia__nombre_materia"]
    autocomplete_fields = ["materia"]


@admin.register(ProfesorMateria)
class ProfesorMateriaAdmin(ModelAdmin):
    list_display = ["profesor", "materia", "año", "seccion", "es_profesor_principal"]
    list_filter = ["año", "es_profesor_principal", "seccion"]
    search_fields = ["profesor__nombre", "materia__nombre_materia"]
    autocomplete_fields = ["profesor", "materia", "año", "seccion"]
    list_editable = ["es_profesor_principal"]


@admin.register(Matricula)
class MatriculaAdmin(ModelAdmin):
    list_display = ["estudiante", "año", "seccion", "fecha_matricula"]
    list_filter = ["año", "seccion"]
    search_fields = ["estudiante__nombre", "estudiante__apellido"]
    autocomplete_fields = ["estudiante", "seccion"]


@admin.register(Nota)
class NotaAdmin(ModelAdmin):
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
