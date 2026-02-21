from django.core.paginator import Page
from django.http import (
    HttpRequest,
    HttpResponseForbidden,
)
from django.db.models import Avg, Count, Prefetch, QuerySet
from app.vistas.forms import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
)
from app.vistas.listas import VistaListaObjetos
from estudios.forms.gestion.calificaciones import (
    FormTarea,
    FormTipoTarea,
)
from estudios.forms.gestion.busqueda import (
    NotasBusquedaForm,
    TareaBusquedaForm,
)
from estudios.modelos.gestion.personas import (
    Matricula,
    ProfesorMateria,
)
from estudios.modelos.parametros import Lapso, obtener_lapso_actual
from estudios.modelos.gestion.calificaciones import (
    Nota,
    Tarea,
    TareaProfesorMateria,
    TipoTarea,
)
from usuarios.models import GruposBase


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
    template_name = "calificaciones/tareas/index.html"
    plantilla_lista = "calificaciones/tareas/lista.html"
    genero_sustantivo_objeto = "F"

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if tipos := datos_form.get(TareaBusquedaForm.Campos.TIPOS):
            queryset = queryset.filter(tareaprofesormateria__tarea__tipo__in=tipos)

        if materias := datos_form.get(TareaBusquedaForm.Campos.MATERIAS):
            queryset = queryset.filter(materia__in=materias)

        if secciones := datos_form.get(TareaBusquedaForm.Campos.SECCIONES):
            queryset = queryset.filter(seccion__in=secciones)

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

    form_filtros = TareaBusquedaForm  # type: ignore
    paginate_by = 10
    http_method_names = ("get", "post", "delete")
    lapso_actual: "Lapso | None"

    def get_queryset(self, *args, **kwargs):
        lapso_actual = self.lapso_actual = obtener_lapso_actual()

        q = ProfesorMateria.objects.filter(
            profesor=self.request.user.profesor,  # type: ignore - sí existe "profesor" como atributo
            tareaprofesormateria__tarea__lapso=lapso_actual,
        )

        return super().get_queryset(q)

    def aplicar_filtros(self, queryset, datos_form):
        """Además filtrar solo las tareas propias del profesor"""
        queryset = super().aplicar_filtros(queryset, datos_form)

        return queryset.distinct().prefetch_related(
            Prefetch(
                "tareaprofesormateria_set",
                TareaProfesorMateria.objects.filter(
                    profesormateria__profesor=self.request.user.profesor,  # type: ignore - sí existe "profesor" como atributo
                    tarea__lapso=self.lapso_actual,
                ),
                to_attr="tareas_asignadas",
            )
        )

    def obtener_total(self, ctx):
        return self.model.objects.filter(
            profesor=self.request.user.profesor,  # type: ignore - sí existe "profesor" como atributo
            lapso=self.lapso_actual,
        ).count()

    def al_menos_uno(self):
        return self.model.objects.filter(
            profesor=self.request.user.profesor,  # type: ignore - sí existe "profesor" como atributo
            lapso=self.lapso_actual,
        ).exists()  # type: ignore - sí existe "profesor" como atributo

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

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        return ctx


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


class ListaNotas(VistaListaObjetos):
    model = Nota
    template_name = "calificaciones/notas/index.html"
    plantilla_lista = "calificaciones/notas/lista.html"
    paginate_by = 1
    form_filtros = NotasBusquedaForm
    genero_sustantivo_objeto = "F"

    def get_queryset(self, *args, **kwargs):
        queryset = (
            Matricula.objects.annotate(promedio=Avg("nota__valor"))
            .select_related("estudiante", "seccion", "seccion__año", "lapso")
            .order_by("estudiante__apellidos", "estudiante__nombres")
        )

        notas_qs = Nota.objects.select_related(
            "tarea_profesormateria__profesormateria__materia",
            "tarea_profesormateria__tarea",
        ).order_by("tarea_profesormateria__profesormateria__materia__nombre")

        datos_form = self.inicializar_form_filtros()

        self.modificar_paginacion(datos_form)

        # busqueda textual
        queryset = self.aplicar_filtros(queryset, datos_form)
        queryset = self.aplicar_orden(queryset, datos_form)

        if secciones := datos_form.get(NotasBusquedaForm.Campos.SECCIONES):
            notas_qs = notas_qs.filter(
                tarea_profesormateria__profesormateria__seccion__in=secciones
            )
            queryset = queryset.filter(seccion__in=secciones)

        if años := datos_form.get("anios"):
            notas_qs = notas_qs.filter(
                tarea_profesormateria__profesormateria__seccion__año__in=años
            )
            queryset = queryset.filter(seccion__año__in=años)

        if lapsos := datos_form.get(NotasBusquedaForm.Campos.LAPSOS):
            notas_qs = notas_qs.filter(tarea_profesormateria__tarea__lapso__in=lapsos)
            queryset = queryset.filter(lapso__in=lapsos)

        if materias := datos_form.get(NotasBusquedaForm.Campos.MATERIAS):
            notas_qs = notas_qs.filter(
                tarea_profesormateria__profesormateria__materia__in=materias
            )

        # Prefetch optimizado para notas con sus relaciones
        notas_prefetch = Prefetch(
            "nota_set",
            queryset=notas_qs,
            to_attr="notas_prefetch",
        )

        # Consulta principal con optimizaciones
        return queryset.prefetch_related(notas_prefetch)

    def paginate_queryset(self, queryset, page_size):
        """Sobrescribe el método de paginación para mantener la paginación estándar."""
        return super().paginate_queryset(queryset, page_size)

    def procesar_matriculas(self, matriculas):
        """Procesa las matrículas para agrupar notas por materia"""
        matriculas_procesadas = []

        for matricula in matriculas:
            # Diccionario para agrupar notas por materia
            materias_dict = {}

            # Procesar las notas prefetched
            for nota in getattr(matricula, "notas_prefetch", []):
                materia = nota.tarea_profesormateria.profesormateria.materia
                materia_id = materia.id

                if materia_id not in materias_dict:
                    materias_dict[materia_id] = {
                        "materia": materia,
                        "notas": [],
                        "promedio": 0.0,
                    }

                # Agregar nota con información relevante
                materias_dict[materia_id]["notas"].append(
                    {
                        "id": nota.id,
                        "valor": nota.valor,
                        "fecha": nota.fecha,
                        "tipo": nota.tarea_profesormateria.tarea.tipo.nombre,
                        "tarea_id": nota.tarea_profesormateria.tarea.id,
                    }
                )

            # Calcular promedios por materia
            for materia_data in materias_dict.values():
                notas = [n["valor"] for n in materia_data["notas"]]
                if notas:
                    materia_data["promedio"] = sum(notas) / len(notas)

            # Convertir diccionario a lista ordenada por nombre de materia
            materias_lista = sorted(
                materias_dict.values(), key=lambda x: x["materia"].nombre
            )

            # Calcular promedio general
            promedios_materias = [
                m["promedio"] for m in materias_lista if m["promedio"] > 0
            ]
            promedio_general = (
                sum(promedios_materias) / len(promedios_materias)
                if promedios_materias
                else 0.0
            )

            # Crear estructura procesada para la matrícula
            matricula_procesada = {
                "id": matricula.id,
                "estudiante": matricula.estudiante,
                "seccion": matricula.seccion,
                "lapso": matricula.lapso,
                "materias_cursadas": materias_lista,
                "promedio_general": promedio_general,
                "total_materias": len(materias_lista),
            }

            matriculas_procesadas.append(matricula_procesada)

        return matriculas_procesadas

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Obtener el objeto de paginación del contexto
        page_obj: "Page | None" = ctx.get("page_obj")

        if page_obj and page_obj.object_list:
            # Procesar solo las matrículas de la página actual
            ctx["matriculas_procesadas"] = self.procesar_matriculas(
                page_obj.object_list
            )
        else:
            ctx["matriculas_procesadas"] = ()

        return ctx

    def obtener_total(self):
        return super().obtener_total()
