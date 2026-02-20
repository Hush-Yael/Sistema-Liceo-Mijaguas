from django import forms
from django.db.models import Exists
from usuarios.models import Usuario
from app.settings import MIGRANDO
from app.util import nc
from estudios.forms import LapsoActualForm, obtener_matriculas_de_lapso
from estudios.modelos.gestion.personas import (
    Estudiante,
    Matricula,
    Profesor,
    ProfesorMateria,
)
from estudios.modelos.parametros import (
    Lapso,
    Seccion,
    AñoMateria,
    obtener_lapso_actual,
)


class FormMatricula(LapsoActualForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["seccion"].label_from_instance = lambda obj: obj.nombre  # type: ignore

        lapso_actual = self.lapso_actual

        # cambiar las opciones del campo "estudiante" por los estudiantes NO matriculados en el lapso actual
        if lapso_actual is not None:
            matriculas_lapso_actual = obtener_matriculas_de_lapso(lapso_actual)

            # al editar, conservar al estudiante de la matricula actual
            if self.instance.pk:
                matriculas_lapso_actual = matriculas_lapso_actual.exclude(
                    pk=self.instance.pk
                )

            self.fields["estudiante"].queryset = (  # type: ignore
                Estudiante.objects.annotate(
                    matriculado_actualmente=Exists(matriculas_lapso_actual)
                )
                .filter(matriculado_actualmente=False, bachiller__isnull=True)
                .order_by("apellidos", "nombres")
            )

            self.fields["lapso"].choices = (("", lapso_actual.nombre),)  # type: ignore

    class Meta:
        model = Matricula
        fields = (
            nc(Matricula.estudiante),
            nc(Matricula.seccion),
            nc(Matricula.estado),
            nc(Matricula.lapso),
        )

    lapso_actual: "Lapso | None" = None

    estudiante = forms.ModelChoiceField(
        label="Estudiante",
        queryset=Estudiante.objects.none() if not MIGRANDO else None,
    )

    seccion = forms.ModelChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra")
        if not MIGRANDO
        else None,
    )

    def clean_estudiante(self):
        if estudiante := self.cleaned_data.get("estudiante"):
            matriculas_lapso_actual = Matricula.objects.filter(
                estudiante=estudiante, lapso=self.lapso_actual
            )

            if matriculas_lapso_actual.exists():
                raise forms.ValidationError("El estudiante ya se encuentra matriculado")

        return estudiante

    def clean_seccion(self):
        if seccion := self.cleaned_data.get("seccion"):
            # al crear, verificar que la sección no este llena
            if self.instance.pk is None:
                cantidad_actual = Matricula.objects.filter(
                    seccion=seccion, lapso=obtener_lapso_actual()
                ).count()

                if cantidad_actual >= seccion.capacidad:
                    raise forms.ValidationError(
                        "La sección seleccionada se encuentra llena"
                    )

        return seccion


class FormProfesor(forms.ModelForm):
    class Meta:
        model = Profesor
        exclude = (nc(Profesor.fecha_ingreso),)

    field_order = (
        nc(Profesor.nombres),
        nc(Profesor.apellidos),
        nc(Profesor.cedula),
        nc(Profesor.sexo),
        nc(Profesor.telefono),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campo_usuario: forms.ModelChoiceField = self.fields[nc(Profesor.usuario)]  # type: ignore

        campo_usuario.label = "Escoja un usuario:"

        campo_usuario.queryset = campo_usuario.queryset.filter(  # type: ignore
            profesor__isnull=True,
        )

        # Al editar, incluir el usuario asociado al profesor
        if self.instance.pk:
            if self.instance.usuario:
                campo_usuario.queryset |= (  # type: ignore
                    Usuario.objects.filter(pk=self.instance.usuario.pk)
                )

        self.campos_usuario = (
            campo_usuario,
            self.fields["usuario_manual"],
        )

    usuario_manual = forms.BooleanField(
        label="Crear usuario automáticamente",
        initial=False,
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                ":checked": "asignacionUsuario === 'manual'",
            }
        ),
    )


class ProfesorMateriaForm(forms.ModelForm):
    class Meta:
        model = ProfesorMateria
        fields = ["profesor", "materia", "seccion"]
        widgets = {
            "profesor": forms.Select(
                attrs={
                    "class": "profesor-select w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "x-model": "profesorId",
                }
            ),
            "materia": forms.Select(
                attrs={
                    "class": "materia-select w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "x-model": "materiaId",
                }
            ),
            "seccion": forms.Select(
                attrs={
                    "class": "seccion-select w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500",
                    "x-model": "seccionId",
                }
            ),
        }


class FormProfesorMateriaMasivo(forms.Form):
    instance: "Profesor | None" = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campo_materias: forms.MultipleChoiceField = self.fields[
            f"{nc(ProfesorMateria.materia)}s"
        ]  # type: ignore - sí es un MultipleChoiceField

        campo_materias.choices = self.obtener_materias_disponibles()

    profesor = forms.ModelChoiceField(
        queryset=Profesor.objects.filter(activo=True),
        label="Profesor",
        empty_label="Seleccione un profesor",
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Solo se incluyen profesores activos.",
    )

    materias = forms.MultipleChoiceField(
        label="Materias y secciones",
        widget=forms.SelectMultiple(),
    )

    def obtener_materias_disponibles(self) -> "list[tuple[str, str]]":
        """
        Obtiene todas las combinaciones posibles de (sección, materia) que están:
        1. Disponibles en AñoMateria (materias asignadas a algún año)
        2. NO están ya asignadas en ProfesorMateria
        """

        asignaciones_existentes = ProfesorMateria.objects.values(
            "seccion_id", "materia_id"
        )

        # Construimos una subconsulta para excluir asignaciones existentes
        combinaciones_excluir = [
            (asignacion["seccion_id"], asignacion["materia_id"])
            for asignacion in asignaciones_existentes
        ]

        # Obtenemos todas las secciones con sus años y materias disponibles
        materias_disponibles = []

        # Primero obtenemos todas las materias por año
        años_materias = AñoMateria.objects.select_related(
            nc(AñoMateria.año), nc(AñoMateria.materia)
        ).values(
            f"{nc(AñoMateria.año)}_id",
            f"{nc(AñoMateria.materia)}_id",
            f"{nc(AñoMateria.materia)}__nombre",
        )

        for año_materia in años_materias:
            # Obtenemos todas las secciones de este año
            secciones = Seccion.objects.values("id", "nombre").filter(
                año__id=año_materia["año_id"]
            )

            for seccion in secciones:
                # Verificamos si esta combinación ya está asignada
                if (
                    seccion["id"],
                    año_materia["materia_id"],
                ) not in combinaciones_excluir:
                    opcion_id = f"{seccion['id']}_{año_materia['materia_id']}"
                    label = f"{año_materia['materia__nombre']}_{seccion['nombre']}"
                    materias_disponibles.append((opcion_id, label))

        # Ordenamos por label
        materias_disponibles.sort(key=lambda x: x[1])

        return materias_disponibles

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data:
            raise forms.ValidationError("No se obtuvieron los datos")

        profesor = cleaned_data.get(nc(ProfesorMateria.profesor))
        materias = cleaned_data.get(f"{nc(ProfesorMateria.materia)}s", ())

        if profesor and materias:
            # Verificamos nuevamente que las materias seleccionadas sigan disponibles
            materias_disponibles_dict = dict(self.obtener_materias_disponibles())

            for materia_opcion in materias:
                if materia_opcion not in materias_disponibles_dict:
                    nombre_materia = materias_disponibles_dict.get(
                        str(materia_opcion), "NOMBRE MATERIA"
                    )

                    self.add_error(
                        "materias",
                        f"La materia '{nombre_materia}' ya está asignada a otro profesor",
                    )

        return cleaned_data

    def save(self, commit: bool = True):
        """
        Guarda todas las asignaciones seleccionadas
        """
        profesor = self.cleaned_data["profesor"]
        materias_seleccionadas = self.cleaned_data["materias"]

        combos_seccion_materia = tuple(
            # Obtener los ID del compuesto (seccion_id, materia_id)
            tuple(map(int, materia_opcion.split("_")))
            for materia_opcion in materias_seleccionadas
        )

        # Agregamos todas las asignaciones de una vez
        asignaciones = ProfesorMateria.objects.bulk_create(
            tuple(
                ProfesorMateria(
                    profesor=profesor, seccion_id=seccion_id, materia_id=materia_id
                )
                for seccion_id, materia_id in combos_seccion_materia
            ),
            ignore_conflicts=True,
        )

        return asignaciones


class FormTransferirProfesorMateria(forms.Form):
    class Campos:
        PROFESOR = "profesor"
        MATERIAS = "pms"

    profesor = forms.ModelChoiceField(
        queryset=Profesor.objects.filter(**{nc(Profesor.activo): True}).all(),
        label="Profesor para transferirle las asignaciones",
    )

    pms = forms.ModelMultipleChoiceField(ProfesorMateria.objects.all(), initial=None)


class FormEstudiante(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = (
            nc(Estudiante.nombres),
            nc(Estudiante.apellidos),
            nc(Estudiante.cedula),
            nc(Estudiante.cedula),
            nc(Estudiante.sexo),
            nc(Estudiante.fecha_nacimiento),
        )

        widgets = {
            nc(Estudiante.fecha_nacimiento): forms.DateInput(attrs={"type": "date"}),
        }

    field_order = (
        nc(Estudiante.nombres),
        nc(Estudiante.apellidos),
        nc(Estudiante.cedula),
        nc(Estudiante.sexo),
        nc(Estudiante.fecha_nacimiento),
    )


class FormMatricularEstudiantes(forms.Form):
    """Usado en la sección de estudiantes por medio del modal"""

    lapso_actual = obtener_lapso_actual() if not MIGRANDO else None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.lapso_actual:
            # No se pueden matricular estudiantes que ya estén matriculados en el lapso actual
            self.fields["estudiantes"].queryset = Estudiante.objects.exclude(  # type: ignore - sí se puede asignar el queryset
                matricula__lapso=self.lapso_actual
            )

    estudiantes = forms.ModelMultipleChoiceField(
        queryset=Estudiante.objects.none() if not MIGRANDO else None
    )

    seccion = forms.ModelChoiceField(
        queryset=Seccion.objects.all() if not MIGRANDO else None
    )

    def save(self):
        estudiantes = self.cleaned_data["estudiantes"]
        seccion = self.cleaned_data["seccion"]

        return Matricula.objects.bulk_create(
            tuple(
                Matricula(
                    estudiante=estudiante, seccion=seccion, lapso=self.lapso_actual
                )
                for estudiante in estudiantes
            )
        )
