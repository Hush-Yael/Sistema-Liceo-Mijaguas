from typing import Any, Mapping
from django.contrib import messages
from django.db import models
from django.db.models.functions.datetime import TruncMinute
from django.http import (
    HttpResponseBadRequest,
)
from django.db.models import Case, Count, Q, F, Prefetch, When
from app.campos import FiltrosConjuntoOpciones
from app.forms import ConjuntoOpcionesForm
from app.util import obtener_filtro_bool_o_nulo
from app.vistas.forms import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
)
from app.vistas.listas import VistaListaObjetos
from estudios.forms.parametros import (
    FormAsignaciones,
    FormLapso,
    FormMateria,
    FormSeccion,
    FormAño,
)
from estudios.forms.parametros.busqueda import (
    LapsoBusquedaForm,
    MateriaBusquedaForm,
    OpcionesFormSeccion,
    SeccionBusquedaForm,
)
from estudios.modelos.parametros import (
    Lapso,
    Año,
    Seccion,
    Materia,
    AñoMateria,
    obtener_lapso_actual,
)


class ListaLapsos(VistaListaObjetos):
    template_name = "parametros/lapsos/index.html"
    plantilla_lista = "parametros/lapsos/lista.html"
    model = Lapso
    form_filtros = LapsoBusquedaForm

    def get_queryset(self, *args, **kwargs):
        lapso_actual = obtener_lapso_actual()

        q = Lapso.objects.order_by("-id", "numero")

        if lapso_actual is not None:
            q = q.annotate(
                es_actual=Case(When(id=lapso_actual.pk, then=True), default=False)
            )

        return super().get_queryset(q)


class CrearLapso(VistaCrearObjeto):
    template_name = "parametros/lapsos/form.html"
    model = Lapso
    form_class = FormLapso


class ActualizarLapso(VistaActualizarObjeto):
    template_name = "parametros/lapsos/form.html"
    model = Lapso
    form_class = FormLapso


class ListaMaterias(VistaListaObjetos):
    template_name = "parametros/materias/index.html"
    plantilla_lista = "parametros/materias/lista.html"
    model = Materia
    form_filtros = MateriaBusquedaForm
    form_asignaciones = FormAsignaciones
    genero_sustantivo_objeto = "F"
    columnas_totales = (
        {"titulo": "Nombre", "clave": "nombre"},
        {"clave": "asignaciones", "titulo": "Años asignados", "anotada": True},
        {"clave": "fecha", "titulo": "Fecha de creación", "anotada": True},
    )

    def get_queryset(self, *args, **kwargs):
        queryset = (
            Materia.objects.annotate(
                fecha=TruncMinute("fecha_creacion"),
            )
            .only(
                "id",
                "nombre",
            )
            .order_by("nombre")
        )

        return super().get_queryset(queryset)

    def aplicar_filtros(
        self,
        queryset: models.QuerySet,
        datos_form: "dict[str, Any] | Mapping[str, Any]",
    ):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if años_asignados := datos_form.get(MateriaBusquedaForm.Campos.ANIOS_ASIGNADOS):
            tipo_busqueda_anios = datos_form.get(
                f"{MateriaBusquedaForm.Campos.ANIOS_ASIGNADOS}{ConjuntoOpcionesForm.sufijo_tipo_q}"
            )

            # busqueda exacta de años asignados, ya sea todos o ninguno
            if (
                todos := tipo_busqueda_anios
                == FiltrosConjuntoOpciones.CONTIENE_TODAS.value[0]
            ) or tipo_busqueda_anios == FiltrosConjuntoOpciones.NO_CONTIENE_TODAS.value[
                0
            ]:
                queryset = queryset.annotate(
                    total_asignaciones=Count("añomateria"),
                    asignaciones_especificas=Count(
                        "añomateria", filter=Q(añomateria__año__in=años_asignados)
                    ),
                )

                if todos:
                    queryset = queryset.filter(
                        total_asignaciones=len(años_asignados),
                        asignaciones_especificas=len(años_asignados),
                    )
                else:
                    queryset = queryset.exclude(
                        total_asignaciones=len(años_asignados),
                        asignaciones_especificas=len(años_asignados),
                    )

            # busqueda de al menos un año asignado en la lista
            elif (
                tipo_busqueda_anios == FiltrosConjuntoOpciones.CONTIENE_ALGUNA.value[0]
            ):
                queryset = queryset.filter(añomateria__año__in=años_asignados)

            # busqueda de ningún año asignado en la lista
            elif (
                tipo_busqueda_anios
                == FiltrosConjuntoOpciones.NO_CONTIENE_ALGUNA.value[0]
            ):
                queryset = queryset.exclude(añomateria__año__in=años_asignados)

        return queryset.prefetch_related(
            Prefetch(
                "añomateria_set",
                queryset=AñoMateria.objects.all(),
                to_attr="asignaciones",
            )
        )

    def get_context_data(self, *args, **kwargs):
        if not self.object_list:
            return super().get_context_data(*args, **kwargs)

        ctx = super().get_context_data(*args, **kwargs)

        ctx["form_asignaciones"] = self.form_asignaciones()
        return ctx

    def actualizar(self, request, ids, datos, *args, **kwargs):
        form = self.form_asignaciones(datos)

        if not form.is_valid():
            return HttpResponseBadRequest("La lista de años es inválida")

        materias = Materia.objects.filter(id__in=ids)
        asignaciones: list[Año] = form.cleaned_data["asignaciones"]

        if len(materias):
            # eliminar las asignaciones que no estén en la lista
            AñoMateria.objects.filter(materia__in=materias).exclude(
                año__in=asignaciones
            ).delete()

            if len(asignaciones):
                asignadas = 0
                for materia in materias:
                    asignadas = len(
                        AñoMateria.objects.bulk_create(
                            (
                                AñoMateria(año=año, materia=materia)
                                for año in asignaciones
                            ),
                            ignore_conflicts=True,
                        )
                    )

                if asignadas > 0:
                    messages.success(
                        request,
                        "Las materias seleccionadas fueron asignadas a los años seleccionados correctamente",
                        "retraso=8000",
                    )
                else:
                    messages.error(
                        request,
                        "No se pudieron actualizar las materias seleccionadas",
                    )
            else:
                messages.success(
                    request,
                    "Las materias seleccionadas fueron desasignadas de todos los años correctamente",
                    "retraso=8000",
                )
        else:
            messages.error(
                request,
                "No se pudieron actualizar las materias seleccionadas",
            )


class CrearMateria(VistaCrearObjeto):
    template_name = "parametros/materias/form.html"
    model = Materia
    form_class = FormMateria
    genero_sustantivo_objeto = "F"

    def form_valid(self, form):
        años_seleccionados: list[Año] = list(form.cleaned_data["asignaciones"])
        materia: Materia = self.object  # type: ignore

        if len(años_seleccionados):
            AñoMateria.objects.bulk_create(
                [AñoMateria(año=año, materia=materia) for año in años_seleccionados]
            )

        return super().form_valid(form)


class ActualizarMateria(VistaActualizarObjeto):
    template_name = "parametros/materias/form.html"
    model = Materia
    form_class = FormMateria
    genero_sustantivo_objeto = "F"

    def form_valid(self, form):
        años_seleccionados: list[Año] = list(form.cleaned_data["asignaciones"])

        if len(años_seleccionados):
            materia: Materia = self.object
            todos_los_años = Año.objects.all()
            asignados: list[int] = list(
                AñoMateria.objects.filter(materia=materia).values_list(
                    "año_id", flat=True
                )
            )

            años_a_asignar = []

            for año in todos_los_años:
                if años_seleccionados.__contains__(año) and not asignados.__contains__(
                    año.id  # type: ignore
                ):
                    años_a_asignar.append(año)

            AñoMateria.objects.filter(materia=self.object).exclude(
                año__in=años_seleccionados
            ).delete()

            if len(años_a_asignar):
                AñoMateria.objects.bulk_create(
                    [AñoMateria(año=año, materia=self.object) for año in años_a_asignar]
                )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # recuperar las asignaciones actuales
        ctx["form"].fields["asignaciones"].initial = list(
            AñoMateria.objects.filter(materia=self.object).values_list(
                "año_id", flat=True
            )
        )

        return ctx


class ListaAños(VistaListaObjetos):
    template_name = "parametros/años/index.html"
    plantilla_lista = "parametros/años/lista.html"
    model = Año

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(Año.objects.all())


class CrearAño(VistaCrearObjeto):
    template_name = "parametros/años/form.html"
    model = Año
    form_class = FormAño


class ActualizarAño(VistaActualizarObjeto):
    template_name = "parametros/años/form.html"
    model = Año
    form_class = FormAño


class ListaSecciones(VistaListaObjetos):
    template_name = "parametros/secciones/index.html"
    plantilla_lista = "parametros/secciones/lista.html"
    model = Seccion
    genero_sustantivo_objeto = "F"
    form_filtros = SeccionBusquedaForm
    agrupados = True

    def get_queryset(self, *args, **kwargs):
        q = self.model.objects.annotate(cantidad_matriculas=Count("matricula")).all()
        return super().get_queryset(q)

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if letra := datos_form.get(SeccionBusquedaForm.Campos.LETRA):
            queryset = queryset.filter(letra__in=letra)

        if (
            vocero := obtener_filtro_bool_o_nulo(
                SeccionBusquedaForm.Campos.VOCERO, datos_form
            )
        ) is not None:
            valor_filtro = Q(vocero__isnull=True)

            if vocero:
                queryset = queryset.exclude(valor_filtro)
            else:
                queryset = queryset.filter(valor_filtro)

        if disponibilidad := datos_form.get(SeccionBusquedaForm.Campos.DISPONIBILIDAD):
            if disponibilidad == OpcionesFormSeccion.Disponibilidad.LLENA.value[0]:
                queryset = queryset.filter(cantidad_matriculas__gte=F("capacidad"))
            elif (
                disponibilidad == OpcionesFormSeccion.Disponibilidad.DISPONIBLE.value[0]
            ):
                queryset = queryset.filter(cantidad_matriculas__lt=F("capacidad"))
            elif disponibilidad == OpcionesFormSeccion.Disponibilidad.VACIA.value[0]:
                queryset = queryset.filter(cantidad_matriculas=0)

        return queryset

    def agrupar_queryset(self, lista_objetos):
        return (
            Año.objects.annotate(Count("seccion"))
            .filter(seccion__in=lista_objetos.values("id"))
            .prefetch_related(
                Prefetch(
                    "seccion_set",
                    queryset=lista_objetos,
                    to_attr="secciones",
                )
            )
        )


class CrearSeccion(VistaCrearObjeto):
    template_name = "parametros/secciones/form.html"
    model = Seccion
    form_class = FormSeccion
    genero_sustantivo_objeto = "F"

    def get_initial(self):
        if (año := self.request.GET.get("año")) and año.isdecimal():
            if año := Año.objects.filter(id=año).first():
                return {
                    "año": año,
                }

        return {}


class ActualizarSeccion(VistaActualizarObjeto):
    template_name = "parametros/secciones/form.html"
    model = Seccion
    form_class = FormSeccion
    genero_sustantivo_objeto = "F"
