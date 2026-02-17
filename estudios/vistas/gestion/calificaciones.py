from functools import reduce
from django.db.models.functions.datetime import TruncMinute
from django.http import (
    HttpRequest,
    HttpResponseForbidden,
)
from django.db.models import F, Count, Prefetch, QuerySet, Value
from app.util import nc
from app.vistas import nombre_url_editar_auto
from app.vistas.forms import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
)
from app.vistas.listas import VistaListaObjetos, VistaTablaAdaptable
from estudios.forms.gestion.calificaciones import (
    FormTarea,
    FormTipoTarea,
)
from estudios.forms.gestion.busqueda import (
    NotasBusquedaForm,
    TareaBusquedaForm,
    TareaProfesorMateriaBusquedaForm,
)
from estudios.modelos.gestion.personas import (
    Matricula,
    ProfesorMateria,
)
from estudios.modelos.parametros import Materia
from django.db.models.functions import Concat
from estudios.modelos.gestion.calificaciones import (
    Nota,
    Tarea,
    TareaProfesorMateria,
    TipoTarea,
)
from estudios.vistas.gestion import aplicar_filtros_secciones_y_lapsos
from usuarios.models import GruposBase


class ListaNotas(VistaTablaAdaptable):
    model = Nota
    template_name = "calificaciones/notas/index.html"
    plantilla_lista = "calificaciones/notas/lista.html"
    paginate_by = 50
    form_filtros = NotasBusquedaForm
    columnas_a_evitar = set()
    columnas_totales = (
        {"titulo": "Estudiante", "clave": "estudiante_nombres", "anotada": True},
        {
            "titulo": "Cédula",
            "clave": "cedula",
            "alinear": "derecha",
            "anotada": True,
        },
        {"titulo": "Materia", "clave": "materia_nombre", "anotada": True},
        {"titulo": "Sección", "clave": "seccion_nombre", "anotada": True},
        {"titulo": "Valor", "clave": "valor", "alinear": "derecha"},
        {
            "titulo": "Lapso",
            "clave": "lapso_nombre",
            "anotada": True,
            "alinear": "derecha",
        },
        {"titulo": "Fecha de añadida", "clave": "fecha_añadida", "anotada": True},
    )
    genero_sustantivo_objeto = "F"

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        queryset = Nota.objects.annotate(
            materia_nombre=F("tarea_profesormateria__profesormateria__materia__nombre"),
            seccion_nombre=F("matricula__seccion__nombre"),
            cedula=F("matricula__estudiante__cedula"),
            lapso_nombre=F("matricula__lapso__nombre"),
            estudiante_nombres=Concat(
                "matricula__estudiante__nombres",
                Value(" "),
                "matricula__estudiante__apellidos",
            ),
            fecha_añadida=TruncMinute("fecha"),
        ).only(
            *(
                col["clave"]
                for col in self.columnas_totales
                if not col.get("anotada", False)
            )
        )

        return super().get_queryset(queryset)

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        queryset = aplicar_filtros_secciones_y_lapsos(
            self,
            queryset,
            datos_form,
            seccion_col_nombre="matricula__seccion",
            lapso_col_nombre="matricula__lapso",
        )

        if materias := self.obtener_y_alternar(
            NotasBusquedaForm.Campos.MATERIAS, datos_form, "materia_nombre"
        ):
            queryset = queryset.filter(materia_id__in=materias)

        try:
            nota_minima = float(datos_form.get("valor_minimo", 0))  # type: ignore
            nota_maxima = float(datos_form.get("valor_maximo", 20))  # type: ignore

            if nota_minima <= nota_maxima:
                queryset = queryset.filter(valor__range=(nota_minima, nota_maxima))
        except (ValueError, TypeError):
            pass

        return queryset

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx.update(
            {
                "hay_matriculas": Matricula.objects.exists(),
                "hay_materias": Materia.objects.exists(),
            }
        )

        return ctx


class ListaTiposTareas(VistaListaObjetos):
    model = TipoTarea
    template_name = "calificaciones/tipos-tareas/index.html"
    plantilla_lista = "calificaciones/tipos-tareas/lista.html"
    genero_sustantivo_objeto = "F"

    def get_queryset(self, *args, **kwargs):
        q = TipoTarea.objects.annotate(cantidad=Count("tarea")).all()
        return super().get_queryset(q)


class VistaFormTipoTarea:
    template_name = "calificaciones/tipos-tareas/form.html"
    model = TipoTarea
    form_class = FormTipoTarea
    genero_sustantivo_objeto = "F"


class CrearTipoTarea(VistaFormTipoTarea, VistaCrearObjeto):
    pass


class EditarTipoTarea(VistaFormTipoTarea, VistaActualizarObjeto):
    pass


def nada_que_ver_profesor(request: HttpRequest):
    """Indica que un usuario no es profesor ni admin"""

    return (
        not hasattr(request.user, "profesor")
        and not request.user.grupos.filter(  # type: ignore - sí existe "grupos" como atributo
            name=GruposBase.ADMIN.value
        ).exists()
    )


class ListaTareasMixin(VistaListaObjetos):
    """Clase base para las listas de tareas"""

    model = Tarea
    template_name = "calificaciones/tareas/pestañas/info-completa.html"
    plantilla_lista = "calificaciones/tareas/pestañas/lista_info-completa.html"
    genero_sustantivo_objeto = "F"

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if tipos := datos_form.get(TareaBusquedaForm.Campos.TIPOS):
            queryset = queryset.filter(tipo__in=tipos)

        return queryset


class ProfesorPropioMixin:
    request: HttpRequest

    def es_profesor(self):
        """Indica si el usuario es profesor"""
        return hasattr(self.request.user, "profesor")

    def has_permission(self):
        """El usuario puede ver la vista si es profesor"""

        puede_ver = super().has_permission()  # type: ignore - Sí existe el método "has_permission"

        return puede_ver and self.es_profesor()


class ListaTareasProfesor(
    ProfesorPropioMixin,
    ListaTareasMixin,
):
    """Vista dedicada a las tareas propias de cada profesor"""

    form_filtros = TareaBusquedaForm
    http_method_names = ("get", "post", "delete")

    def get_queryset(self, *args, **kwargs):
        q = self.model.objects.all().filter(profesor=self.request.user.profesor)  # type: ignore - sí existe "profesor" como atributo

        return super().get_queryset(q)

    def aplicar_filtros(self, queryset, datos_form):
        """Además filtrar solo las tareas propias del profesor"""
        queryset = super().aplicar_filtros(queryset, datos_form)

        queryset = queryset.filter(profesor=self.request.user.profesor)  # type: ignore - sí existe "profesor" como atributo

        return queryset

    def obtener_total(self):
        self.total = self.model.objects.filter(
            profesor=self.request.user.profesor  # type: ignore
        ).count()

    def al_menos_uno(self):
        return self.model.objects.filter(profesor=self.request.user.profesor).exists()  # type: ignore - sí existe "profesor" como atributo

    def delete(self, request: HttpRequest, *args, **kwargs):
        if not self.es_profesor():
            return HttpResponseForbidden(
                f"No tienes permisos para eliminar est{self.vocal_del_genero}s {self.nombre_objeto_plural}"
            )

        return super().delete(request, *args, **kwargs)

    def eliminar(self, request: HttpRequest, ids: "list[str]"):
        return self.model.objects.filter(
            id__in=ids, profesor=getattr(request.user, "profesor", None)
        ).delete()


class ListaTareasProfesorMateriaMixin(VistaListaObjetos):
    model = TareaProfesorMateria
    template_name = "calificaciones/tareas/pestañas/por-materias.html"
    plantilla_lista = "calificaciones/tareas/pestañas/lista_por-materias.html"
    genero_sustantivo_objeto = "F"
    url_crear = None  # type: ignore
    form_filtros = TareaProfesorMateriaBusquedaForm
    http_method_names = ("get", "post")

    def aplicar_filtros(self, queryset, datos_form):
        tpm_queryset = TareaProfesorMateria.objects.select_related("tarea").only(
            nc(TareaProfesorMateria.tarea)
        )

        if hasattr(self.request.user, "profesor"):
            queryset = queryset.filter(profesor=self.request.user.profesor)  # type: ignore - sí existe "profesor" como atributo
            tpm_queryset = tpm_queryset.filter(
                profesormateria__profesor=self.request.user.profesor  # type: ignore - sí existe "profesor" como atributo
            )

        queryset = super().aplicar_filtros(queryset, datos_form)

        if tipos := datos_form.get(TareaProfesorMateriaBusquedaForm.Campos.TIPOS):
            queryset = queryset.filter(tipo__in=tipos)
            tpm_queryset = tpm_queryset.filter(tarea__tipo__in=tipos)

        if anios := datos_form.get(TareaProfesorMateriaBusquedaForm.Campos.AÑOS):
            queryset = queryset.filter(
                tareaprofesormateria__profesormateria__seccion__año__in=anios
            )
            tpm_queryset = tpm_queryset.filter(profesormateria__seccion__año__in=anios)

        if secciones := datos_form.get(
            TareaProfesorMateriaBusquedaForm.Campos.SECCIONES
        ):
            queryset = queryset.filter(
                tareaprofesormateria__profesormateria__seccion__in=secciones
            )
            tpm_queryset = tpm_queryset.filter(profesormateria__seccion__in=secciones)

        return queryset.prefetch_related(
            Prefetch(
                "tareaprofesormateria_set",
                queryset=tpm_queryset,
                to_attr="materias_asignadas",
            )
        )

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        self.cantidad_filtradas = reduce(
            lambda x, y: x + len(y.materias_asignadas), ctx["object_list"], 0
        )

        return ctx


class ListaTareasProfesorMateriaPropias(
    ListaTareasProfesorMateriaMixin, ProfesorPropioMixin
):
    url_editar = nombre_url_editar_auto(Tarea)

    """Vista dedicada a la visualización de tareas propias de cada profesor asociadas a sus materias."""

    def get_queryset(self, *args, **kwargs):
        q = (
            Tarea.objects.annotate(cantidad_asignadas=Count("tareaprofesormateria"))
            .only(nc(Tarea.nombre))
            .filter(cantidad_asignadas__gt=0, profesor=self.request.user.profesor)  # type: ignore - sí existe "profesor" como atributo
        )

        return super().get_queryset(q)

    def obtener_total(self):
        self.total = self.model.objects.filter(
            profesormateria__profesor=self.request.user.profesor  # type: ignore - sí existe "profesor" como atributo
        ).count()

    def eliminar(self, request: HttpRequest, ids: "list[str]"):
        return self.model.objects.filter(
            id__in=ids,
            profesormateria__profesor=getattr(request.user, "profesor", None),
        ).delete()


class VistaFormTarea:
    template_name = "calificaciones/tareas/form.html"
    model = Tarea
    form_class = FormTarea
    request: HttpRequest
    genero_sustantivo_objeto = "F"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()  # type: ignore - Sí existe "get_form_kwargs" como atributo

        if self.request.user.profesor:  # type: ignore - sí existe "profesor" como atributo
            kwargs["profesor"] = self.request.user.profesor  # type: ignore - sí existe "profesor" como atributo

        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)  # type: ignore

        if self.request.method == "GET":
            no_es_usuario_profesor = ctx["no_es_usuario_profesor"] = not hasattr(
                self.request.user, "profesor"
            )

            if not no_es_usuario_profesor:
                materias_del_profesor: "QuerySet[ProfesorMateria]" = (
                    ctx["form"].fields["profesormateria"].queryset
                )
                pms_agrupadas = {}

                for profesormateria in materias_del_profesor:
                    nombre_materia = profesormateria.materia.nombre

                    if nombre_materia not in pms_agrupadas:
                        pms_agrupadas[nombre_materia] = []

                    pms_agrupadas[nombre_materia].append(
                        {
                            "id": str(profesormateria.id),  # type: ignore
                            "label": profesormateria.seccion.nombre,
                        }
                    )

                ctx["pms_agrupadas"] = [
                    {"label": pm[0], "opciones": pm[1]} for pm in pms_agrupadas.items()
                ]

        return ctx


class CrearTarea(VistaFormTarea, VistaCrearObjeto):
    pass


class ActualizarTarea(VistaFormTarea, VistaActualizarObjeto):
    pass
