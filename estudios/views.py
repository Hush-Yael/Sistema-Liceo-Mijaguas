from django.http import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
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
from django.contrib.auth.models import Group
from .forms import FormularioProfesorBusqueda, FormularioNotasBusqueda


def inicio(request: HttpRequest):
    contexto = {
        "cantidades": {
            "materias": Materia.objects.count(),
            "profesores": Profesor.objects.count(),
            "estudiantes": Estudiante.objects.count(),
        }
    }

    if request.user.is_superuser:
        """ contexto["profesores"] = ProfesorMateria.objects.values(
            "materia", "año", "profesor"
        ) """
        """ materias_año = (
            AñoMateria.objects.select_related("año", "materia")
            # .prefetch_related()
            .order_by("año__numero_año", "materia__nombre_materia")
        )
        print(materias_año) """

    return render(request, "inicio.html", contexto)


def materias(request: HttpRequest):
    materias = Materia.objects.order_by("nombre_materia")
    años = Año.objects.values("numero_año", "nombre_año_corto").order_by("numero_año")

    # se guarda cada materia por id, con una lista de los años en los que está asignada
    materias_años_asignaciones = {}

    if materias.count() > 0:
        for materia in materias:
            materias_años_asignaciones[materia.pk] = []
            materia_años = AñoMateria.objects.values("año__numero_año").filter(
                materia=materia
            )

            for materia_año in materia_años:
                materias_años_asignaciones[materia.pk].append(
                    materia_año["año__numero_año"],
                )

    return render(
        request,
        "materias.html",
        {
            "materias": materias,
            "años": años,
            "asignaciones": materias_años_asignaciones,
        },
    )


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
    años_list = Año.objects.values("nombre_año", "id", "numero_año").order_by(
        "numero_año"
    )
    años = {}

    for a in años_list:
        años[a["id"]] = {
            "nombre": a["nombre_año"],
            "numero": a["numero_año"],
            "secciones": [],
        }

    secciones = Seccion.objects.all().order_by("año", "letra_seccion")
    es_profesor = Group.objects.get(name="Profesor") in request.user.groups.all()

    for seccion in secciones:
        años[seccion.año_id]["secciones"].append(seccion)  # type: ignore

    return render(
        request,
        "notas/index.html",
        {"es_profesor": es_profesor, "años": años},
    )


def notas__seccion_estudiantes(request: HttpRequest, seccion_id):
    seccion = Seccion.objects.get(id=seccion_id)

    estudiantes_notas_seccion = Matricula.objects.filter(seccion=seccion).values(
        "estudiante__cedula",
        "estudiante__apellidos",
        "estudiante__nombres",
    )

    print(estudiantes_notas_seccion)

    return render(
        request,
        "notas/[seccion]_estudiantes.html",
        {"estudiantes_notas_seccion": estudiantes_notas_seccion, "seccion": seccion},
    )


def notas__seccion_estudiante_lapsos(
    request: HttpRequest, seccion_id: int, estudiante_cedula: int
):
    seccion = Seccion.objects.get(id=seccion_id)

    estudiante = Estudiante.objects.get(cedula=estudiante_cedula)

    lapsos = Lapso.objects.order_by("numero_lapso").all().order_by("-fecha_inicio")

    return render(
        request,
        "notas/[seccion]_[estudiante]_lapsos.html",
        {
            "seccion": seccion,
            "estudiante": estudiante,
            "notas": notas,
            "lapsos": lapsos,
        },
    )


def notas__seccion_estudiante_lapso(
    request: HttpRequest, seccion_id: int, estudiante_cedula: int, lapso_id: int
):
    form = FormularioNotasBusqueda()

    seccion = Seccion.objects.get(id=seccion_id)
    estudiante = Estudiante.objects.get(cedula=estudiante_cedula)
    lapso = Lapso.objects.get(id=lapso_id)
    materias = Materia.objects.values("id", "nombre_materia").order_by("nombre_materia")

    filtros = {
        "matricula__seccion": seccion,
        "matricula__estudiante": estudiante,
        "matricula__lapso": lapso,
    }
    columnas = [
        "valor_nota",
        "fecha_nota",
        "comentarios",
    ]
    orden = ["-fecha_nota"]

    id_materia_buscada = request.COOKIES.get(
        "notas_materia_id", form.initial.get("materia_id", "")
    )
    maximo = request.COOKIES.get("maximo", form.initial.get("maximo", 20))
    minimo = request.COOKIES.get("minimo", form.initial.get("minimo", 0))

    if request.method == "POST":
        form = FormularioNotasBusqueda(request.POST)

        if form.is_valid():
            id_materia_buscada = form.cleaned_data["materia_id"]
            maximo = form.cleaned_data["maximo"]
            minimo = form.cleaned_data["minimo"]

    if id_materia_buscada:
        if (materia := Materia.objects.get(id=id_materia_buscada)) is not None:
            filtros["materia"] = materia

    if filtros.get("materia", None) is None:
        orden.insert(0, "materia__nombre_materia")
        columnas.append("materia__nombre_materia")

    promedio = Nota.objects.filter(**filtros).aggregate(promedio=Avg("valor_nota"))

    filtros["valor_nota__range"] = (minimo, maximo)

    notas = Nota.objects.filter(**filtros).values(*columnas).order_by(*orden)

    form.initial = {
        "materia_id": id_materia_buscada,
        "notas_maximo": maximo,
        "notas_minimo": minimo,
    }

    response = render(
        request,
        "notas/[seccion]_[estudiante]_[lapso].html",
        {
            "seccion": seccion,
            "materia_buscada": filtros.get("materia", None),
            "estudiante": estudiante,
            "notas": notas,
            "promedio": round(promedio["promedio"], 2)
            if promedio["promedio"]
            else None,
            "materias": materias,
            "lapso": lapso,
            "form": form,
        },
    )

    response.set_cookie("notas_materia_id", id_materia_buscada)  # type: ignore
    response.set_cookie("notas_maximo", maximo)  # type: ignore
    response.set_cookie("notas_minimo", minimo)  # type: ignore

    return response


@login_required
def estudiantes_matriculados_por_año(request: HttpRequest):
    """Consulta para ver estudiantes matriculados por año"""
    matriculas = (
        Matricula.objects.filter(estado="activo")
        .select_related("estudiante", "año")
        .order_by("año__numero_año", "estudiante__apellido")
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
        .order_by("año__numero_año", "materia__nombre_materia")
    )

    return render(
        request, "consultas/materias_profesores.html", {"materias_año": materias_año}
    )


@login_required
def profesores_y_materias(request: HttpRequest):
    """Profesores y las materias que imparten"""
    profesores_materias = ProfesorMateria.objects.select_related(
        "profesor", "materia", "año"
    ).order_by("profesor__apellido", "año__nombre_año")

    return render(
        request,
        "consultas/profesores_materias.html",
        {"profesores_materias": profesores_materias},
    )


@login_required
def resumen_matriculas_por_año(request: HttpRequest):
    """Resumen de matrículas por año"""
    resumen = (
        Matricula.objects.values("año__id", "año__nombre_año", "año__numero_año")
        .annotate(
            total_estudiantes=Count("estudiante_cedula"),
            estudiantes_activos=Count(
                "estudiante_cedula",
                filter=Q(estudiante__estado="activo"),
                distinct=True,
            ),
        )
        .order_by("año__numero_año")
    )

    return render(request, "consultas/resumen_matriculas.html", {"resumen": resumen})
