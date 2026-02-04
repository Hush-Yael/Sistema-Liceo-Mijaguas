from django import forms
from app.forms import (
    OrdenFormMixin,
)
from app.settings import MIGRANDO
from estudios.forms.parametros.busqueda import LapsoYSeccionFormMixin
from estudios.modelos.parametros import Materia
from estudios.modelos.gestion import (
    Estudiante,
    Matricula,
    MatriculaEstados,
)


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
