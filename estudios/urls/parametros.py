from app.vistas import crear_crud_urls
import estudios.vistas.parametros as vistas
from estudios.modelos.parametros import (
    Materia,
    Año,
    Lapso,
    Seccion,
)

urlpatterns = (
    *crear_crud_urls(
        Materia,
        vistas.ListaMaterias,
        vistas.CrearMateria,
        vistas.ActualizarMateria,
    ),
    *crear_crud_urls(Año, vistas.ListaAños, vistas.CrearAño, vistas.ActualizarAño),
    *crear_crud_urls(
        Lapso, vistas.ListaLapsos, vistas.CrearLapso, vistas.ActualizarLapso
    ),
    *crear_crud_urls(
        Seccion,
        vistas.ListaSecciones,
        vistas.CrearSeccion,
        vistas.ActualizarSeccion,
    ),
)
