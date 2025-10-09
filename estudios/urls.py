from django.urls import path
from . import views


urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("materias/", views.materias, name="materias"),
    path("materias/<int:materia_id>/", views.materia, name="materia"),
    path("profesores/", views.profesores, name="profesores"),
    path(
        "estudiantes-matriculados/",
        views.estudiantes_matriculados_por_año,
        name="estudiantes_matriculados",
    ),
    path(
        "materias-profesores/",
        views.materias_por_año_con_profesores,
        name="materias_profesores",
    ),
    path(
        "calificaciones-estudiante/<int:estudiante_id>/",
        views.calificaciones_por_estudiante_lapso,
        name="calificaciones_estudiante",
    ),
    path(
        "promedios-estudiantes/",
        views.promedio_calificaciones_estudiante_materia,
        name="promedios_estudiantes",
    ),
    path(
        "promedios-año-materia/",
        views.calificaciones_promedio_por_año_materia,
        name="promedios_año_materia",
    ),
    path(
        "profesores-materias/", views.profesores_y_materias, name="profesores_materias"
    ),
    path(
        "resumen-matriculas/",
        views.resumen_matriculas_por_año,
        name="resumen_matriculas",
    ),
]
