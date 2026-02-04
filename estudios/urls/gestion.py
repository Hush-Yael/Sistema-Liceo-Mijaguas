from django.urls import path
from app.vistas import crear_crud_urls
import estudios.vistas.gestion as vistas


urlpatterns = (
    path("", vistas.inicio, name="inicio"),
    path("notas/", vistas.ListaNotas.as_view(), name="notas"),
    path("notas/crear/", vistas.ListaNotas.as_view(), name="crear_nota"),
    *crear_crud_urls(
        "matricula",
        "matriculas",
        vistas.ListaMatriculas,
        vistas.CrearMatricula,
        vistas.ActualizarMatricula,
    ),
)
