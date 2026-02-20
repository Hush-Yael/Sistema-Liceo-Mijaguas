from typing import TypedDict
from typing_extensions import NotRequired
from django.http import HttpRequest
from django.conf import settings
from django.urls import reverse_lazy
from app.util import vn, vnp
from app.vistas import nombre_url_crear_auto, nombre_url_lista_auto
from estudios.modelos.gestion.calificaciones import Nota, Tarea, TipoTarea
from estudios.modelos.gestion.personas import (
    Estudiante,
    Profesor,
    ProfesorMateria,
    Matricula,
)
from estudios.modelos.parametros import Lapso, Materia, Seccion, Año
from usuarios.models import Usuario, Grupo
from app.settings import MEDIA_URL


class Enlace(TypedDict):
    label: str
    icono_nombre: str
    href: str
    icono_style: NotRequired[str]


def obtener_enlaces(request: HttpRequest, permisos: "set[str]"):
    def si_permitido(permiso: str, enlace: Enlace) -> "Enlace | None":
        return enlace if request.user.is_superuser or permiso in permisos else None  # type: ignore

    return [
        {
            "label": "Profesores",
            "icono_nombre": "profesores",
            "enlaces": [
                si_permitido(
                    "estudios.add_profesor",
                    {
                        "label": "Añadir profesor",
                        "icono_nombre": "añadir",
                        "href": reverse_lazy(nombre_url_crear_auto(Profesor)),
                    },
                ),
                si_permitido(
                    "estudios.view_profesor",
                    {
                        "label": "Lista de profesores",
                        "icono_nombre": "usuarios",
                        "href": reverse_lazy(nombre_url_lista_auto(Profesor)),
                    },
                ),
                si_permitido(
                    "estudios.view_profesormateria",
                    {
                        "label": "Materias impartidas",
                        "icono_nombre": "asignaciones_pm",
                        "href": reverse_lazy(nombre_url_lista_auto(ProfesorMateria)),
                    },
                ),
            ],
        },
        {
            "label": "Estudiantes",
            "icono_nombre": "estudiantes",
            "enlaces": [
                si_permitido(
                    "estudios.add_estudiante",
                    {
                        "label": "Añadir estudiante",
                        "icono_nombre": "añadir",
                        "href": reverse_lazy(nombre_url_crear_auto(Estudiante)),
                    },
                ),
                si_permitido(
                    "estudios.view_estudiante",
                    {
                        "label": "Lista de estudiantes",
                        "icono_nombre": "tabla",
                        "href": reverse_lazy(nombre_url_lista_auto(Estudiante)),
                    },
                ),
                si_permitido(
                    "estudios.view_seccion",
                    {
                        "label": "Secciones",
                        "icono_nombre": "secciones",
                        "icono_style": "transform: scale(1.1)",
                        "href": reverse_lazy(nombre_url_lista_auto(Seccion)),
                    },
                ),
                si_permitido(
                    "estudios.view_matricula",
                    {
                        "label": "Matrículas",
                        "icono_nombre": "matriculas",
                        "href": reverse_lazy(nombre_url_lista_auto(Matricula)),
                    },
                ),
            ],
        },
        {
            "label": "Notas",
            "icono_nombre": "notas",
            "enlaces": [
                si_permitido(
                    "estudios.add_nota",
                    {"label": "Añadir nota", "icono_nombre": "añadir"},
                ),
                si_permitido(
                    "estudios.view_nota",
                    {
                        "label": "Lista de notas",
                        "icono_nombre": "tabla",
                        "href": reverse_lazy(nombre_url_lista_auto(Nota)),
                    },
                ),
                si_permitido(
                    "estudios.view_nota",
                    {"label": "Boletines", "icono_nombre": "boletines"},
                ),
            ],
        },
        {
            "label": vnp(Tarea),
            "icono_nombre": "tareas",
            "enlaces": [
                si_permitido(
                    "estudios.add_tarea",
                    {
                        "label": f"Añadir {vn(Tarea)}",
                        "icono_nombre": "añadir",
                        "href": reverse_lazy(nombre_url_crear_auto(Tarea)),
                    },
                )
                if hasattr(request.user, "profesor")
                else None,
                si_permitido(
                    "estudios.view_tarea",
                    {
                        "label": f"Mis {vnp(Tarea)}",
                        "icono_nombre": "tabla",
                        # "href": reverse_lazy("mis_tareas"),
                        "href": reverse_lazy(nombre_url_lista_auto(Tarea)),
                    },
                )
                if hasattr(request.user, "profesor")
                else None,
                # si_permitido(
                #     "estudios.view_tarea",
                #     {
                #         "label": "Todas las tareas",
                #         "icono_nombre": "tabla",
                #         "href": reverse_lazy(nombre_url_lista_auto(Tarea)),
                #     },
                # ),
                si_permitido(
                    "estudios.view_tipotarea",
                    {
                        "label": vnp(TipoTarea),
                        "icono_nombre": "tabla",
                        "href": reverse_lazy(nombre_url_lista_auto(TipoTarea)),
                    },
                ),
            ],
        },
        {
            "label": "Gestión académica",
            "icono_nombre": "admin",
            "enlaces": [
                si_permitido(
                    "estudios.view_año",
                    {
                        "label": "Años",
                        "icono_nombre": "años",
                        "href": reverse_lazy(nombre_url_lista_auto(Año)),
                    },
                ),
                si_permitido(
                    "estudios.view_lapso",
                    {
                        "label": "Lapsos",
                        "icono_nombre": "lapsos",
                        "href": reverse_lazy(nombre_url_lista_auto(Lapso)),
                    },
                ),
                si_permitido(
                    "estudios.view_materia",
                    {
                        "label": "Materias",
                        "icono_nombre": "materias",
                        "href": reverse_lazy(nombre_url_lista_auto(Materia)),
                    },
                ),
            ],
        },
        {
            "label": "Usuarios",
            "icono_nombre": "usuarios",
            "enlaces": [
                si_permitido(
                    "usuarios.add_usuario",
                    {
                        "label": "Añadir usuario",
                        "icono_nombre": "añadir",
                        "href": reverse_lazy(nombre_url_crear_auto(Usuario)),
                    },
                ),
                si_permitido(
                    "usuarios.view_usuario",
                    {
                        "label": "Lista de usuarios",
                        "icono_nombre": "usuarios",
                        "href": reverse_lazy(nombre_url_lista_auto(Usuario)),
                    },
                ),
                si_permitido(
                    "usuarios.view_grupo",
                    {
                        "label": "Grupos de permisos",
                        "icono_nombre": "permisos",
                        "href": reverse_lazy(nombre_url_lista_auto(Grupo)),
                    },
                ),
            ],
        },
    ]


def contexto(request: HttpRequest):
    autenticado = request.user.is_authenticated
    if autenticado:  # type: ignore
        permisos = request.user.get_all_permissions()  # type: ignore

    return {
        "DEBUG": settings.DEBUG,
        "enlaces": obtener_enlaces(request, permisos)  # type: ignore - sí se define permisos
        if autenticado
        else [],
        "media_url": MEDIA_URL,
    }
