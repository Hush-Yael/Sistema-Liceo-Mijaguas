from django import forms
from app.campos import OPCIONES_TIPO_BUSQUEDA_CANTIDADES, CampoBooleanoONulo
from app.forms import (
    BusquedaFormMixin,
    OrdenFormMixin,
)
from app.settings import MIGRANDO
from app.util import mn, nc, vn
from estudios.forms.parametros.busqueda import LapsoYSeccionFormMixin
from estudios.modelos.gestion.calificaciones import Tarea, TipoTarea
from estudios.modelos.parametros import Materia, Seccion, Año
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
            "columna_db": f"{vn(Matricula)}__{vn(Estudiante)}__{nc(Estudiante.nombres)}",
            "nombre_campo": "nombres",
        },
        {
            "columna_db": f"{vn(Matricula)}__{vn(Estudiante)}__{nc(Estudiante.apellidos)}",
            "nombre_campo": "apellidos",
        },
        {
            "columna_db": f"{vn(Matricula)}__{vn(Estudiante)}__{nc(Estudiante.cedula)}",
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
            "columna_db": f"{vn(Estudiante)}__{nc(Estudiante.nombres)}",
            "nombre_campo": "nombres",
        },
        {
            "columna_db": f"{vn(Estudiante)}__{nc(Estudiante.apellidos)}",
            "nombre_campo": "apellidos",
        },
        {
            "columna_db": f"{vn(Estudiante)}__{nc(Estudiante.cedula)}",
            "nombre_campo": "cedula",
        },
    )
    opciones_orden = (
        (
            f"{vn(Estudiante)}__{nc(Estudiante.nombres)}",
            "Nombres",
        ),
        (
            f"{vn(Estudiante)}__{nc(Estudiante.apellidos)}",
            "Apellidos",
        ),
        (
            f"{vn(Estudiante)}__{nc(Estudiante.cedula)}",
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


class ProfesorBusquedaFormMixin(OrdenFormMixin, BusquedaFormMixin):
    opciones_orden = (
        (nc(Profesor.nombres), "Nombres"),
        (nc(Profesor.apellidos), "Apellidos"),
        (nc(Profesor.cedula), "Cédula"),
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
            {
                "columna_db": f"{mn(Usuario)}__{nc(Usuario.username)}",
                "nombre_campo": "username",
                "label_campo": "Nombre de usuario",
            },
        )
        if not MIGRANDO
        else ()
    )


class ProfesorBusquedaForm(ProfesorBusquedaFormMixin):
    def __init__(self, *args, **kwargs) -> None:
        self.columnas_busqueda = (
            *(self.columnas_busqueda),
            {"columna_db": nc(Profesor.telefono), "nombre_campo": "telefono"},
        )

        self.opciones_orden = (
            *(self.opciones_orden),
            (nc(Profesor.telefono), "Telefono"),
        )

        super().__init__(*args, **kwargs)

    class Campos:
        TIENE_USUARIO = "tiene_usuario"
        ACTIVO = "activo"
        TIENE_TELEFONO = "tiene_telefono"

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


# Se usa ProfesorBusquedaFormMixin ya que el queryset también es del modelo Profesor (las materias se añaden con Prefetch)
class ProfesorMateriaBusquedaForm(ProfesorBusquedaFormMixin):
    def __init__(self, *args, **kwargs) -> None:

        self.columnas_busqueda = (
            *(self.columnas_busqueda),
            {
                "columna_db": "cantidad_materias",
                "nombre_campo": "cantidad_materias",
                "label_campo": "Cantidad de materias",
                "opciones_tipo_busqueda": OPCIONES_TIPO_BUSQUEDA_CANTIDADES,
            },
        )

        self.opciones_orden = (
            *(self.opciones_orden),
            ("cantidad_materias", "Cantidad de materias"),
        )

        super(ProfesorBusquedaFormMixin, self).__init__(*args, **kwargs)

    class Campos:
        MATERIAS = "materias"
        AÑOS = "anios"
        SECCIONES = "secciones"

    campos_prefijo_cookie = "pm"

    materias = forms.ModelMultipleChoiceField(
        label="Materias",
        queryset=Materia.objects.all() if not MIGRANDO else None,
        required=False,
    )

    anios = forms.ModelMultipleChoiceField(
        label="Años",
        queryset=Año.objects.all() if not MIGRANDO else None,
        required=False,
    )

    secciones = forms.ModelMultipleChoiceField(
        label="Secciones",
        queryset=Seccion.objects.all() if not MIGRANDO else None,
        required=False,
    )


class TareaBusquedaForm(BusquedaFormMixin):
    class Campos:
        TIPOS = "tipos"

    columnas_busqueda = (
        {
            "columna_db": nc(Tarea.nombre),
            "nombre_campo": "titulo",
            "label_campo": "Título",
        },
        {
            "columna_db": nc(Tarea.descripcion),
            "nombre_campo": "descripcion",
            "label_campo": "Descripción",
        },
    )

    campos_prefijo_cookie = "tareas"

    tipos = forms.ModelMultipleChoiceField(
        label="Tipo",
        queryset=TipoTarea.objects.all().order_by(nc(TipoTarea.nombre))
        if not MIGRANDO
        else None,
        required=False,
    )


class TareaProfesorMateriaBusquedaForm(BusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    class Campos:  # type: ignore
        TIPOS = "tipos"
        MATERIAS = "materias"
        AÑOS = "anios"
        SECCIONES = "secciones"

    columnas_busqueda = (
        {
            "columna_db": f"{mn(Tarea)}__{nc(Tarea.nombre)}",
            "nombre_campo": "titulo",
            "label_campo": "Título",
        },
        {
            "columna_db": f"{mn(Tarea)}__{nc(Tarea.descripcion)}",
            "nombre_campo": "descripcion",
            "label_campo": "Descripción",
        },
    )

    campos_prefijo_cookie = "tpm"

    materias = forms.ModelMultipleChoiceField(
        label="Materias",
        queryset=Materia.objects.all() if not MIGRANDO else None,
        required=False,
    )

    anios = forms.ModelMultipleChoiceField(
        label="Años",
        queryset=Año.objects.all() if not MIGRANDO else None,
        required=False,
    )

    secciones = forms.ModelMultipleChoiceField(
        label="Secciones",
        queryset=Seccion.objects.all() if not MIGRANDO else None,
        required=False,
    )


class EstudianteBusquedaForm(BusquedaFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    class Campos:
        MATRICULA_ACTUAL = "matricula_actual"
        SECCIONES = "secciones"

    columnas_busqueda = (
        {"columna_db": nc(Estudiante.nombres), "nombre_campo": "nombres"},
        {"columna_db": nc(Estudiante.apellidos), "nombre_campo": "apellidos"},
        {
            "columna_db": nc(Estudiante.cedula),
            "nombre_campo": "cedula",
            "label_campo": "Cedula",
        },
    )

    campos_prefijo_cookie = "estudiantes"

    matricula_actual = CampoBooleanoONulo(
        label="Matriculado actualmente",
        label_no_escogido="NO matriculado actualmente",
        label_si_escogido="matriculado actualmente",
    )

    secciones = forms.ModelMultipleChoiceField(
        label="Secciones",
        queryset=Seccion.objects.all() if not MIGRANDO else None,
        required=False,
    )
