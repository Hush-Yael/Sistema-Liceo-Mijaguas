from typing import Any, Mapping
from django.db import models
from django.http import HttpRequest
from django.shortcuts import render
from app.vistas import VistaListaObjetos
from django.contrib.auth.decorators import login_required


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


@login_required
def inicio(request: HttpRequest):
    return render(request, "gestion/inicio.html")
