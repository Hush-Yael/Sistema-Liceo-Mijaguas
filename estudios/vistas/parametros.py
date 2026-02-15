from typing import Any, Mapping
from django.db import models
from django.db.models.functions.datetime import TruncMinute
from django.http import (
    HttpResponseBadRequest,
)
from django.db.models import Case, Count, Q, F, Value, When
from app.campos import FiltrosConjuntoOpciones
from app.forms import ConjuntoOpcionesForm
from app.util import obtener_filtro_bool_o_nulo
from app.vistas import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
    VistaListaObjetos,
)
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
)
from django.db.models.functions import Concat


class ListaLapsos(VistaListaObjetos):
    template_name = "parametros/lapsos/index.html"
    plantilla_lista = "parametros/lapsos/lista.html"
    nombre_url_editar = "editar_lapso"
    model = Lapso
    form_filtros = LapsoBusquedaForm  # type: ignore

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        return super().get_queryset(Lapso.objects.all().order_by("-id", "numero"))

    def establecer_columnas(self):
        super().establecer_columnas()
        self.columnas_mostradas[0]["alinear"] = "derecha"
        col_n_lapso = self.columnas_mostradas.pop(0)
        self.columnas_mostradas.insert(1, col_n_lapso)


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
    nombre_url_editar = "editar_materia"
    model = Materia
    form_filtros = MateriaBusquedaForm  # type: ignore
    form_asignaciones = FormAsignaciones
    genero_sustantivo_objeto = "F"
    lista_años: "list[dict]"
    columnas_totales = (
        {"titulo": "Nombre", "clave": "nombre"},
        {"clave": "asignaciones", "titulo": "Años asignados", "anotada": True},
        {"clave": "fecha", "titulo": "Fecha de creación", "anotada": True},
    )

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        queryset = (
            Materia.objects.annotate(
                fecha=TruncMinute("fecha_creacion"),
            )
            .values(
                "id",
                "nombre",
                "fecha",
            )
            .order_by("nombre")
        )

        materias = super().get_queryset(queryset)

        if materias:
            años = Año.objects.values("id", "nombre_corto")
            self.lista_años = list(años)
            asignaciones = list(AñoMateria.objects.values("año_id", "materia__id"))

            for materia in materias:
                materia["asignaciones"] = [
                    asignacion["año_id"]
                    for asignacion in asignaciones
                    if (asignacion["materia__id"] == materia["id"])
                ]

        return materias

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

        return queryset

    def get_context_data(self, *args, **kwargs):
        if not self.object_list:
            return super().get_context_data(*args, **kwargs)

        ctx = super().get_context_data(*args, **kwargs)
        ctx.update(
            {
                "lista_años": self.lista_años,
                "form_asignaciones": self.form_asignaciones(),
            }
        )
        return ctx

    def actualizar(self, request, ids, datos, *args, **kwargs):
        form = self.form_asignaciones(datos)

        if not form.is_valid():
            return HttpResponseBadRequest("La lista de años es inválida")

        asignaciones = form.cleaned_data["asignaciones"]
        años = Año.objects.filter(id__in=asignaciones)

        for id in ids:
            materia = Materia.objects.get(id=id)
            AñoMateria.objects.filter(materia=materia).delete()

            if asignaciones:
                AñoMateria.objects.bulk_create(
                    [AñoMateria(año=año, materia=materia) for año in años]
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
    nombre_url_editar = "editar_año"
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
    nombre_url_editar = "editar_seccion"
    model = Seccion
    paginate_by = 50
    genero_sustantivo_objeto = "F"
    form_filtros = SeccionBusquedaForm  # type: ignore
    columnas_a_evitar = set()
    columnas_totales = (
        {"titulo": "Nombre", "clave": "nombre"},
        {"titulo": "Año", "clave": "nombre_año", "anotada": True},
        {"titulo": "Letra", "clave": "letra"},
        {"titulo": "Capacidad", "clave": "capacidad", "alinear": "derecha"},
        {
            "titulo": "Alumnos",
            "clave": "cantidad_matriculas",
            "alinear": "derecha",
            "anotada": True,
        },
        {"titulo": "Vocero", "clave": "vocero_nombre", "anotada": True},
    )
    opciones_columnas_texto = tuple(
        o[0] for o in OpcionesFormSeccion.ColumnasTexto._value2member_map_
    )

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        return super().get_queryset(
            Seccion.objects.annotate(
                nombre_año=F("año__nombre"),
                vocero_nombre=Case(
                    When(
                        vocero__isnull=False,
                        then=Concat(
                            F("vocero__nombres"), Value(" "), F("vocero__apellidos")
                        ),
                    ),
                    default=None,
                ),
                cantidad_matriculas=Count(
                    "matricula", filter=Q(matricula__estado="activo")
                ),
            ).only(
                *(
                    col["clave"]
                    for col in self.columnas_mostradas
                    if not col.get("anotada", False)
                )
            )
        )

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if año := self.obtener_y_alternar(
            SeccionBusquedaForm.Campos.ANIO, datos_form, "año"
        ):
            queryset = queryset.filter(año__in=año)

        if letra := self.obtener_y_alternar(
            SeccionBusquedaForm.Campos.LETRA, datos_form, "letra"
        ):
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
        self.alternar_col_por_filtro(vocero, "vocero")

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


class CrearSeccion(VistaCrearObjeto):
    template_name = "parametros/secciones/form.html"
    model = Seccion
    form_class = FormSeccion
    genero_sustantivo_objeto = "F"


class ActualizarSeccion(VistaActualizarObjeto):
    template_name = "parametros/secciones/form.html"
    model = Seccion
    form_class = FormSeccion
    genero_sustantivo_objeto = "F"
