from django.http import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import (
    Año,
    Materia,
    Profesor,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Nota,
)
from .forms import FormularioProfesorBusqueda


def inicio(request: HttpRequest):
    return render(request, "inicio.html")


@login_required
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


@login_required
def materia(request: HttpRequest, materia_id: int):
    try:
        materia = Materia.objects.get(id=materia_id)
    except Materia.DoesNotExist:
        return render(request, "404.html")

    materia_años = AñoMateria.objects.filter(materia=materia)
    años_asignados = []

    for materia_año in materia_años:
        años_asignados.append(materia_año.año.numero_año)

    return render(
        request,
        "[materia].html",
        {"materia": materia, "años_asignados": años_asignados},
    )


@login_required
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
        "profesores/index.html",
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
def notas_por_estudiante_lapso(request, estudiante_id):
    """Consulta de notas por estudiante y lapso"""
    notas = (
        Nota.objects.filter(estudiante_id=estudiante_id)
        .select_related("estudiante", "materia", "lapso")
        .order_by("lapso__numero_lapso", "materia__nombre_materia")
    )

    return render(
        request,
        "consultas/notas_estudiante.html",
        {"notas": notas},
    )


@login_required
def promedio_notas_estudiante_materia(request: HttpRequest):
    """Promedio de notas por estudiante y materia"""
    promedios = (
        Nota.objects.values(
            "estudiante__id",
            "estudiante__nombre",
            "estudiante__apellido",
            "materia__id",
            "materia__nombre_materia",
        )
        .annotate(promedio_nota=Avg("valor_nota"))
        .order_by("estudiante__apellido", "materia__nombre_materia")
    )

    return render(
        request, "consultas/promedios_estudiantes.html", {"promedios": promedios}
    )


@login_required
def notas_promedio_por_año_materia(request: HttpRequest):
    """Notas promedio por año y materia"""
    promedios = (
        Nota.objects.values(
            "lapso__año__id",
            "lapso__año__nombre_año",
            "materia__id",
            "materia__nombre_materia",
        )
        .annotate(promedio_general=Avg("valor_nota"))
        .order_by("lapso__año__numero_año", "materia__nombre_materia")
    )

    return render(
        request, "consultas/promedios_año_materia.html", {"promedios": promedios}
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
            total_estudiantes=Count("estudiante_id"),
            estudiantes_activos=Count(
                "estudiante_id", filter=Q(estudiante__esta_activo=True)
            ),
        )
        .order_by("año__numero_año")
    )

    return render(request, "consultas/resumen_matriculas.html", {"resumen": resumen})
