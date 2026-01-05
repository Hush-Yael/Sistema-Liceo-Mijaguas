from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
)
from django.http.request import QueryDict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.urls import reverse_lazy
from app.vistas import VistaActualizarObjeto, VistaCrearObjeto, VistaListaObjetos
from estudios.formularios import FormAsignaciones, FormLapso, FormMateria, FormAño
from estudios.formularios_busqueda import NotasBusquedaForm
from .models import (
    Lapso,
    Seccion,
    Año,
    Estudiante,
    Materia,
    Profesor,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Nota,
)


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


def al_menos_un_filtro_aplicado(lista: "list[str]"):
    if lista and ((len(lista) == 1 and lista[0] != "") or len(lista) > 1):
        return lista
    return None


class ListaNotas(VistaListaObjetos):
    model = Nota
    template_name = "notas/index.html"
    paginate_by = 50
    form_filtros = NotasBusquedaForm  # type: ignore
    todas_las_columnas = [
        {
            "nombre_col": "matricula__estudiante",
            "titulo": "Estudiante",
            "clave": "estudiante",
        },
        {"nombre_col": "materia", "titulo": "Materia", "clave": "materia"},
        {
            "nombre_col": "matricula__seccion__nombre",
            "titulo": "Sección",
            "clave": "seccion_nombre",
        },
        {
            "nombre_col": "valor",
            "titulo": "Valor",
            "clave": "valor",
            "alinear": "derecha",
        },
        {
            "nombre_col": "matricula__lapso__nombre",
            "titulo": "Lapso",
            "clave": "lapso_nombre",
            "alinear": "derecha",
        },
        {"nombre_col": "fecha", "titulo": "Fecha", "clave": "fecha"},
    ]

    def establecer_columnas(self):
        self.columnas = list(
            filter(
                lambda col: col["clave"] not in self.columnas_a_evitar,
                self.todas_las_columnas,
            )
        )

        self.columnas_ocultables = list(
            map(lambda col: col["titulo"], self.columnas[1:])
        )

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        queryset = Nota.objects.annotate(
            seccion_nombre=F("matricula__seccion__nombre"),
            lapso_nombre=F("matricula__lapso__nombre"),
        ).only(*[col["nombre_col"] for col in self.todas_las_columnas])

        self.total = queryset.count()

        return super().get_queryset(queryset)

    def aplicar_filtros(self, queryset, datos_request, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_request, datos_form)

        if secciones := al_menos_un_filtro_aplicado(datos_form.get("notas_secciones")):  # type: ignore
            queryset = queryset.filter(matricula__seccion_id__in=secciones)
            self.columnas_a_evitar.add("seccion_nombre")
        else:
            self.columnas_a_evitar.discard("seccion_nombre")

        if lapsos := al_menos_un_filtro_aplicado(datos_form.get("notas_lapsos")):  # type: ignore
            queryset = queryset.filter(matricula__lapso_id__in=lapsos)
            self.columnas_a_evitar.add("lapso_nombre")
        else:
            self.columnas_a_evitar.discard("lapso_nombre")

        if materias := al_menos_un_filtro_aplicado(datos_form.get("notas_materias")):  # type: ignore
            queryset = queryset.filter(materia_id__in=materias)
            self.columnas_a_evitar.add("materia")
        else:
            self.columnas_a_evitar.discard("materia")

        nota_minima = float(datos_form.get("notas_valor_minimo", 0))  # type: ignore
        nota_maxima = float(datos_form.get("notas_valor_maximo", 20))  # type: ignore

        if nota_minima <= nota_maxima:
            queryset = queryset.filter(valor__range=(nota_minima, nota_maxima))

        busqueda = datos_request.get("q")
        if isinstance(busqueda, str) and busqueda.strip() != "":
            tipo_busqueda = datos_form["notas_tipo_busqueda"]
            columna_buscada = datos_form["notas_columna_buscada"]

            if columna_buscada == "nombres_y_apellidos":
                queryset = queryset.filter(
                    Q(matricula__estudiante__nombres__icontains=busqueda)
                    | Q(matricula__estudiante__apellidos__icontains=busqueda)
                )
            else:
                columna = {f"{columna_buscada}__{tipo_busqueda}": busqueda}
                queryset = queryset.filter(**columna)

        return queryset

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx.update(
            {
                "hay_matriculas": Matricula.objects.exists(),
                "hay_materias": Materia.objects.exists(),
                "total": self.total,
            }
        )

        return ctx


class ListaMaterias(VistaListaObjetos):
    template_name = "materias/index.html"
    model = Materia
    form_asignaciones = FormAsignaciones
    articulo_nombre_plural = "las"
    lista_años: "list[dict]"

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        materias = list(Materia.objects.values().order_by("nombre"))

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

    def establecer_columnas(self):
        super().establecer_columnas()
        self.columnas.insert(1, {"clave": "asignaciones", "titulo": "Asignaciones"})
        self.columnas_ocultables.insert(0, "Asignaciones")

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

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
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


@login_required
def estudiantes_matriculados_por_año(request: HttpRequest):
    """Consulta para ver estudiantes matriculados por año"""
    matriculas = (
        Matricula.objects.filter(estado="activo")
        .select_related("estudiante", "año")
        .order_by("año__numero", "estudiante__apellido")
    )

    return render(
        request, "consultas/estudiantes_matriculados.html", {"matriculas": matriculas}
    )


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
