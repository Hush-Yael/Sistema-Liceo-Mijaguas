from django.urls import path
from app.vistas import crear_crud_urls, nombre_url_lista_auto, nombre_url_crear_auto
from estudios.vistas.gestion import inicio
import estudios.vistas.gestion.personas as vistas
from estudios.modelos.gestion.personas import (
    Estudiante,
    Profesor,
    ProfesorMateria,
    Matricula,
)


urlpatterns = (
    path("", inicio, name="inicio"),
    *crear_crud_urls(
        Estudiante,
        vistas.ListaEstudiantes,
        vistas.CrearEstudiante,
        vistas.ActualizarEstudiante,
    ),
    *crear_crud_urls(
        Profesor,
        vistas.ListaProfesores,
        vistas.CrearProfesor,
        vistas.ActualizarProfesor,
    ),
    path(
        f"{ProfesorMateria._meta.verbose_name_plural}/",
        vistas.ListaProfesoresMaterias.as_view(),
        name=nombre_url_lista_auto(ProfesorMateria),
    ),
    path(
        f"{ProfesorMateria._meta.verbose_name_plural}/crear/",
        vistas.CrearProfesorMateria.as_view(),
        name=nombre_url_crear_auto(ProfesorMateria),
    ),
    *crear_crud_urls(
        Matricula,
        vistas.ListaMatriculas,
        vistas.CrearMatricula,
        vistas.ActualizarMatricula,
    ),
)
