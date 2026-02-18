from typing import Any, Mapping
from django.db import models
from django.http import HttpRequest
from django.shortcuts import render
from app.vistas.listas import VistaListaObjetos
from django.contrib.auth.decorators import login_required


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
    return render(request, "gestion/inicio.html")
