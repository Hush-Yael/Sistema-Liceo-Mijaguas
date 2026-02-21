from typing import Any, Mapping
from django.db import models
from django.http import HttpRequest
from django.shortcuts import render
from app.vistas.listas import VistaListaObjetos
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from estudios.modelos.parametros import Materia, Año, Lapso, Seccion
from estudios.modelos.gestion.personas import (
    Estudiante,
    Profesor,
    Matricula,
)


def aplicar_filtros_secciones_y_lapsos(
    cls: VistaListaObjetos,
    queryset: models.QuerySet,
    datos_form: "dict[str, Any] | Mapping[str, Any]",
    seccion_col_nombre: str = "seccion",
    lapso_col_nombre: str = "lapso",
):
    if secciones := datos_form.get("secciones"):
        kwargs = {f"{seccion_col_nombre}_id__in": secciones}
        queryset = queryset.filter(**kwargs)

    if lapsos := datos_form.get("lapsos"):
        kwargs = {f"{lapso_col_nombre}_id__in": lapsos}
        queryset = queryset.filter(**kwargs)

    return queryset


@login_required
def inicio(request: HttpRequest):
    # Obtener el lapso actual
    lapso_actual = Lapso.objects.last()

    # Estadísticas generales
    total_estudiantes = Estudiante.objects.count()
    profesores_activos = Profesor.objects.filter(activo=True).count()

    total_materias = Materia.objects.count()

    # distribucion_materias = []

    # for materia in Materia.objects.all():
    #     count = ProfesorMateria.objects.filter(materia=materia).count()
    #     distribucion_materias.append(
    #         {
    #             "materia": materia,
    #             "count": count,
    #             "porcentaje": (count / total_materias * 100)
    #             if total_materias > 0
    #             else 0,
    #         }
    #     )

    # Distribución por años
    distribucion_años = []

    años = Año.objects.all().order_by("id")

    for año in años:
        count = Matricula.objects.filter(
            seccion__año=año, lapso=lapso_actual, estado="A"
        ).count()
        distribucion_años.append(
            {
                "año": año,
                "count": count,
                "porcentaje": (count / total_estudiantes * 100)
                if total_estudiantes > 0
                else 0,
            }
        )

    # Secciones con capacidad
    secciones = (
        Seccion.objects.select_related("año")
        .annotate(
            matriculados=Count(
                "matricula",
                filter=Q(matricula__lapso=lapso_actual, matricula__estado="A"),
            )
        )
        .order_by("-matriculados")[:5]
    )

    context = {
        "total_estudiantes": total_estudiantes,
        "profesores_activos": profesores_activos,
        "total_materias": total_materias,
        "distribucion_años": distribucion_años,
        "secciones": secciones,
        "lapso_actual": lapso_actual,
    }

    return render(request, "gestion/inicio.html", context)
