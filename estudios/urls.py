from django.urls import path
from app.vistas import crear_crud_urls
from . import views


urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("profesores/", views.profesores, name="profesores"),
    path("notas/", views.notas, name="notas"),
    path(
        "notas_tabla/",
        views.notas_tabla,
        name="notas_tabla",
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


urlpatterns += crear_crud_urls(
    "materia",
    "materias",
    views.ListaMaterias,
    views.CrearMateria,
    views.ActualizarMateria,
)

urlpatterns += crear_crud_urls(
    "año", "años", views.ListaAños, views.CrearAño, views.ActualizarAño
)

urlpatterns += crear_crud_urls(
    "lapso", "lapsos", views.ListaLapsos, views.CrearLapso, views.ActualizarLapso
)
