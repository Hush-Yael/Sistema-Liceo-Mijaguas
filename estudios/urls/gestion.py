from django.urls import path
from app.vistas import crear_crud_urls
from app.util import nombre_url_lista_auto, nombre_url_crear_auto
from estudios.vistas.gestion import inicio
import estudios.vistas.gestion.personas as vistas_personas
import estudios.vistas.gestion.calificaciones as vistas_calificaciones
from estudios.modelos.gestion.calificaciones import Nota
from estudios.modelos.gestion.personas import Profesor, ProfesorMateria, Matricula


urlpatterns = (
    path("", inicio, name="inicio"),
    path(
        "notas/",
        vistas_calificaciones.ListaNotas.as_view(),
        name=nombre_url_lista_auto(Nota),
    ),
    path(
        "notas/crear/",
        vistas_calificaciones.ListaNotas.as_view(),
        name=nombre_url_crear_auto(Nota),
    ),
    *crear_crud_urls(
        Profesor,
        vistas_personas.ListaProfesores,
        vistas_personas.CrearProfesor,
        vistas_personas.ActualizarProfesor,
    ),
    *crear_crud_urls(
        ProfesorMateria,
        vistas_personas.ListaProfesoresMaterias,
        vistas_personas.CrearProfesorMateria,
        vistas_personas.ActualizarProfesorMateria,
    ),
    *crear_crud_urls(
        Matricula,
        vistas_personas.ListaMatriculas,
        vistas_personas.CrearMatricula,
        vistas_personas.ActualizarMatricula,
    ),
)
