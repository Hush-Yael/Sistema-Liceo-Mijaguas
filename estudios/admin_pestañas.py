from estudios.formularios import FormLapso, FormMateria, FormAño
from estudios.models import (
    Lapso,
    Año,
    Materia,
    AñoMateria,
)
from django import forms
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from usuarios.models import User


# Crea la lista de pestañas disponibles al entrar en la sección de administración al cargarla completa
def obtener_lista_pestañas_admin(usuario: User, pestaña_inicial):
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

    if pestaña_inicial is None:
        pestañas[0]["es_inicial"] = True

    return pestañas


# Al cargar la página por primera vez o cambiar de pestaña, obtiene su vista completa (todo se reemplaza)
def obtener_vista_pestaña_admin_completa(
    request: HttpRequest,
    nombre_pestaña: str,
):
    if not request.user.has_perm(
        "estudios.view_" + pestañas_admin[nombre_pestaña]["nombre_modelo"]
    ):
        return HttpResponse(
            "No tienes permisos para acceder a esta pestaña", status=403
        )

    return render(
        request,
        f"administrar/pestañas/{nombre_pestaña}.html",
        {
            "form": pestañas_admin[nombre_pestaña]["form"](),
            "pestaña": nombre_pestaña,
            **(
                pestañas_admin[nombre_pestaña]["obtener_datos_extra_vista_completa"]()
                if pestañas_admin[nombre_pestaña].get(
                    "obtener_datos_extra_vista_completa"
                )
                else {}
            ),
        },
    )


# Al añadir/modificar un objeto, valida el formulario y devuelve sus campos, junto con el objeto creado o modificado, a partir de un parcial definido en la plantilla
def obtener_vista_pestaña_admin_form(
    request: HttpRequest,
    nombre_pestaña: str,
):
    form_del_modelo = pestañas_admin[nombre_pestaña]["form"]
    obtener_datos_extra = pestañas_admin[nombre_pestaña].get(
        "obtener_datos_extra_parcial_form"
    )

    # nuevo o guardar cambios
    if request.method == "POST":
        nombre_modelo = pestañas_admin[nombre_pestaña]["nombre_modelo"]
        datos = request.POST

        try:
            objeto_id = int(datos.get("id"))
        except (ValueError, TypeError):
            objeto_id = -1

        editando = objeto_id > -1

        if editando:
            if not request.user.has_perm("estudios.add_" + nombre_modelo):
                return HttpResponse(
                    "No tienes permisos para añadir nada en esta pestaña", status=403
                )
        else:
            if not request.user.has_perm("estudios.change_" + nombre_modelo):
                return HttpResponse(
                    "No tienes permisos para modificar nada en esta pestaña", status=403
                )

        if editando:
            form = form_del_modelo(
                datos,
                instance=pestañas_admin[nombre_pestaña]["modelo"].objects.get(
                    id=objeto_id
                ),
            )
        else:
            form = form_del_modelo(datos)

        exito = form.is_valid()

        if exito:
            # si es necesario, modificar el objeto o hacer otras cosas antes de guardar
            if (
                modificar_antes_guardar := pestañas_admin[nombre_pestaña].get(
                    "modificar_antes_guardar"
                )
            ) is not None:
                modificar_antes_guardar(form)

            form.save()

            # si es necesario, hacer otras cosas después de guardar
            if (
                modificar_luego_guardar := pestañas_admin[nombre_pestaña].get(
                    "modificar_luego_guardar"
                )
            ) is not None:
                modificar_luego_guardar(form)

        objeto_retornado = form.instance

        if exito:  # limpiar valores
            form = form_del_modelo()

        # Procesar el formulario válido aquí si es necesario
        return render(
            request,
            # el formulario se genera desde un parcial en la pestaña
            f"administrar/pestañas/{nombre_pestaña}.html#campos",
            {
                "form": form,
                "exito": exito,
                "editado": editando,
                "objeto_retornado": objeto_retornado,
                **(obtener_datos_extra() if obtener_datos_extra is not None else {}),
            },
        )
    elif request.method == "GET":
        objeto_id = request.GET.get("objeto_id")
        objeto = pestañas_admin[nombre_pestaña]["modelo"].objects.get(id=objeto_id)
        form: forms.ModelForm = form_del_modelo(instance=objeto)

        if pestañas_admin[nombre_pestaña].get("modificar_form_editar"):
            pestañas_admin[nombre_pestaña]["modificar_form_editar"](objeto, form)

        return render(
            request,
            # el formulario se genera desde un parcial en la pestaña
            f"administrar/pestañas/{nombre_pestaña}.html#campos",
            {
                "datos_extra": obtener_datos_extra()
                if obtener_datos_extra is not None
                else None,
                "objeto_id": objeto_id,
                "form": form,
                "objeto_retornado": objeto,
            },
        )

    return HttpResponse("Metodo no permitido", status=405)


# Obtiene todos los años existentes en la base de datos
def obtener_años():
    años = Año.objects.values(
        "id", "numero", "nombre", "nombre_corto", "fecha_creacion"
    ).order_by("numero")
    return años


# Devuelve todas las materias actuales y en qué años se encuentran asignadas
def obtener_materias_y_asignaciones():
    materias = Materia.objects.values("id", "nombre", "fecha_creacion").order_by(
        "nombre"
    )
    años = obtener_años().values("numero", "nombre_corto")

    materias_años = list(AñoMateria.objects.values("año__numero", "materia__id"))

    for materia in materias:
        materia["asignaciones"] = []

        for año in años:
            if materias_años.__contains__(
                {
                    "año__numero": año["numero"],
                    "materia__id": materia["id"],
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
        "id", "nombre", "numero", "fecha_inicio", "fecha_fin"
    ).order_by("-id")
    return lapsos


# Al añadir una materia, se asigna automáticamente a los años seleccionados
def asignar_a_años(
    form: FormMateria,
):
    nueva_materia = form.instance
    editando = form.instance.id > -1
    lista_años: list[Año] = form.cleaned_data["asignaciones"]
    ya_asignados = []

    if editando:
        asignaciones = AñoMateria.objects.filter(materia=nueva_materia).values_list(
            "año_id", flat=True
        )

        ya_asignados = list(Año.objects.filter(id__in=asignaciones))

    for año in lista_años:
        if ya_asignados.__contains__(año):
            continue

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


def obtener_años_asignados(objeto: Materia, form: FormMateria):
    asignadas = AñoMateria.objects.values_list("año_id", flat=True).filter(
        materia=objeto
    )
    form.initial["asignaciones"] = list(Año.objects.filter(id__in=asignadas))


pestañas_admin = {
    "años": {
        "modelo": Año,
        "texto": "Años",
        "nombre_modelo": "año",
        "form": FormAño,
        "obtener_datos_extra_vista_completa": lambda: {"lista_objetos": obtener_años()},
        "obtener_datos_extra_parcial_form": lambda: {"años": obtener_años()},
    },
    "lapsos": {
        "modelo": Lapso,
        "texto": "Lapsos",
        "nombre_modelo": "lapso",
        "form": FormLapso,
        "obtener_datos_extra_vista_completa": lambda: {
            "lista_objetos": obtener_lapsos()
        },
    },
    "materias": {
        "modelo": Materia,
        "texto": "Materias",
        "nombre_modelo": "materia",
        "form": FormMateria,
        "obtener_datos_extra_vista_completa": obtener_materias_y_asignaciones,
        # se necesita la lista de años para iterar sobre las asignaciones del nuevo objeto en el parcial
        "obtener_datos_extra_parcial_form": lambda: {"lista_años": obtener_años()},
        "modificar_form_editar": lambda objeto, form: obtener_años_asignados(
            objeto, form
        ),
        "modificar_luego_guardar": asignar_a_años,
    },
}
