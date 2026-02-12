from django import forms
from app.campos import CampoBooleanoONulo
from app.forms import (
    BusquedaFormMixin,
    OrdenFormMixin,
)
from app.settings import MIGRANDO
from estudios.forms.parametros.busqueda import LapsoYSeccionFormMixin
from estudios.modelos.parametros import Materia
from estudios.modelos.gestion.personas import (
    Estudiante,
    Matricula,
    MatriculaEstados,
    Profesor,
)
from usuarios.models import Usuario


class NotasBusquedaForm(LapsoYSeccionFormMixin):
    class Campos:
        MATERIAS = "materias"
        LAPSOS = "lapsos"
        SECCIONES = "secciones"

    campos_prefijo_cookie = "notas"
    columnas_busqueda = (
        {
            "columna_db": f"{Matricula._meta.verbose_name}__{Estudiante._meta.verbose_name}__{Estudiante.nombres.field.name}",
            "nombre_campo": "nombres",
        },
        {
            "columna_db": f"{Matricula._meta.verbose_name}__{Estudiante._meta.verbose_name}__{Estudiante.apellidos.field.name}",
            "nombre_campo": "apellidos",
        },
        {
            "columna_db": f"{Matricula._meta.verbose_name}__{Estudiante._meta.verbose_name}__{Estudiante.cedula.field.name}",
            "nombre_campo": "cedula",
        },
    )

    materias = forms.ModelMultipleChoiceField(
        label="Materia",
        queryset=Materia.objects.all().order_by("nombre") if not MIGRANDO else None,
        required=False,
    )


class MatriculaBusquedaForm(OrdenFormMixin, LapsoYSeccionFormMixin):
    columnas_busqueda = (
        {
            "columna_db": f"{Estudiante._meta.verbose_name}__{Estudiante.nombres.field.name}",
            "nombre_campo": "nombres",
        },
        {
            "columna_db": f"{Estudiante._meta.verbose_name}__{Estudiante.apellidos.field.name}",
            "nombre_campo": "apellidos",
        },
        {
            "columna_db": f"{Estudiante._meta.verbose_name}__{Estudiante.cedula.field.name}",
            "nombre_campo": "cedula",
        },
    )
    opciones_orden = (
        (
            f"{Estudiante._meta.verbose_name}__{Estudiante.nombres.field.name}",
            "Nombres",
        ),
        (
            f"{Estudiante._meta.verbose_name}__{Estudiante.apellidos.field.name}",
            "Apellidos",
        ),
        (
            f"{Estudiante._meta.verbose_name}__{Estudiante.cedula.field.name}",
            "Cedula",
        ),
    )
    campos_prefijo_cookie = "matriculas"

    estado = forms.ChoiceField(
        label="Estado",
        initial=None,
        choices=MatriculaEstados.choices,
        required=False,
    )


class ProfesorBusquedaForm(OrdenFormMixin, BusquedaFormMixin):
    class Campos:
        TIENE_USUARIO = "tiene_usuario"
        ACTIVO = "activo"
        TIENE_TELEFONO = "tiene_telefono"

    opciones_orden = (
        (nc(Profesor.nombres), "Nombres"),
        (nc(Profesor.apellidos), "Apellidos"),
        (nc(Profesor.cedula), "Cédula"),
        (nc(Profesor.telefono), "Telefono"),
        (f"{mn(Usuario)}__{nc(Usuario.username)}", "Nombre de usuario"),
    )

    columnas_busqueda = (
        (
            {"columna_db": nc(Profesor.nombres), "nombre_campo": "nombres"},
            {"columna_db": nc(Profesor.apellidos), "nombre_campo": "apellidos"},
            {
                "columna_db": nc(Profesor.cedula),
                "nombre_campo": "cedula",
                "label_campo": "Cédula",
            },
            {"columna_db": nc(Profesor.telefono), "nombre_campo": "telefono"},
            {
                "columna_db": f"{mn(Usuario)}__{nc(Usuario.username)}",
                "nombre_campo": "username",
                "label_campo": "Nombre de usuario",
            },
        )
        if not MIGRANDO
        else ()
    )
    campos_prefijo_cookie = "profesores"

    tiene_usuario = CampoBooleanoONulo(
        label="Tiene usuario",
        label_no_escogido="NO Tiene usuario",
        label_si_escogido="Tiene usuario",
    )

    activo = CampoBooleanoONulo(
        label="Activo",
        label_no_escogido="Inactivo",
        label_si_escogido="Activo",
    )

    tiene_telefono = CampoBooleanoONulo(
        label="Tiene teléfono",
        label_no_escogido="NO Tiene teléfono",
        label_si_escogido="Tiene teléfono",
    )
