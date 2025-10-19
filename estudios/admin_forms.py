from django import forms
from django.utils.datetime_safe import datetime
from .models import (
    Seccion,
    Materia,
    Estudiante,
    Lapso,
    ProfesorMateria,
    Nota,
    AñoMateria,
)


class LapsoAdminForm(forms.ModelForm):
    class Meta:
        model = Lapso
        fields = "__all__"

    def clean_fecha_inicio(self):
        fecha = self.cleaned_data.get("fecha_inicio")

        if fecha is None:
            return

        if fecha < datetime.now().date():
            raise forms.ValidationError(
                "La fecha de inicio debe ser mayor o igual a la fecha actual"
            )

        return fecha

    def clean_fecha_fin(self):
        fecha = self.cleaned_data.get("fecha_fin")

        if fecha is None:
            return

        if fecha < datetime.now().date():
            raise forms.ValidationError(
                "La fecha de fin debe ser mayor o igual al año actual"
            )

        fecha_inicio = self.cleaned_data.get("fecha_inicio")

        if fecha_inicio is None:
            return fecha

        if fecha <= fecha_inicio:
            raise forms.ValidationError(
                "La fecha de fin debe ser mayor o igual a la fecha de inicio"
            )

        return fecha


class NotaAdminForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cambiar los widgets para autocompletado nativo de Django
        self.fields["estudiante"].widget.attrs["data-ajax--url"] = (
            "/admin/sistema_escolar/estudiante/autocomplete/"
        )

        self.fields["materia"].widget.attrs["data-ajax--url"] = (
            "/admin/sistema_escolar/materia/autocomplete/"
        )

        self.fields["seccion"].widget.attrs["data-ajax--url"] = (
            "/admin/sistema_escolar/seccion/autocomplete/"
        )

        # Limitar los querysets como antes
        if hasattr(self.request.user, "profesor"):  # pyright: ignore[reportAttributeAccessIssue]
            profesor = self.request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]
            secciones_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("seccion_id", flat=True)
            materias_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("materia_id", flat=True)

            self.fields["seccion"].queryset = Seccion.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                id__in=secciones_profesor
            )
            self.fields["materia"].queryset = Materia.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                id__in=materias_profesor
            )
            self.fields["estudiante"].queryset = Estudiante.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                matricula__seccion_id__in=secciones_profesor
            ).distinct()

    def clean_materia(self):
        materia = self.cleaned_data.get("materia")

        if materia is not None:
            seccion = self.data.get("seccion")

            if not seccion:
                return materia

            año = Seccion.objects.get(id=int(seccion)).año  # pyright: ignore[reportOptionalMemberAccess]

            if not año or materia.id not in AñoMateria.objects.filter(
                año=año
            ).values_list("materia_id", flat=True):
                raise forms.ValidationError(
                    "La materia no está asignada para el año de la sección seleccionada"
                )

        return materia


class ProfesorMateriaAdminForm(forms.ModelForm):
    class Meta:
        model = ProfesorMateria
        fields = "__all__"

    def clean_seccion(self):
        profesor = self.cleaned_data.get("profesor")
        seccion = self.cleaned_data.get("seccion")
        año = self.cleaned_data.get("año")
        materia = self.cleaned_data.get("materia")

        if not profesor or not materia or not año:
            return seccion

        secciones_profesor = ProfesorMateria.objects.filter(
            profesor=profesor
        ).values_list("seccion_id", flat=True)

        # No se pueden asignar todas las secciones más de una vez, ni se pueden asignar secciones si ya se han asignado todas
        if None in secciones_profesor:
            raise forms.ValidationError(
                "El profesor ya tiene asignadas todas las secciones"
            )

        if seccion is not None:
            if seccion.id in secciones_profesor:  # type: ignore
                raise forms.ValidationError("El profesor ya tiene asignada esa sección")

            # La sección debe pertenecer al mismo año
            if (año := self.cleaned_data.get("año")) is not None:
                año_de_seccion = Seccion.objects.get(id=seccion.id).año  # type: ignore

                if año != año_de_seccion:  # type: ignore
                    raise forms.ValidationError(
                        "La sección debe pertenecer al mismo año"
                    )

        return seccion

    def clean_materia(self):
        materia = self.cleaned_data.get("materia")

        if materia is not None:
            año = self.data.get("año")

            if año is not None and año is not int:
                año = int(año)

            if año is None or materia.id not in AñoMateria.objects.filter(
                año=año
            ).values_list("materia_id", flat=True):
                raise forms.ValidationError(
                    "La materia no está asignada para el año seleccionado"
                )

        return materia
