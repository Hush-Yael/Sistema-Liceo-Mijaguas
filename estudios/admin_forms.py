from django import forms
from django.utils.datetime_safe import datetime
from .models import (
    Seccion,
    Materia,
    Estudiante,
    Lapso,
    ProfesorMateria,
    Nota,
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
