from django import forms
from app.util import nc
from estudios.forms import LapsoActualForm
from estudios.modelos.gestion.calificaciones import (
    Tarea,
    TareaProfesorMateria,
    TipoTarea,
)
from estudios.modelos.gestion.personas import Profesor, ProfesorMateria
from app.settings import MIGRANDO
from estudios.modelos.parametros import obtener_lapso_actual


class FormTipoTarea(forms.ModelForm):
    class Meta:
        model = TipoTarea
        fields = "__all__"

        widgets = {
            "descripcion": forms.Textarea(),
        }


class FormTarea(LapsoActualForm, forms.ModelForm):
    class Meta:
        model = Tarea
        fields = (nc(Tarea.tipo),)

    def __init__(self, *args, **kwargs):
        profesor: "Profesor | None" = kwargs.pop("profesor", None)

        super().__init__(*args, **kwargs)

        self.fields["profesormateria"].label_from_instance = (  # type: ignore
            lambda obj: f"{obj.materia.nombre} ({obj.seccion.nombre})"
        )

        if profesor:
            self.profesor = profesor

            # Limitar las materias a las asignadas al profesor
            self.fields["profesormateria"].queryset = (  # type: ignore
                ProfesorMateria.objects.filter(profesor=profesor)
            )

            # Al editar, incluir las materias asignadas a la tarea
            if self.instance.pk:
                self.fields["profesormateria"].initial = (  # type: ignore
                    ProfesorMateria.objects.filter(
                        tareaprofesormateria__tarea=self.instance
                    )
                )

    profesormateria = forms.ModelMultipleChoiceField(
        label="Materias",
        queryset=ProfesorMateria.objects.none() if not MIGRANDO else None,
        required=False,
    )

    def save(self, commit=False):
        if not self.profesor:
            raise forms.ValidationError(
                "Usted no puede crear tareas, pues no es profesor"
            )

        tarea = super().save(commit)
        tarea.lapso = obtener_lapso_actual()
        tarea.profesor = self.profesor

        tarea.save()

        pms: "list[ProfesorMateria] | None" = self.cleaned_data.get("profesormateria")

        if not pms:
            return tarea

        nuevas_tareas = tuple(
            TareaProfesorMateria(
                tarea=tarea,
                profesormateria=pm,
            )
            for pm in pms
        )

        TareaProfesorMateria.objects.bulk_create(nuevas_tareas, ignore_conflicts=True)

        return tarea
