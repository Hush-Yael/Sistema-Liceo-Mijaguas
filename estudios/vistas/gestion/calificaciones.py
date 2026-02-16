from django.db.models.functions.datetime import TruncMinute
from django.db.models import F, Value
from app.vistas.listas import VistaListaObjetos, VistaTablaAdaptable
from estudios.forms.gestion.busqueda import (
    NotasBusquedaForm,
)
from estudios.modelos.gestion.personas import (
    Matricula,
)
from estudios.modelos.parametros import Materia
from django.db.models.functions import Concat
from estudios.modelos.gestion.calificaciones import Nota
from estudios.vistas.gestion import aplicar_filtros_secciones_y_lapsos


class ListaNotas(VistaTablaAdaptable):
    model = Nota
    template_name = "gestion/notas/index.html"
    plantilla_lista = "gestion/notas/lista.html"
    paginate_by = 50
    form_filtros = NotasBusquedaForm  # type: ignore
    columnas_a_evitar = set()
    columnas_totales = (
        {"titulo": "Estudiante", "clave": "estudiante_nombres", "anotada": True},
        {
            "titulo": "Cédula",
            "clave": "cedula",
            "alinear": "derecha",
            "anotada": True,
        },
        {"titulo": "Materia", "clave": "materia_nombre", "anotada": True},
        {"titulo": "Sección", "clave": "seccion_nombre", "anotada": True},
        {"titulo": "Valor", "clave": "valor", "alinear": "derecha"},
        {
            "titulo": "Lapso",
            "clave": "lapso_nombre",
            "anotada": True,
            "alinear": "derecha",
        },
        {"titulo": "Fecha de añadida", "clave": "fecha_añadida", "anotada": True},
    )
    genero_sustantivo_objeto = "F"

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        queryset = Nota.objects.annotate(
            materia_nombre=F("materia__nombre"),
            seccion_nombre=F("matricula__seccion__nombre"),
            cedula=F("matricula__estudiante__cedula"),
            lapso_nombre=F("matricula__lapso__nombre"),
            estudiante_nombres=Concat(
                "matricula__estudiante__nombres",
                Value(" "),
                "matricula__estudiante__apellidos",
            ),
            fecha_añadida=TruncMinute("fecha"),
        ).only(
            *(
                col["clave"]
                for col in self.columnas_totales
                if not col.get("anotada", False)
            )
        )

        return super().get_queryset(queryset)

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        queryset = aplicar_filtros_secciones_y_lapsos(
            self,
            queryset,
            datos_form,
            seccion_col_nombre="matricula__seccion",
            lapso_col_nombre="matricula__lapso",
        )

        if materias := self.obtener_y_alternar(
            NotasBusquedaForm.Campos.MATERIAS, datos_form, "materia_nombre"
        ):
            queryset = queryset.filter(materia_id__in=materias)

        try:
            nota_minima = float(datos_form.get("valor_minimo", 0))  # type: ignore
            nota_maxima = float(datos_form.get("valor_maximo", 20))  # type: ignore

            if nota_minima <= nota_maxima:
                queryset = queryset.filter(valor__range=(nota_minima, nota_maxima))
        except (ValueError, TypeError):
            pass

        return queryset

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx.update(
            {
                "hay_matriculas": Matricula.objects.exists(),
                "hay_materias": Materia.objects.exists(),
            }
        )

        return ctx
