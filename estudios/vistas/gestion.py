from typing import Any, Mapping
from django.db import models
from django.db.models.functions.datetime import TruncMinute
from django.http import (
    HttpRequest,
)
from django.shortcuts import redirect, render
from django.db.models import Case, Q, F, Value, When
from django.urls import reverse_lazy
from app.vistas import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
    VistaListaObjetos,
)
from estudios.forms.gestion import (
    FormMatricula,
)
from estudios.forms.gestion.busqueda import (
    MatriculaBusquedaForm,
    NotasBusquedaForm,
)
from estudios.modelos.gestion import (
    MatriculaEstados,
    Matricula,
    Nota,
)
from estudios.modelos.parametros import Materia, Lapso
from django.db.models.functions import Concat
from django.contrib import messages
from estudios.modelos.parametros import obtener_lapso_actual


def inicio(request: HttpRequest):
    return render(request, "gestion/inicio.html")


def aplicar_filtros_secciones_y_lapsos(
    cls: VistaListaObjetos,
    queryset: models.QuerySet,
    datos_form: "dict[str, Any] | Mapping[str, Any]",
    seccion_col_nombre: str = "seccion",
    lapso_col_nombre: str = "lapso",
):
    if secciones := cls.obtener_y_alternar("secciones", datos_form, "seccion_nombre"):
        kwargs = {f"{seccion_col_nombre}_id__in": secciones}
        queryset = queryset.filter(**kwargs)

    if lapsos := cls.obtener_y_alternar("lapsos", datos_form, "lapso_nombre"):
        kwargs = {f"{lapso_col_nombre}_id__in": lapsos}
        queryset = queryset.filter(**kwargs)

    return queryset


class ListaNotas(VistaListaObjetos):
    model = Nota
    template_name = "gestion/notas/index.html"
    plantilla_lista = "gestion/notas/lista.html"
    paginate_by = 50
    form_filtros = NotasBusquedaForm  # type: ignore
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
            materia_nombre=F("materia__nombre"),
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


class ListaMatriculas(VistaListaObjetos):
    template_name = "gestion/matriculas/index.html"
    plantilla_lista = "gestion/matriculas/lista.html"
    nombre_url_editar = "editar_matricula"
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
    success_url = reverse_lazy("matriculas")


class ActualizarMatricula(VistaActualizarObjeto):
    template_name = "gestion/matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"
    success_url = reverse_lazy("matriculas")

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
