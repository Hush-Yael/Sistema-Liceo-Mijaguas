from typing import Any, Mapping
from django.db import models
from django.db.models.functions.datetime import TruncMinute
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
)
from django.http.request import QueryDict
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, Q, F, Value, When
from django.urls import reverse_lazy
from app.vistas import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
    VistaListaObjetos,
)
from estudios.formularios import (
    FormAsignaciones,
    FormLapso,
    FormMateria,
    FormMatricula,
    FormSeccion,
    FormAño,
)
from estudios.formularios_busqueda import (
    OPCION_BUSCAR_NOMBRES_Y_APELLIDOS,
    AsignacionesBuscarTipoOpciones,
    MateriaBusquedaForm,
    MatriculaBusquedaForm,
    NotasBusquedaForm,
    OpcionesFormSeccion,
    SeccionBusquedaForm,
)
from .models import (
    Lapso,
    MatriculaEstados,
    Seccion,
    Año,
    Estudiante,
    Materia,
    Profesor,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Nota,
    obtener_lapso_actual,
)
from django.db.models.functions import Concat
from django.contrib import messages


def inicio(request: HttpRequest):
    contexto = {
        "cantidades": {
            "materias": Materia.objects.count(),
            "profesores": Profesor.objects.count(),
            "estudiantes": Estudiante.objects.count(),
        }
    }

    if request.user.is_superuser:  # type: ignore
        """ contexto["profesores"] = ProfesorMateria.objects.values(
            "materia", "año", "profesor"
        ) """
        """ materias_año = (
            AñoMateria.objects.select_related("año", "materia")
            # .prefetch_related()
            .order_by("año__numero", "materia__nombre")
        )
        print(materias_año) """

    return render(request, "inicio.html", contexto)


def aplicar_filtros_secciones_y_lapsos(
    cls: VistaListaObjetos,
    queryset: models.QuerySet,
    datos_form: "dict[str, Any] | Mapping[str, Any]",
    seccion_col_nombre: str = "seccion",
    lapso_col_nombre: str = "lapso",
):
    if secciones := datos_form.get("secciones"):  # type: ignore
        kwargs = {f"{seccion_col_nombre}_id__in": secciones}
        queryset = queryset.filter(**kwargs)
        cls.columnas_a_evitar.add("seccion_nombre")
    else:
        cls.columnas_a_evitar.discard("seccion_nombre")

    if lapsos := datos_form.get("lapsos"):  # type: ignore
        kwargs = {f"{lapso_col_nombre}_id__in": lapsos}
        queryset = queryset.filter(**kwargs)
        cls.columnas_a_evitar.add("lapso_nombre")
    else:
        cls.columnas_a_evitar.discard("lapso_nombre")

    return queryset


def aplicar_busqueda_estudiante(
    queryset: models.QuerySet,
    datos_form: "dict[str, Any] | Mapping[str, Any]",
    estudiante_col_nombre: str,
):
    busqueda = datos_form.get("q")
    if isinstance(busqueda, str) and busqueda.strip() != "":
        tipo_busqueda = datos_form.get("tipo_busqueda")
        columna_buscada = datos_form.get("columna_buscada")

        columna_y_valor = {f"{columna_buscada}__{tipo_busqueda}": busqueda}

        if columna_buscada == OPCION_BUSCAR_NOMBRES_Y_APELLIDOS[0]:
            valor_compuesto = {
                f"{columna_buscada}": Concat(
                    f"{estudiante_col_nombre}__nombres",
                    Value(" "),
                    f"{estudiante_col_nombre}__apellidos",
                )
            }
            queryset = queryset.annotate(**valor_compuesto).filter(**columna_y_valor)
        else:
            queryset = queryset.filter(**columna_y_valor)

    return queryset


class ListaNotas(VistaListaObjetos):
    model = Nota
    template_name = "notas/index.html"
    paginate_by = 50
    form_filtros = NotasBusquedaForm  # type: ignore
    columnas_a_evitar = set()
    columnas_totales = (
        {"titulo": "Estudiante", "clave": "estudiante_nombres", "anotada": True},
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
        queryset = aplicar_filtros_secciones_y_lapsos(
            self,
            queryset,
            datos_form,
            seccion_col_nombre="matricula__seccion",
            lapso_col_nombre="matricula__lapso",
        )

        if materias := datos_form.get("materias"):  # type: ignore
            queryset = queryset.filter(materia_id__in=materias)
            self.columnas_a_evitar.add("materia")
        else:
            self.columnas_a_evitar.discard("materia")

        nota_minima = float(datos_form.get("valor_minimo", 0))  # type: ignore
        nota_maxima = float(datos_form.get("valor_maximo", 20))  # type: ignore

        if nota_minima <= nota_maxima:
            queryset = queryset.filter(valor__range=(nota_minima, nota_maxima))

        queryset = aplicar_busqueda_estudiante(
            queryset, datos_form, "matricula__estudiante"
        )

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


class ListaMaterias(VistaListaObjetos):
    template_name = "materias/index.html"
    model = Materia
    form_asignaciones = FormAsignaciones
    genero_sustantivo_objeto = "F"
    lista_años: "list[dict]"
    form_filtros = MateriaBusquedaForm  # type: ignore
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
        if años_asignados := datos_form.get("anios_asignados"):
            tipo_busqueda_anios = (
                datos_form.get(
                    "tipo_busqueda_anios",
                )
                or self.form_filtros.fields["tipo_busqueda_anios"].initial[0]
            )

            # busqueda exacta de años asignados, ya sea todos o ninguno
            if (
                todos := tipo_busqueda_anios
                == AsignacionesBuscarTipoOpciones.TODOS.value[0]
            ) or tipo_busqueda_anios == AsignacionesBuscarTipoOpciones.NO_TODOS.value[
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

            # busqueda de al menos un año asignado o no asignado en la lista
            elif (
                algunos := tipo_busqueda_anios
                == AsignacionesBuscarTipoOpciones.ALGUNOS.value[0]
            ) or tipo_busqueda_anios == AsignacionesBuscarTipoOpciones.NO_ALGUNOS.value[
                0
            ]:
                if algunos:
                    queryset = queryset.filter(añomateria__año__in=años_asignados)
                else:
                    queryset = queryset.exclude(añomateria__año__in=años_asignados)

        busqueda = datos_form.get("q")

        if isinstance(busqueda, str) and busqueda.strip() != "":
            tipo_busqueda = datos_form.get("tipo_busqueda")
            columna_y_valor = {f"nombre__{tipo_busqueda}": busqueda}
            queryset = queryset.filter(**columna_y_valor)

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

    def put(self, request: HttpRequest, *args, **kwargs):
        datos = QueryDict(request.body)  # type: ignore

        if not (ids := datos.getlist("ids")):
            return HttpResponseBadRequest("No se indicó una lista de ids")

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

        self.object_list = self.get_queryset()

        ctx = self.get_context_data(*args, **kwargs)
        ctx["tabla_reemplazada_por_htmx"] = 1

        return render(
            request,
            f"{self.template_name}#respuesta_cambios_tabla",
            ctx,
        )


class CrearMateria(VistaCrearObjeto):
    template_name = "materias/form.html"
    model = Materia
    form_class = FormMateria
    genero_sustantivo_objeto = "F"
    success_url = reverse_lazy("materias")

    def form_valid(self, form):
        años_seleccionados: list[Año] = list(form.cleaned_data["asignaciones"])
        materia: Materia = self.object  # type: ignore

        if len(años_seleccionados):
            AñoMateria.objects.bulk_create(
                [AñoMateria(año=año, materia=materia) for año in años_seleccionados]
            )

        return super().form_valid(form)


class ActualizarMateria(VistaActualizarObjeto):
    template_name = "materias/form.html"
    model = Materia
    form_class = FormMateria
    genero_sustantivo_objeto = "F"
    success_url = reverse_lazy("materias")

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


class ListaLapsos(VistaListaObjetos):
    template_name = "lapsos/index.html"
    model = Lapso

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        return super().get_queryset(Lapso.objects.all().order_by("numero"))

    def establecer_columnas(self):
        super().establecer_columnas()
        self.columnas_mostradas[0]["alinear"] = "derecha"
        col_n_lapso = self.columnas_mostradas.pop(0)
        self.columnas_mostradas.insert(1, col_n_lapso)


class CrearLapso(VistaCrearObjeto):
    template_name = "lapsos/form.html"
    model = Lapso
    form_class = FormLapso
    success_url = reverse_lazy("lapsos")


class ActualizarLapso(VistaActualizarObjeto):
    template_name = "lapsos/form.html"
    model = Lapso
    form_class = FormLapso
    success_url = reverse_lazy("lapsos")


class ListaAños(VistaListaObjetos):
    template_name = "años/index.html"
    model = Año

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(Año.objects.all())


class CrearAño(VistaCrearObjeto):
    template_name = "años/form.html"
    model = Año
    form_class = FormAño
    success_url = reverse_lazy("años")


class ActualizarAño(VistaActualizarObjeto):
    template_name = "años/form.html"
    model = Año
    form_class = FormAño
    success_url = reverse_lazy("años")


class ListaSecciones(VistaListaObjetos):
    template_name = "secciones/index.html"
    model = Seccion
    paginate_by = 50
    genero_sustantivo_objeto = "F"
    form_filtros = SeccionBusquedaForm  # type: ignore
    columnas_a_evitar = set()
    columnas_totales = (
        {"titulo": "Año", "clave": "nombre_año", "anotada": True},
        {"titulo": "Nombre", "clave": "nombre"},
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
    columnas_texto = tuple(
        o[0] for o in OpcionesFormSeccion.ColumnasTexto._value2member_map_
    )

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        return super().get_queryset(
            Seccion.objects.annotate(
                nombre_año=F("año__nombre"),
                vocero_nombre=Concat(
                    F("vocero__nombres"), Value(" "), F("vocero__apellidos")
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
        if año := datos_form.get("anio"):  # type: ignore
            queryset = queryset.filter(año__in=año)
            self.columnas_a_evitar.add("año")
        else:
            self.columnas_a_evitar.discard("año")

        if letra := datos_form.get("letra"):  # type: ignore
            queryset = queryset.filter(letra__in=letra)
            self.columnas_a_evitar.add("letra")
        else:
            self.columnas_a_evitar.discard("letra")

        if vocero := datos_form.get("vocero"):
            if vocero == self.form_filtros.OpcionesVocero.CON_VOCERO.value[0]:  # type: ignore
                queryset = queryset.filter(vocero__isnull=False)
            elif vocero == self.form_filtros.OpcionesVocero.SIN_VOCERO.value[0]:  # type: ignore
                queryset = queryset.filter(vocero__isnull=True)

            self.columnas_a_evitar.add("vocero")
        else:
            self.columnas_a_evitar.discard("vocero")

        if disponibilidad := datos_form.get("disponibilidad"):
            if disponibilidad == OpcionesFormSeccion.Disponibilidad.LLENA.value[0]:
                queryset = queryset.filter(cantidad_matriculas__gte=F("capacidad"))
            elif (
                disponibilidad == OpcionesFormSeccion.Disponibilidad.DISPONIBLE.value[0]
            ):
                queryset = queryset.filter(cantidad_matriculas__lt=F("capacidad"))
            elif disponibilidad == OpcionesFormSeccion.Disponibilidad.VACIA.value[0]:
                queryset = queryset.filter(cantidad_matriculas=0)

        busqueda = datos_form.get("q")

        if isinstance(busqueda, str) and busqueda.strip() != "":
            columna_buscada = datos_form.get("columna_buscada")

            opcion_de_texto = columna_buscada in self.columnas_texto

            if opcion_de_texto:
                tipo_busqueda = datos_form.get("tipo_busqueda_texto")

                columna_y_valor = {f"{columna_buscada}__{tipo_busqueda}": busqueda}

                if (
                    columna_buscada
                    == OpcionesFormSeccion.ColumnasTexto.NOMBRE_VOCERO.value[0]
                ):
                    valor_compuesto = {
                        f"{columna_buscada}": Concat(
                            F("vocero__nombres"), Value(" "), F("vocero__apellidos")
                        )
                    }

                    queryset = queryset.annotate(**valor_compuesto)

                queryset = queryset.filter(**columna_y_valor)
            else:
                try:
                    busqueda = int(busqueda)
                    tipo_busqueda = datos_form.get("tipo_busqueda_numerica")
                    columna_y_valor = {f"{columna_buscada}__{tipo_busqueda}": busqueda}

                    queryset = queryset.filter(**columna_y_valor)
                except (ValueError, TypeError):
                    pass

        return queryset


class CrearSeccion(VistaCrearObjeto):
    template_name = "secciones/form.html"
    model = Seccion
    form_class = FormSeccion
    genero_sustantivo_objeto = "F"
    success_url = reverse_lazy("secciones")


class ActualizarSeccion(VistaActualizarObjeto):
    template_name = "secciones/form.html"
    model = Seccion
    form_class = FormSeccion
    genero_sustantivo_objeto = "F"
    success_url = reverse_lazy("secciones")


class ListaMatriculas(VistaListaObjetos):
    template_name = "matriculas/index.html"
    model = Matricula
    genero_sustantivo_objeto = "F"
    form_filtros = MatriculaBusquedaForm  # type: ignore
    paginate_by = 50
    columnas_totales = (
        {"titulo": "Estudiante", "clave": "estudiante_nombres"},
        {"titulo": "Sección", "clave": "seccion_nombre"},
        {"titulo": "Estado", "clave": "estado"},
        {"titulo": "Lapso", "clave": "lapso_nombre"},
        {"titulo": "Fecha de añadida", "clave": "fecha_añadida"},
    )
    columnas_a_evitar = set()
    estados_opciones = dict(MatriculaEstados.choices)
    lapso_actual: "Lapso | None" = None

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(
            Matricula.objects.annotate(
                seccion_nombre=F("seccion__nombre"),
                lapso_nombre=F("lapso__nombre"),
                estudiante_nombres=Concat(
                    "estudiante__nombres", Value(" "), "estudiante__apellidos"
                ),
                fecha=TruncMinute("fecha_añadida"),
                # no se pueden seleccionar las matriculas de un lapso distinto al actual
                no_seleccionable=Case(
                    When(Q(lapso=obtener_lapso_actual()), then=0), default=1
                ),
            ).order_by(
                "-lapso__id",
                "-fecha",
                "seccion__letra",
                "estudiante__apellidos",
                "estudiante__nombres",
            )
        )

    def aplicar_filtros(self, queryset, datos_form):
        queryset = aplicar_filtros_secciones_y_lapsos(
            self, queryset, datos_form, "seccion"
        )

        if estado := datos_form.get("estado"):
            queryset = queryset.filter(estado=estado)
            self.columnas_a_evitar.add("estado")
        else:
            self.columnas_a_evitar.discard("estado")

        queryset = aplicar_busqueda_estudiante(queryset, datos_form, "estudiante")

        return queryset

    def get(self, request: HttpRequest, *args, **kwargs):
        self.lapso_actual = obtener_lapso_actual()
        return super().get(request, *args, **kwargs)

    def eliminar_seleccionados(self, ids):
        return Matricula.objects.filter(id__in=ids, lapso=self.lapso_actual).delete()


class CrearMatricula(VistaCrearObjeto):
    template_name = "matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"
    success_url = reverse_lazy("matriculas")


class ActualizarMatricula(VistaActualizarObjeto):
    template_name = "matriculas/form.html"
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


def estudiantes_por_seccion(request, año_id):
    """Consulta para ver estudiantes por sección"""
    secciones = Seccion.objects.filter(año_id=año_id).prefetch_related(
        "matricula_set__estudiante"
    )

    data = []
    for seccion in secciones:
        estudiantes = [
            mat.estudiante for mat in seccion.matricula_set.filter(estado="activo")
        ]
        data.append(
            {"seccion": seccion, "estudiantes": estudiantes, "total": len(estudiantes)}
        )

    return render(request, "consultas/estudiantes_por_seccion.html", {"data": data})


def profesores_por_seccion(request, seccion_id):
    """Consulta para ver profesores que enseñan en una sección"""
    seccion = Seccion.objects.get(id=seccion_id)
    profesores_materias = ProfesorMateria.objects.filter(
        seccion=seccion
    ).select_related("profesor", "materia")

    return render(
        request,
        "consultas/profesores_seccion.html",
        {"seccion": seccion, "profesores_materias": profesores_materias},
    )


@login_required
def materias_por_año_con_profesores(request: HttpRequest):
    """Consulta para ver materias por año con sus profesores"""
    materias_año = (
        AñoMateria.objects.select_related("año", "materia")
        .prefetch_related("profesormateria_set__profesor")
        .order_by("año__numero", "materia__nombre")
    )

    return render(
        request, "consultas/materias_profesores.html", {"materias_año": materias_año}
    )


@login_required
def profesores_y_materias(request: HttpRequest):
    """Profesores y las materias que imparten"""
    profesores_materias = ProfesorMateria.objects.select_related(
        "profesor", "materia", "año"
    ).order_by("profesor__apellido", "año__nombre")

    return render(
        request,
        "consultas/profesores_materias.html",
        {"profesores_materias": profesores_materias},
    )


@login_required
def resumen_matriculas_por_año(request: HttpRequest):
    """Resumen de matrículas por año"""
    resumen = (
        Matricula.objects.values("año__id", "año__nombre", "año__numero")
        .annotate(
            total_estudiantes=Count("estudiante_cedula"),
            estudiantes_activos=Count(
                "estudiante_cedula",
                filter=Q(estudiante__estado="activo"),
                distinct=True,
            ),
        )
        .order_by("año__numero")
    )

    return render(request, "consultas/resumen_matriculas.html", {"resumen": resumen})
