from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Model, F

from estudios.admin_pestañas import (
    obtener_lista_pestañas_admin,
    obtener_vista_pestaña_admin_completa,
    obtener_vista_pestaña_admin_form,
    pestañas_admin,
)
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


@login_required
def administrar(request: HttpRequest):
    datos = request.GET
    pestaña_inicial = datos.get("pestaña")

    lista_pestañas = obtener_lista_pestañas_admin(
        request.user,
        pestaña_inicial,
    )

    return render(
        request,
        "administrar/index.html",
        {
            "lista_pestañas": lista_pestañas,
            "pestaña_inicial": pestaña_inicial or lista_pestañas[0]["nombre"],
        },
    )


@login_required
def obtener_pestaña_admin(request: HttpRequest):
    try:
        if (
            request.method != "GET"
            and request.method != "POST"
            and request.method != "DELETE"
        ):
            return HttpResponse("", status=405)

        metodo = request.method

        if request.method != "DELETE":
            datos = getattr(request, metodo)
        else:
            datos = request.GET

        pestaña = datos.get("pestaña")
    except Exception as e:
        print(f"Error al obtener la pestaña: {str(e)}")
        return HttpResponse("Error al obtener la pestaña", status=500)

    if pestaña not in pestañas_admin:
        return HttpResponse("No se encontró la pestaña buscada", status=404)

    if metodo == "GET" or metodo == "DELETE":
        if metodo == "DELETE":
            modelo: Model = pestañas_admin[pestaña]["modelo"]
            seleccion = datos.getlist("seleccion")

            if seleccion and seleccion != []:
                modelo.objects.filter(id__in=seleccion).delete()
            else:
                return HttpResponse("No se seleccionaron objetos", status=400)

        return obtener_vista_pestaña_admin_completa(
            request=request,
            nombre_pestaña=pestaña,
        )
    elif metodo == "POST":
        return obtener_vista_pestaña_admin_form(
            request=request,
            nombre_pestaña=pestaña,
        )


@login_required
def obtener_form_editar_pestaña(request: HttpRequest):
    if request.method != "GET":
        return HttpResponse("", status=405)

    pestaña = request.GET.get("pestaña")

    if pestaña not in pestañas_admin:
        return HttpResponse("No se encontró la pestaña buscada", status=40)

    return obtener_vista_pestaña_admin_form(
        request=request,
        nombre_pestaña=pestaña,
    )


# Llama a obtener_vista_pestaña_admin_completa para manejar la vista completa de la pestaña
@login_required
def vista_pestaña_admin_completa(request: HttpRequest):
    return obtener_pestaña_admin(request)


# Llama a obtener_vista_pestaña_admin_form para manejar la lógica del formulario y procesar la solicitud
@login_required
def vista_pestaña_admin_form(request: HttpRequest):
    return obtener_pestaña_admin(request)


def notas(request: HttpRequest):
    form = FormularioNotasBusqueda()

    cookies_a_corregir = obtener_y_corregir_valores_iniciales(request.COOKIES, form)

    cantidad_años = Año.objects.count()
    cantidad_lapsos = Lapso.objects.count()
    total = Nota.objects.all().count()

    return render_con_cookies(
        request,
        "notas/index.html",
        {
            "form": form,
            "total": total,
            "cantidad_años": cantidad_años,
            "cantidad_lapsos": cantidad_lapsos,
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

    secciones = form.data.getlist("notas_secciones", [])
    lapsos = form.data.getlist("notas_lapsos", [])
    materias = form.data.getlist("notas_materias", [])

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
    columnas_fijas = 2

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
            "columnas_ocultables": list(
                map(lambda x: x["titulo"], columnas[columnas_fijas - 1 :])
            ),
            "columnas_fijas": columnas_fijas,
            # Para indicar (al cambiar de página) que solo se cargue la tabla y la paginación, ya que lo demás no se actualiza
            "solo_tabla": datos.get("solo_tabla", False),
        },
        cookies_para_guardar,
    )


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
