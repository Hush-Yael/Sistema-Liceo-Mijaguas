from typing import TypedDict
from typing_extensions import NotRequired
from django.http import HttpRequest
from django.conf import settings
from django.urls import reverse_lazy


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
                    {"label": "Añadir profesor", "icono_nombre": "añadir"},
                ),
                si_permitido(
                    "estudios.view_profesor",
                    {"label": "Lista de profesores", "icono_nombre": "usuarios"},
                ),
                si_permitido(
                    "estudios.view_profesormateria",
                    {
                        "label": "Asignación de materias",
                        "icono_nombre": "asignaciones_pm",
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
                    {"label": "Añadir estudiante", "icono_nombre": "añadir"},
                ),
                si_permitido(
                    "estudios.view_estudiante",
                    {"label": "Lista de estudiantes", "icono_nombre": "usuarios"},
                ),
                si_permitido(
                    "estudios.view_seccion",
                    {
                        "label": "Secciones",
                        "icono_nombre": "secciones",
                        "icono_style": "transform: scale(1.1)",
                        "href": reverse_lazy("secciones"),
                    },
                ),
                si_permitido(
                    "estudios.view_matricula",
                    {
                        "label": "Matrículas",
                        "icono_nombre": "tabla",
                        "href": reverse_lazy("matriculas"),
                    },
                ),
                si_permitido(
                    "estudios.view_bachiller",
                    {
                        "label": "Bachilleres",
                        "icono_nombre": "bachilleres",
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
                        "href": reverse_lazy("notas"),
                    },
                ),
                si_permitido(
                    "estudios.view_nota",
                    {"label": "Boletines", "icono_nombre": "boletines"},
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
                        "href": reverse_lazy("años"),
                    },
                ),
                si_permitido(
                    "estudios.view_lapso",
                    {
                        "label": "Lapsos",
                        "icono_nombre": "lapsos",
                        "href": reverse_lazy("lapsos"),
                    },
                ),
                si_permitido(
                    "estudios.view_materia",
                    {
                        "label": "Materias",
                        "icono_nombre": "materias",
                        "href": reverse_lazy("materias"),
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
                    {"label": "Añadir usuario", "icono_nombre": "añadir"},
                ),
                si_permitido(
                    "usuarios.view_usuario",
                    {"label": "Lista de usuarios", "icono_nombre": "usuarios"},
                ),
                si_permitido(
                    "usuarios.view_grupo",
                    {
                        "label": "Grupos de permisos",
                        "icono_nombre": "permisos",
                        "href": reverse_lazy("grupos"),
                    },
                ),
            ],
        },
        (
            {
                "label": "Panel de administración",
                "icono_nombre": "panel",
                "href": "/admin/",
            }
            if request.user.is_staff  # type: ignore
            else None
        ),
    ]


def contexto(request: HttpRequest):
    permisos = request.user.get_all_permissions()  # type: ignore

    return {
        "DEBUG": settings.DEBUG,
        "enlaces": obtener_enlaces(request, permisos)
        if request.user.is_authenticated
        else [],
    }
