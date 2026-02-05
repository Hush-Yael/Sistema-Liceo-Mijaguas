from django.urls import path
from app.vistas import crear_crud_urls
import estudios.vistas.gestion as vistas


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
        Matricula,
        vistas_personas.ListaMatriculas,
        vistas_personas.CrearMatricula,
        vistas_personas.ActualizarMatricula,
    ),
)
