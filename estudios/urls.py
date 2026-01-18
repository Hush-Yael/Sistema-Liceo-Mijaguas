from django.urls import path
from app.vistas import crear_crud_urls
from . import views


urlpatterns = (
    path("", views.inicio, name="inicio"),
    path("notas/", views.ListaNotas.as_view(), name="notas"),
    path("notas/crear/", views.ListaNotas.as_view(), name="crear_nota"),
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
    *crear_crud_urls(
        "materia",
        "materias",
        views.ListaMaterias,
        views.CrearMateria,
        views.ActualizarMateria,
    ),
    *crear_crud_urls(
        "año", "años", views.ListaAños, views.CrearAño, views.ActualizarAño
    ),
    *crear_crud_urls(
        "lapso", "lapsos", views.ListaLapsos, views.CrearLapso, views.ActualizarLapso
    ),
    *crear_crud_urls(
        "seccion",
        "secciones",
        views.ListaSecciones,
        views.CrearSeccion,
        views.ActualizarSeccion,
    ),
    *crear_crud_urls(
        "matricula",
        "matriculas",
        views.ListaMatriculas,
        views.CrearMatricula,
        views.ActualizarMatricula,
    ),
)
