from app.vistas import crear_crud_urls
import estudios.vistas.parametros as vistas


urlpatterns = (
    *crear_crud_urls(
        "materia",
        "materias",
        vistas.ListaMaterias,
        vistas.CrearMateria,
        vistas.ActualizarMateria,
    ),
    *crear_crud_urls(
        "año", "años", vistas.ListaAños, vistas.CrearAño, vistas.ActualizarAño
    ),
    *crear_crud_urls(
        "lapso", "lapsos", vistas.ListaLapsos, vistas.CrearLapso, vistas.ActualizarLapso
    ),
    *crear_crud_urls(
        "seccion",
        "secciones",
        vistas.ListaSecciones,
        vistas.CrearSeccion,
        vistas.ActualizarSeccion,
    ),
)
