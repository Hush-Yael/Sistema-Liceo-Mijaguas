from django.http import HttpRequest
from django.conf import settings
from django.urls import reverse_lazy


def obtener_enlaces(request: HttpRequest, permisos: "set[str]"):
    def si_permitido(permiso: str, enlace: "dict[str, str]") -> "dict[str, str] | None":
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
                    {"label": "Todos los profesores", "icono_nombre": "usuarios"},
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
                    {"label": "Todos los estudiantes", "icono_nombre": "usuarios"},
                ),
                si_permitido(
                    "estudios.view_matricula",
                    {"label": "Matrículas", "icono_nombre": "tabla"},
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
            "label": "Materias",
            "icono_nombre": "materias",
            "enlaces": [
                si_permitido(
                    "estudios.add_materia",
                    {
                        "label": "Añadir materia",
                        "icono_nombre": "añadir",
                        "href": reverse_lazy("crear_materia"),
                    },
                ),
                si_permitido(
                    "estudios.view_materia",
                    {
                        "label": "Lista de materias",
                        "icono_nombre": "tabla",
                        "href": reverse_lazy("materias"),
                    },
                ),
            ],
        },
        {
            "label": "Administración",
            "icono_nombre": "admin",
            "enlaces": [
                si_permitido(
                    "estudios.view_año",
                    {
                        "label": "Años académicos",
                        "icono_nombre": "años",
                        "href": reverse_lazy("años"),
                    },
                ),
                si_permitido(
                    "estudios.view_seccion",
                    {"label": "Secciones", "icono_nombre": "secciones"},
                ),
                si_permitido(
                    "estudios.view_lapso",
                    {
                        "label": "Lapsos académicos",
                        "icono_nombre": "lapsos",
                        "href": reverse_lazy("lapsos"),
                    },
                ),
            ],
        },
        {
            "label": "Usuarios",
            "icono_nombre": "usuarios",
            "enlaces": [
                si_permitido(
                    "usuarios.add_user",
                    {"label": "Añadir usuario", "icono_nombre": "añadir"},
                ),
                si_permitido(
                    "usuarios.view_user",
                    {"label": "Todos los usuarios", "icono_nombre": "usuarios"},
                ),
                si_permitido(
                    "auth.view_permission",
                    {"label": "Permisos", "icono_nombre": "permisos"},
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
