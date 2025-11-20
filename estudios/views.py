from typing import Tuple
from django import forms
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
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
from .forms import FormularioProfesorBusqueda, FormularioNotasBusqueda
from django.core.paginator import Paginator
import json


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
            .order_by("año__numero", "materia__nombre")
        )
        print(materias_año) """

    return render(request, "inicio.html", contexto)


def materias(request: HttpRequest):
    materias = Materia.objects.order_by("nombre")
    años = Año.objects.values("numero", "nombre_corto").order_by("numero")

    # se guarda cada materia por id, con una lista de los años en los que está asignada
    materias_años_asignaciones = {}

    if materias.count() > 0:
        for materia in materias:
            materias_años_asignaciones[materia.pk] = []
            materia_años = AñoMateria.objects.values("año__numero").filter(
                materia=materia
            )

            for materia_año in materia_años:
                materias_años_asignaciones[materia.pk].append(
                    materia_año["año__numero"],
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
    cookies = request.COOKIES
    cookies_a_corregir: list[Tuple] = []
    form = FormularioNotasBusqueda()

    # print("Cookies recibidas:", cookies)

    # cambiar los valores iniciales del form al cargar la página
    for id, campo in form.fields.items():
        if (cookie := cookies.get(id)) is not None:
            try:
                if isinstance(campo, forms.ModelMultipleChoiceField):
                    cookie = json.loads(cookie)
                    campo.initial = cookie

                # validar que el valor de la cookie sea correcto para indicarlo como valor inicial al campo
                else:
                    valor_valido = campo.clean(cookie)
                    campo.initial = valor_valido
            # si no lo es, se deja como está y se manda a corregir la cookie con el valor por defecto
            except (ValueError, forms.ValidationError):
                # print(f'La cookie "{id}" no tenía un valor válido --> {cookie}')
                cookies_a_corregir.append((id, campo.initial))

            # print(f"Campo <{id}>: initial = {campo.initial}, cookie = {cookie}")
        """ else:
            print(f"Campo <{id}>: initial = {campo.initial}") """

    cantidad_años = Año.objects.count()
    cantidad_lapsos = Lapso.objects.count()

    total = Nota.objects.all().count()

    respuesta = render(
        request,
        "notas/index.html",
        {
            "form": form,
            "total": total,
            "cantidad_años": cantidad_años,
            "cantidad_lapsos": cantidad_lapsos,
        },
    )

    for clave, valor in cookies_a_corregir:
        respuesta.set_cookie(clave, valor)

    return respuesta


def notas_tabla(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse("", status=405)

    # para guardar los valores de los campos en cookies que cambian los valores iniciales al cargar la página por primera vez
    filtros_cookies = []

    datos = request.POST
    # print("POST:", datos)

    form = FormularioNotasBusqueda()
    form = FormularioNotasBusqueda(datos)

    # validar el form para que los campos cuyos valores no sean válidos tengan su valor por defecto
    form.is_valid()

    for id, campo in form.fields.items():
        # filtros de selección
        if isinstance(campo, forms.ModelMultipleChoiceField):
            queryset = form.cleaned_data.get(id)

            if not queryset:
                filtros_cookies.append((id, None))
            elif hasattr(queryset, "values_list"):
                filtros_cookies.append(
                    (id, json.dumps(list(queryset.values_list("pk", flat=True))))
                )
        # filtros de búsqueda y valor de notas
        else:
            valor = form.cleaned_data.get(id)

            filtros_cookies.append((id, str(valor)))

        # print(f"Campo <{id}>, con valor <{form.cleaned_data.get(id)}>")

    # print("Form data:", form.data)

    secciones = form.data.getlist("notas_secciones", [])
    lapsos = form.data.getlist("notas_lapsos", [])
    materias = form.data.getlist("notas_materias", [])

    notas = Nota.objects.all().order_by("-fecha")

    if secciones and len(secciones) > 0 and secciones[0] != "":
        notas = notas.filter(matricula__seccion_id__in=secciones)

    if lapsos and len(lapsos) > 0 and lapsos[0] != "":
        notas = notas.filter(matricula__lapso_id__in=lapsos)

    if materias and len(materias) > 0 and materias[0] != "":
        notas = notas.filter(materia_id__in=materias)

    total_conjunto = notas.count()

    nota_minima = float(form.data.get("notas_valor_minimo"))
    nota_maxima = float(form.data.get("notas_valor_maximo"))

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

    cantidad_por_pagina = int(datos.get("notas_cantidad_paginas", 10))
    paginador = Paginator(notas, cantidad_por_pagina)

    notas = paginador.get_page(datos.get("pagina", 1))

    respuesta = render(
        request,
        "notas/contenido-tabla.html",
        {
            "notas": notas,
            "total_conjunto": total_conjunto,
            "paginador": paginador,
            "cantidad_por_pagina": cantidad_por_pagina,
            "form": form,
            "secciones": secciones if secciones and secciones[0] != "" else [],
            "lapsos": lapsos if lapsos and lapsos[0] != "" else [],
            "materias": materias if materias and materias[0] != "" else [],
            # Para indicar (al cambiar de página) que solo se cargue la tabla y la paginación, ya que lo demás no se actualiza
            "solo_tabla": datos.get("solo_tabla", False),
        },
    )

    for clave, valor in filtros_cookies:
        respuesta.set_cookie(clave, valor)

    return respuesta


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
