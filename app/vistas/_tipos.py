from typing import Literal, TypedDict
from typing_extensions import NotRequired
from django import forms


class Columna(TypedDict):
    clave: str
    titulo: str
    alinear: NotRequired[Literal["derecha", "centro"]]


class ColumnaFija(Columna):
    anotada: NotRequired[bool]


class PermisosVistaLista(TypedDict):
    crear: bool
    editar: bool
    eliminar: bool


class VistaListaContexto(TypedDict):
    form_filtros: "forms.Form | None"
    form_con_orden: bool
    permisos: PermisosVistaLista
    no_hay_objetos: bool
    modelos_relacionados: "list[str]"
    lista_reemplazada_por_htmx: NotRequired[bool]
    mensajes_recibidos: NotRequired[bool]
