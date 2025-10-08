from django.http import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import (
    Materia,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Calificacion,
)


@login_required
def inicio(request: HttpRequest):
    return render(request, "inicio.html")


@login_required
def materias(request: HttpRequest):
    materias = Materia.objects.all().order_by("nombre_materia")

    return render(request, "materias.html", {"materias": materias})


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
def calificaciones_por_estudiante_lapso(request, estudiante_id):
    """Consulta de calificaciones por estudiante y lapso"""
    calificaciones = (
        Calificacion.objects.filter(estudiante_id=estudiante_id)
        .select_related("estudiante", "materia", "lapso")
        .order_by("lapso__numero_lapso", "materia__nombre_materia")
    )

    return render(
        request,
        "consultas/calificaciones_estudiante.html",
        {"calificaciones": calificaciones},
    )


@login_required
def promedio_calificaciones_estudiante_materia(request: HttpRequest):
    """Promedio de calificaciones por estudiante y materia"""
    promedios = (
        Calificacion.objects.values(
            "estudiante__id",
            "estudiante__nombre",
            "estudiante__apellido",
            "materia__id",
            "materia__nombre_materia",
        )
        .annotate(promedio_calificacion=Avg("valor_calificacion"))
        .order_by("estudiante__apellido", "materia__nombre_materia")
    )

    return render(
        request, "consultas/promedios_estudiantes.html", {"promedios": promedios}
    )


@login_required
def calificaciones_promedio_por_año_materia(request: HttpRequest):
    """Calificaciones promedio por año y materia"""
    promedios = (
        Calificacion.objects.values(
            "lapso__año__id",
            "lapso__año__nombre_año",
            "materia__id",
            "materia__nombre_materia",
        )
        .annotate(promedio_general=Avg("valor_calificacion"))
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
