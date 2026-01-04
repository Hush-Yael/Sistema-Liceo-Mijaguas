from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.http.request import QueryDict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.urls import reverse_lazy

from app.vistas import VistaActualizarObjeto, VistaCrearObjeto, VistaListaObjetos

from estudios.formularios import FormAsignaciones, FormLapso, FormMateria, FormAño
from estudios.utilidades_cookies import (
    obtener_y_corregir_valores_iniciales,
    render_con_cookies,
    verificar_y_aplicar_filtros,
)
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
from .formularios_busqueda import FormularioProfesorBusqueda, FormularioNotasBusqueda
from django.core.paginator import Paginator


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


def profesores(request: HttpRequest):
    profesores = None

    form = FormularioProfesorBusqueda()

    columna_buscada = request.COOKIES.get("profesores_columna", "apellidos")
    tipo_busqueda = request.COOKIES.get("profesores_tipo_busqueda", "icontains")
    orden = request.COOKIES.get("profesores_orden", "apellidos")
    orden_col = orden
    direccion = request.COOKIES.get("profesores_direccion", "asc")

    if request.method == "POST":
        form = FormularioProfesorBusqueda(request.POST)

        if form.is_valid():
            busqueda = form.cleaned_data["busqueda"].strip()

            columna_buscada = form.cleaned_data["columna_buscada"]
            tipo_busqueda = form.cleaned_data["tipo_busqueda"]
            orden = form.cleaned_data["ordenar_por"]
            direccion = form.cleaned_data["direccion_de_orden"]

            if busqueda != "":
                columna_buscada_key = f"{columna_buscada}{tipo_busqueda}"
                profesores = Profesor.objects.filter(**{columna_buscada_key: busqueda})

    if direccion == "desc":
        orden_col = f"-{orden}"

    if profesores is None:
        profesores = Profesor.objects

    profesores = profesores.order_by(orden_col).select_related("usuario").all()

    form.initial = {
        "columna_buscada": columna_buscada,
        "tipo_busqueda": tipo_busqueda,
        "ordenar_por": orden,
        "direccion_de_orden": direccion,
    }

    response = render(
        request,
        "profesores.html",
        {
            "form": form,
            "profesores": profesores,
        },
    )

    response.set_cookie("profesores_columna", columna_buscada)
    response.set_cookie("profesores_tipo_busqueda", tipo_busqueda)
    response.set_cookie("profesores_orden", orden)
    response.set_cookie("profesores_direccion", direccion)

    return response


def notas(request: HttpRequest):
    form = FormularioNotasBusqueda()

    cookies_a_corregir = obtener_y_corregir_valores_iniciales(request.COOKIES, form)

    hay_matriculas = Matricula.objects.exists()
    hay_materias = Materia.objects.exists()
    total = Nota.objects.count()

    return render_con_cookies(
        request,
        "notas/index.html",
        {
            "form": form,
            "total": total,
            "hay_matriculas": hay_matriculas,
            "hay_materias": hay_materias,
        },
        cookies_a_corregir,
    )


def al_menos_un_filtro_aplicado(lista: "list[str]") -> bool:
    if lista:
        if len(lista) == 1 and lista[0] != "":
            return True
        if len(lista) > 1:
            return True

    return False


def notas_tabla(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse("", status=405)  # type: ignore

    datos = request.POST

    form = FormularioNotasBusqueda(datos)

    cookies_para_guardar = verificar_y_aplicar_filtros(form)

    secciones = form.data.getlist("notas_secciones", [])  # type: ignore
    lapsos = form.data.getlist("notas_lapsos", [])  # type: ignore
    materias = form.data.getlist("notas_materias", [])  # type: ignore

    # se añaden dinámicamente según el orden en el que se muestran
    columnas = [
        {
            "nombre_col": "matricula__estudiante",
            "titulo": "Estudiante",
            "clave": "estudiante",
        },
        (
            {"nombre_col": "materia", "titulo": "Materia", "clave": "materia"}
            if not al_menos_un_filtro_aplicado(materias)  # type: ignore
            else None
        ),
        (
            {
                "nombre_col": "matricula__seccion__nombre",
                "titulo": "Sección",
                "clave": "seccion_nombre",
            }
            if not al_menos_un_filtro_aplicado(secciones)  # type: ignore
            else None
        ),
        {"nombre_col": "valor", "titulo": "Valor", "clave": "valor"},
        (
            {
                "nombre_col": "matricula__lapso__nombre",
                "titulo": "Lapso",
                "clave": "lapso_nombre",
            }
            if not al_menos_un_filtro_aplicado(lapsos)  # type: ignore
            else None
        ),
        {"nombre_col": "fecha", "titulo": "Fecha", "clave": "fecha"},
    ]

    columnas = list(filter(None, columnas))

    notas = (
        Nota.objects.annotate(  # type: ignore
            seccion_nombre=F("matricula__seccion__nombre"),
            lapso_nombre=F("matricula__lapso__nombre"),
        )
        .only(*[columna["nombre_col"] for columna in columnas])
        .order_by("-fecha")
    )

    if al_menos_un_filtro_aplicado(secciones):  # type: ignore
        notas = notas.filter(matricula__seccion_id__in=secciones)

    if al_menos_un_filtro_aplicado(lapsos):  # type: ignore
        notas = notas.filter(matricula__lapso_id__in=lapsos)

    if al_menos_un_filtro_aplicado(materias):  # type: ignore
        notas = notas.filter(materia_id__in=materias)

    total_conjunto = notas.count()

    nota_minima = float(form.data.get("notas_valor_minimo"))  # type: ignore
    nota_maxima = float(form.data.get("notas_valor_maximo"))  # type: ignore

    if nota_minima <= nota_maxima:
        notas = notas.filter(valor__range=(nota_minima, nota_maxima))

    busqueda = datos.get("q")
    if isinstance(busqueda, str) and busqueda.strip() != "":
        tipo_busqueda = form.data["notas_tipo_busqueda"]
        columna_buscada = form.data["notas_columna_buscada"]

        if columna_buscada == "nombres_apellidos":
            notas = notas.filter(
                Q(matricula__estudiante__nombres__icontains=busqueda)
                | Q(matricula__estudiante__apellidos__icontains=busqueda)
            )
        else:
            columna = {f"{columna_buscada}__{tipo_busqueda}": busqueda}
            notas = notas.filter(**columna)

    cantidad_por_pagina = int(datos.get("notas_cantidad_paginas", 10))  # type: ignore
    paginador = Paginator(notas, cantidad_por_pagina)

    notas = paginador.get_page(datos.get("pagina", 1))

    return render_con_cookies(
        request,
        "notas/contenido-tabla.html",
        {
            "notas": notas,
            "total_conjunto": total_conjunto,
            "paginador": paginador,
            "cantidad_por_pagina": cantidad_por_pagina,
            "form": form,
            "columnas": columnas,
            "columnas_ocultables": list(map(lambda x: x["titulo"], columnas[2 - 1 :])),
            # Para indicar (al cambiar de página) que solo se cargue la tabla y la paginación, ya que lo demás no se actualiza
            "solo_tabla": datos.get("solo_tabla", False),
        },
        cookies_para_guardar,
    )


class ListaMaterias(VistaListaObjetos):
    template_name = "materias/index.html"
    model = Materia
    form_asignaciones = FormAsignaciones
    articulo_nombre_plural = "las"
    lista_años: "list[dict]"

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        materias = list(Materia.objects.values().order_by("nombre"))

        if materias:
            años = años = Año.objects.values("numero", "nombre_corto").order_by(
                "numero"
            )
            self.lista_años = list(años)
            asignaciones = list(AñoMateria.objects.values("año__numero", "materia__id"))

            for materia in materias:
                materia["asignaciones"] = []

                for año in años:
                    if asignaciones.__contains__(
                        {
                            "año__numero": año["numero"],
                            "materia__id": materia["id"],
                        }
                    ):
                        materia["asignaciones"].append(año["numero"])

        return materias

    def obtener_columnas(self):
        super().obtener_columnas()
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
                    año.id
                ):  # type: ignore
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
        return super().get_queryset(Año.objects.all().order_by("numero"))


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
