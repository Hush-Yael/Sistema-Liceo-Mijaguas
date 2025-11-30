from estudios.formularios import FormLapso, FormMateria, FormAño
from estudios.models import (
    Lapso,
    Año,
    Materia,
    AñoMateria,
)
from typing import Callable
from django import forms
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from usuarios.models import User


# Crea la lista de pestañas disponibles al entrar en la sección de administración al cargarla completa
def obtener_lista_pestañas_admin(usuario: User, pestaña_inicial: str):
    permisos = list(
        filter(
            lambda permiso: permiso.startswith("estudios.view_"),
            usuario.get_all_permissions(),
        )
    )
    pestañas = []

    for nombre, datos in pestañas_admin.items():
        permiso = "estudios.view_" + nombre.rstrip("s")
        if permiso in permisos:
            pestaña = {
                "nombre": nombre,
                "texto": datos["texto"],
            }

            if pestaña_inicial == nombre:
                pestaña["es_inicial"] = True

            pestañas.append(pestaña)

    return pestañas


# Al cargar la página por primera vez o cambiar de pestaña, obtiene su vista completa (todo se reemplaza)
def obtener_vista_pestaña_admin_completa(
    request: HttpRequest,
    nombre_pestaña: str,
    form_del_modelo: forms.ModelForm,
    nombre_modelo: str,
    datos_extra: dict = {},
):
    if not request.user.has_perm("estudios.view_" + nombre_modelo):
        return HttpResponse(
            "No tienes permisos para acceder a esta pestaña", status=403
        )

    return render(
        request,
        f"administrar/pestañas/{nombre_pestaña}.html",
        {
            **datos_extra,
            "form": form_del_modelo(),
            "pestaña": nombre_pestaña,
        },
    )


# Al añadir/modificar un objeto, valida el formulario y devuelve sus campos, junto con el objeto creado o modificado, a partir de un parcial definido en la plantilla
def obtener_vista_pestaña_admin_form(
    request: HttpRequest,
    nombre_pestaña: str,
    form_del_modelo: forms.ModelForm,
    nombre_modelo: str,
    datos_extra: dict = {},
    modificar_antes_guardar: Callable[[forms.ModelForm], None] = None,
    modificar_luego_guardar: Callable[[forms.ModelForm], None] = None,
):
    if not request.user.has_perm("estudios.add_" + nombre_modelo):
        return HttpResponse(
            "No tienes permisos para modificar nada en esta pestaña", status=403
        )

    form = form_del_modelo(request.POST)
    exito = form.is_valid()

    if exito:
        # si es necesario, modificar el objeto o hacer otras cosas antes de guardar
        if modificar_antes_guardar is not None:
            modificar_antes_guardar(form)

        form.save()

        # si es necesario, hacer otras cosas después de guardar
        if modificar_luego_guardar is not None:
            modificar_luego_guardar(form)

    # Procesar el formulario válido aquí si es necesario
    return render(
        request,
        # el formulario se genera desde un parcial en la pestaña
        f"administrar/pestañas/{nombre_pestaña}.html#campos",
        {
            **datos_extra,
            "form": form,
            "exito": exito,
            "objeto_guardado": form.instance,
        },
    )


# Obtiene todos los años existentes en la base de datos
def obtener_años():
    años = Año.objects.values(
        "numero", "nombre", "nombre_corto", "fecha_creacion"
    ).order_by("numero")
    return años


# Devuelve todas las materias actuales y en qué años se encuentran asignadas
def obtener_materias_y_asignaciones():
    materias = Materia.objects.values("pk", "nombre", "fecha_creacion").order_by(
        "nombre"
    )
    años = obtener_años().values("numero", "nombre_corto")

    materias_años = list(AñoMateria.objects.values("año__numero", "materia__pk"))

    for materia in materias:
        materia["asignaciones"] = []

        for año in años:
            if materias_años.__contains__(
                {
                    "año__numero": año["numero"],
                    "materia__pk": materia["pk"],
                }
            ):
                materia["asignaciones"].append(año["numero"])

    return {
        "lista_objetos": materias,
        "lista_años": años,
    }


# Obtiene todos los lapsos existentes en la base de datos
def obtener_lapsos():
    lapsos = Lapso.objects.values(
        "pk", "nombre", "numero", "fecha_inicio", "fecha_fin"
    ).order_by("-id")
    return lapsos


# Al añadir una materia, se asigna automáticamente a los años seleccionados
def asignar_a_años(form: FormMateria):
    nueva_materia = form.instance
    lista_años: list[Año] = form.cleaned_data["asignaciones"]

    for año in lista_años:
        asignacion = AñoMateria(
            año=año,
            materia=nueva_materia,
        )

        asignacion.save()

    # convertir el objeto guardado a un dict para poder modificarlo
    form.instance = forms.model_to_dict(form.instance)

    # lista de números de años asignados a la materia nueva
    asignaciones_queryset = list(
        form.cleaned_data["asignaciones"].values_list("numero", flat=True)
    )

    # incluir la lista en los datos del objeto para poder acceder a ella en su parcial
    form.instance["asignaciones"] = asignaciones_queryset


pestañas_admin = {
    "años": {
        "modelo": Año,
        "texto": "Años",
        "nombre_modelo": "año",
        "form": FormAño,
        "datos_extra_completo": lambda: {"lista_objetos": obtener_años()},
        "datos_extra_form": lambda: {"años": obtener_años()},
    },
    "lapsos": {
        "modelo": Lapso,
        "texto": "Lapsos",
        "nombre_modelo": "lapso",
        "form": FormLapso,
        "datos_extra_completo": lambda: {"lista_objetos": obtener_lapsos()},
    },
    "materias": {
        "modelo": Materia,
        "texto": "Materias",
        "nombre_modelo": "materia",
        "form": FormMateria,
        "datos_extra_completo": obtener_materias_y_asignaciones,
        # se necesita la lista de años para iterar sobre las asignaciones del nuevo objeto en el parcial
        "datos_extra_form": lambda: {"lista_años": obtener_años()},
        "modificar_luego_guardar": asignar_a_años,
    },
}
