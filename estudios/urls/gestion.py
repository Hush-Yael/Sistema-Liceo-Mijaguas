from django.urls import path
from app.vistas import crear_crud_urls, nombre_url_lista_auto, nombre_url_crear_auto
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
    path(
        f"{ProfesorMateria._meta.verbose_name_plural}/",
        vistas_personas.ListaProfesoresMaterias.as_view(),
        name=nombre_url_lista_auto(ProfesorMateria),
    ),
    path(
        f"{ProfesorMateria._meta.verbose_name_plural}/crear/",
        vistas_personas.CrearProfesorMateria.as_view(),
        name=nombre_url_crear_auto(ProfesorMateria),
    ),
    *crear_crud_urls(
        Matricula,
        vistas_personas.ListaMatriculas,
        vistas_personas.CrearMatricula,
        vistas_personas.ActualizarMatricula,
    ),
)
