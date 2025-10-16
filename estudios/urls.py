from django.urls import path
from . import views


urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("materias/", views.materias, name="materias"),
    path("profesores/", views.profesores, name="profesores"),
    path("notas/", views.notas, name="notas"),
    path(
        "notas/<int:seccion_id>/",
        views.notas__seccion_estudiantes,
        name="notas__seccion_estudiantes",
    ),
    path(
        "notas/<int:seccion_id>/<int:estudiante_id>/",
        views.notas__seccion_estudiante_lapsos,
        name="notas__seccion_estudiante_lapsos",
    ),
    path(
        "notas/<int:seccion_id>/<int:estudiante_id>/<int:lapso_id>/",
        views.notas__seccion_estudiante_lapso,
        name="notas__seccion_estudiante_lapso",
    ),
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
        "profesores-materias/", views.profesores_y_materias, name="profesores_materias"
    ),
    path(
        "resumen-matriculas/",
        views.resumen_matriculas_por_año,
        name="resumen_matriculas",
    ),
]
