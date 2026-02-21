from django.urls import path
from app.vistas import nombre_url_crear_auto, nombre_url_lista_auto
from estudios.modelos.gestion.calificaciones import Nota, Tarea, TipoTarea
import estudios.vistas.gestion.calificaciones as vistas
from app.vistas import crear_crud_urls


urlpatterns = (
    path(
        "notas/",
        vistas.ListaNotas.as_view(),
        name=nombre_url_lista_auto(Nota),
    ),
    path(
        "notas/cargar",
        vistas.VistaMateriasProfesor.as_view(),
        name=nombre_url_crear_auto(Nota),
    ),
    path(
        "notas/cargar/<int:profesormateria_id>/",
        vistas.VistaCargarNotas.as_view(),
        name="cargar_notas",
    ),
    path(
        "api/guardar-nota/",
        vistas.guardar_nota_individual,
        name="guardar_nota_individual",
    ),
    *crear_crud_urls(
        TipoTarea,
        vistas.ListaTiposTareas,
        vistas.CrearTipoTarea,
        vistas.EditarTipoTarea,
    ),
    *crear_crud_urls(
        Tarea,
        vistas.ListaTareasProfesor,
        vistas.CrearTarea,
        vistas.ActualizarTarea,
    ),
)
