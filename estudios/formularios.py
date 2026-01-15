from django import forms
from django.db.models import Exists, OuterRef
from .models import (
    Estudiante,
    Matricula,
    MatriculaEstados,
    Seccion,
    Año,
    Materia,
    Lapso,
    AñoMateria,
    obtener_lapso_actual,
)
from datetime import date


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
            "numero": forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "Ej: 3",
                }
            ),
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": f"Ej: {date.today().year}-III",
                }
            ),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }


asignaciones_campo = forms.ModelMultipleChoiceField(
    queryset=Año.objects.all(),
    widget=forms.CheckboxSelectMultiple(attrs={"id": "materia"}),
    initial=[],
    required=False,
)


class FormMateria(forms.ModelForm):
    asignaciones = asignaciones_campo

    class Meta:
        model = Materia
        fields = ("nombre", "asignaciones")
        labels = {
            "nombre": "Nombre de la materia",
        }

        widgets = {
            "nombre": forms.TextInput,
        }


class FormAsignaciones(forms.ModelForm):
    asignaciones = asignaciones_campo

    class Meta:
        model = AñoMateria
        fields = ("asignaciones",)


def obtener_matriculas_de_lapso(lapso: Lapso):
    """filtra los estudiantes y devuelve aquellos matriculados en un lapso específico"""
    return Matricula.objects.filter(estudiante=OuterRef("pk"), lapso=lapso)


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
        fields = ("año", "nombre", "letra", "capacidad", "vocero")

    vocero = forms.ModelChoiceField(
        queryset=Estudiante.objects.none(),
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


class FormMatricula(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["seccion"].label_from_instance = lambda obj: obj.nombre  # type: ignore

        lapso_actual = self.lapso_actual = obtener_lapso_actual()

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
        fields = ("estudiante", "seccion", "estado", "lapso")

    lapso_actual: "Lapso | None" = None

    estudiante = forms.ModelChoiceField(
        label="Estudiante",
        queryset=Estudiante.objects.none(),
    )

    seccion = forms.ModelChoiceField(
        label="Sección",
        queryset=Seccion.objects.all().order_by("año", "letra"),
    )

    lapso = forms.ChoiceField(
        label="Lapso",
        required=False,
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

    def clean_lapso(self):
        lapso = self.lapso_actual

        if lapso is None:
            raise forms.ValidationError("No se encontró un lapso actual")

        return lapso
