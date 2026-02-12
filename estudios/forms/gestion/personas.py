from typing import Any
from django import forms
from django.db.models import Exists
from usuarios.models import Usuario
from app.settings import MIGRANDO
from estudios.forms import LapsoActualForm, obtener_matriculas_de_lapso
from estudios.modelos.gestion.personas import (
    Estudiante,
    Matricula,
    Profesor,
    ProfesorMateria,
)
from estudios.modelos.parametros import (
    Lapso,
    Materia,
    Seccion,
    obtener_lapso_actual,
)
from usuarios.models import GruposBase


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
            Matricula.estudiante.field.name,
            Matricula.seccion.field.name,
            Matricula.estado.field.name,
            Matricula.lapso.field.name,
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
        exclude = (Profesor.fecha_ingreso.field.name,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campo_usuario: forms.ModelChoiceField = self.fields[nc(Profesor.usuario)]  # type: ignore

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


class FormProfesorMateria(forms.ModelForm):
    class Meta:
        model = ProfesorMateria
        # excluir el campo "materia", ya que este form permite añadir varias materias a la vez
        exclude = (ProfesorMateria.materia.field.name,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["profesor"].queryset.filter(  # type: ignore
            usuario__is_active=True
        ).order_by("apellidos", "nombres")

        self.fields["secciones"].label_from_instance = lambda obj: obj.nombre  # type: ignore

    secciones = forms.ModelMultipleChoiceField(
        label="Secciones",
        queryset=Seccion.objects.order_by("año", "letra") if not MIGRANDO else None,
    )

    def save(self, commit: bool = True):
        secciones: "list[Seccion]" = self.cleaned_data.get("secciones", [])
        materia: "Materia | None" = self.cleaned_data.get(
            self.Meta.model.materia.field.name
        )
        profesor: "Profesor | None" = self.cleaned_data.get(
            self.Meta.model.profesor.field.name
        )

        if secciones:
            ProfesorMateria.objects.bulk_create(
                tuple(
                    ProfesorMateria(profesor=profesor, materia=materia, seccion=seccion)
                    for seccion in secciones
                )
            )
