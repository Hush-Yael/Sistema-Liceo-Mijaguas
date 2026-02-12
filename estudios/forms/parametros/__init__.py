from django import forms
from django.db.models import Exists

from app.util import nc
from estudios.forms import obtener_matriculas_de_lapso
from estudios.modelos.gestion.personas import Estudiante, Matricula, MatriculaEstados
from estudios.modelos.parametros import (
    Materia,
    Lapso,
    Seccion,
)
from estudios.modelos.parametros import (
    Año,
    AñoMateria,
    obtener_lapso_actual,
)
from datetime import date, datetime
from app.settings import MIGRANDO


class FormAño(forms.ModelForm):
    class Meta:
        model = Año
        fields = ("nombre", "nombre_corto")
        labels = {
            "nombre": "Nombre completo del año",
            "nombre_corto": "Nombre corto del año",
        }

        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Primer año"}),
            "nombre_corto": forms.TextInput(attrs={"placeholder": "Ej: 1ero"}),
        }


class FormLapso(forms.ModelForm):
    class Meta:
        model = Lapso
        fields = "__all__"

        widgets = {
            nc(Lapso.numero): forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "Ejemplo: 3",
                }
            ),
            nc(Lapso.nombre): forms.TextInput(
                attrs={
                    "placeholder": f"Ejemplo: {date.today().year}-III",
                }
            ),
            nc(Lapso.fecha_inicio): forms.DateInput(attrs={"type": "date"}),
            nc(Lapso.fecha_fin): forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            hoy = date.today()

            self.fields["fecha_inicio"].widget.attrs["min"] = hoy.strftime("%Y-%m-%d")
            self.fields["fecha_fin"].widget.attrs["min"] = hoy.replace(
                day=hoy.day + 1
            ).strftime("%Y-%m-%d")

        # No se pueden editar las fechas de un lapso ya creado si no es el actual
        else:
            lapso_actual = self.lapso_actual = obtener_lapso_actual()

            if lapso_actual != self.instance:
                self.fields["fecha_inicio"].disabled = True
                self.fields["fecha_fin"].disabled = True

    lapso_actual: "Lapso | None"

    def clean_fecha_inicio(self):
        fecha_inicio: "date | None" = self.cleaned_data.get("fecha_inicio")

        if fecha_inicio:
            # los valores no se pueden cambiar si el lapso no es el actual
            if self.instance.pk and self.instance != self.lapso_actual:
                return self.instance.fecha_inicio

            elif fecha_inicio < datetime.now().date():
                raise forms.ValidationError(
                    "La fecha de inicio no puede ser anterior a la actual"
                )

        return fecha_inicio

    def clean_fecha_fin(self):
        fecha_fin: "date | None" = self.cleaned_data.get("fecha_fin")

        if fecha_fin:
            # los valores no se pueden cambiar si el lapso no es el actual
            if self.instance.pk and self.instance != self.lapso_actual:
                return self.instance.fecha_fin
            else:
                hoy = date.today()

                if fecha_fin <= hoy:
                    raise forms.ValidationError(
                        "La fecha de fin debe ser posterior a la actual"
                    )
                elif fecha_fin < self.cleaned_data.get("fecha_inicio"):  # type: ignore
                    raise forms.ValidationError(
                        "La fecha de fin debe ser posterior a la de inicio"
                    )

        return fecha_fin


def asignaciones_campo():
    return forms.ModelMultipleChoiceField(
        queryset=Año.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"id": "materia"}),
        initial=[],
        required=False,
    )


class FormMateria(forms.ModelForm):
    asignaciones = asignaciones_campo()

    class Meta:
        model = Materia
        fields = ("nombre", "asignaciones")
        labels = {
            "nombre": "Nombre de la materia",
        }

        widgets = {
            nc(Materia.nombre): forms.TextInput,
        }


class FormAsignaciones(forms.ModelForm):
    asignaciones = asignaciones_campo()

    class Meta:
        model = AñoMateria
        fields = ("asignaciones",)


class FormSeccion(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["vocero"].label_from_instance = (  # type: ignore
            lambda obj: obj.nombres + " " + obj.apellidos
        )

        lapso_actual = self.lapso_actual = obtener_lapso_actual()

        if lapso_actual is not None:
            # al editar, cambiar las opciones del vocero por los estudiantes activos matriculados en la sección
            if self.instance.pk:
                self.fields["vocero"].queryset = (  # type: ignore
                    Estudiante.objects.filter(
                        matricula__seccion=self.instance,
                        matricula__lapso=lapso_actual,
                        matricula__estado=MatriculaEstados.ACTIVO,
                    )
                )
            # al crear, cambiar las opciones del vocero por los estudiantes NO matriculados y no graduados, de modo que se matricule en la sección al crearse
            else:
                self.fields["vocero"].queryset = (  # type: ignore
                    Estudiante.objects.annotate(
                        matriculado_actualmente=Exists(
                            obtener_matriculas_de_lapso(lapso_actual)
                        )
                    )
                    .filter(matriculado_actualmente=False, bachiller__isnull=True)
                    .order_by("apellidos", "nombres")
                )

    class Meta:
        model = Seccion
        fields = (
            nc(Seccion.año),
            nc(Seccion.nombre),
            nc(Seccion.letra),  # type: ignore
            nc(Seccion.capacidad),
            nc(Seccion.vocero),
        )

    vocero = forms.ModelChoiceField(
        queryset=Estudiante.objects.none() if not MIGRANDO else None,
        required=False,
    )

    lapso_actual: "Lapso | None" = None

    def clean_vocero(self):
        if vocero := self.cleaned_data.get("vocero"):
            editando = self.instance.pk is not None
            q = Matricula.objects.filter(estudiante=vocero, lapso=self.lapso_actual)

            if editando:
                if not q.filter(seccion=self.instance).exists():
                    raise forms.ValidationError(
                        "El vocero debe estar matriculado en el sección seleccionada"
                    )
            # creando
            else:
                if q.exists():
                    raise forms.ValidationError(
                        "El estudiante ya tiene una sección asignada"
                    )

        return vocero

    def clean_letra(self):
        if letra := self.cleaned_data.get("letra"):
            if (año := self.cleaned_data.get("año")) and Seccion.objects.filter(
                letra=letra.upper(), año=año
            ).exists():
                raise forms.ValidationError("Ya existe una sección con esa letra")

        return letra

    def save(self, commit: bool = True):
        instance = super().save(commit)

        editando = self.instance.pk is not None

        if not editando and self.cleaned_data.get("vocero"):
            Matricula.objects.create(
                estudiante=self.cleaned_data.get("vocero"),
                seccion=instance,
                lapso=self.lapso_actual,
                estado=MatriculaEstados.ACTIVO,
            )

        return instance
