from django.db.models.functions.datetime import TruncMinute
from django.http import (
    HttpRequest,
)
from django.shortcuts import redirect
from django.db.models import Case, Q, F, Value, When
from app.vistas import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
    VistaListaObjetos,
)
from estudios.forms.gestion.personas import (
    FormMatricula,
)
from estudios.forms.gestion.busqueda import (
    MatriculaBusquedaForm,
)
from estudios.modelos.gestion.personas import (
    MatriculaEstados,
    Matricula,
)
from estudios.modelos.parametros import Lapso
from django.db.models.functions import Concat
from django.contrib import messages
from estudios.modelos.parametros import obtener_lapso_actual
from estudios.vistas.gestion import aplicar_filtros_secciones_y_lapsos


class ListaMatriculas(VistaListaObjetos):
    template_name = "gestion/matriculas/index.html"
    plantilla_lista = "gestion/matriculas/lista.html"
    model = Matricula
    genero_sustantivo_objeto = "F"
    form_filtros = MatriculaBusquedaForm  # type: ignore
    paginate_by = 50
    columnas_totales = (
        {"titulo": "Estudiante", "clave": "estudiante_nombres"},
        {"titulo": "Cédula", "clave": "estudiante_cedula", "alinear": "derecha"},
        {"titulo": "Sección", "clave": "seccion_nombre"},
        {"titulo": "Estado", "clave": "estado"},
        {"titulo": "Lapso", "clave": "lapso_nombre"},
        {"titulo": "Fecha de añadida", "clave": "fecha"},
    )
    columnas_a_evitar = set()
    estados_opciones = dict(MatriculaEstados.choices)
    lapso_actual: "Lapso | None" = None

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(
            Matricula.objects.annotate(
                seccion_nombre=F("seccion__nombre"),
                estudiante_cedula=F("estudiante__cedula"),
                lapso_nombre=F("lapso__nombre"),
                estudiante_nombres=Concat(
                    "estudiante__nombres", Value(" "), "estudiante__apellidos"
                ),
                fecha=TruncMinute("fecha_añadida"),
                # no se pueden modificar las matriculas de un lapso distinto al actual
                no_modificable=Case(
                    When(Q(lapso=obtener_lapso_actual()), then=0), default=1
                ),
                # no se pueden seleccionar las matriculas de un lapso distinto al actual
                no_seleccionable=F("no_modificable"),
            ).order_by(
                "-lapso__id",
                "-fecha_añadida",
                "seccion__letra",
                "estudiante__apellidos",
                "estudiante__nombres",
            )
        )

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        queryset = aplicar_filtros_secciones_y_lapsos(
            self, queryset, datos_form, "seccion"
        )

        if estado := self.obtener_y_alternar("estado", datos_form, "estado"):
            queryset = queryset.filter(estado=estado)

        return queryset

    def get(self, request: HttpRequest, *args, **kwargs):
        self.lapso_actual = obtener_lapso_actual()
        return super().get(request, *args, **kwargs)

    def eliminar_seleccionados(self, ids):
        return Matricula.objects.filter(id__in=ids, lapso=self.lapso_actual).delete()


class CrearMatricula(VistaCrearObjeto):
    template_name = "gestion/matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"


class ActualizarMatricula(VistaActualizarObjeto):
    template_name = "gestion/matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"

    def no_se_puede_actualizar(self, request: HttpRequest):
        if self.object.lapso != obtener_lapso_actual():  # type: ignore
            messages.error(
                request,
                "No se puede actualizar una matricula de un lapso distinto al actual",
            )
            return True

    def get(self, request: HttpRequest, *args, **kwargs):
        r = super().get(request, *args, **kwargs)

        if self.no_se_puede_actualizar(request):
            return redirect(self.success_url)  # type: ignore

        return r

    def post(self, request: HttpRequest, *args, **kwargs):
        r = super().post(request, *args, **kwargs)

        if self.no_se_puede_actualizar(request):
            return redirect(self.success_url)  # type: ignore

        return r
