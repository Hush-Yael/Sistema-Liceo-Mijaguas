from django.urls import path
from . import views


urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("materias/", views.materias, name="materias"),
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
        "notas-estudiante/<int:estudiante_id>/",
        views.notas_por_estudiante_lapso,
        name="notas_estudiante",
    ),
    path(
        "promedios-estudiantes/",
        views.promedio_notas_estudiante_materia,
        name="promedios_estudiantes",
    ),
    path(
        "promedios-año-materia/",
        views.notas_promedio_por_año_materia,
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
