from django import forms
from django.utils.datetime_safe import datetime
from .models import (
    Matricula,
    Seccion,
    Materia,
    Estudiante,
    Lapso,
    ProfesorMateria,
    Nota,
    AñoMateria,
)


class MatriculaAdminForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = "__all__"

    def clean_estudiante(self):
        estudiante_cedula = self.data.get("estudiante")

        if estudiante_cedula is not None:
            estudiante_cedula = int(estudiante_cedula)
            estado = Estudiante.objects.get(cedula=estudiante_cedula).estado  # pyright: ignore[reportOptionalMemberAccess]

            if estado != "activo":
                raise forms.ValidationError(
                    f"El estudiante {'no se encuentra activo' if estado == 'inactivo' else 'se encuentra graduado'}"
                )

        return estudiante_cedula

    def clean_seccion(self):
        seccion = self.cleaned_data.get("seccion")

        if seccion is not None:
            cantidad_maxima = Seccion.objects.get(id=seccion.id).capacidad_maxima
            cantidad_actual = Matricula.objects.filter(seccion=seccion).count()

            if cantidad_actual >= cantidad_maxima:
                raise forms.ValidationError(
                    f"La sección seleccionada se encuentra llena (capacidad máxima: {cantidad_maxima})"
                )

        return seccion


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

    def clean_estudiante(self):
        estudiante = self.cleaned_data["estudiante"]

        if estudiante is not None:
            if estudiante.estado != "activo":
                raise forms.ValidationError(
                    f"El estudiante {'no se encuentra activo' if estudiante.estado == 'inactivo' else 'se encuentra graduado'}"
                )

            matricula = Matricula.objects.get(estudiante=estudiante)
            estudiante_seccion = matricula.seccion

            if estudiante_seccion is None:
                raise forms.ValidationError(
                    "El estudiante no se encuentra matriculado en ninguna sección"
                )

            seccion_id = self.data.get("seccion")

            if seccion_id is not None:
                seccion_id = int(seccion_id)

                if seccion_id != estudiante_seccion.id:  # pyright: ignore[reportAttributeAccessIssue]
                    raise forms.ValidationError(
                        "El estudiante no se encuentra matriculado en la sección seleccionada"
                    )

        return estudiante


class ProfesorMateriaAdminForm(forms.ModelForm):
    class Meta:
        model = ProfesorMateria
        fields = "__all__"

    def clean_seccion(self):
        profesor = self.cleaned_data.get("profesor")
        seccion = self.cleaned_data.get("seccion")
        materia = self.cleaned_data.get("materia")

        if not profesor or not materia:
            return seccion

        if seccion is not None:
            try:
                ya_asignada = ProfesorMateria.objects.get(
                    seccion=seccion,
                    materia=materia,
                )

                if ya_asignada:  # type: ignore
                    raise forms.ValidationError(
                        f"""{
                            "El profesor seleccionado ya tiene asignada"
                            if ya_asignada.profesor == profesor
                            else "Ya existe un profesor asignado para"
                        } esa materia en esa sección"""
                    )
            except ProfesorMateria.DoesNotExist:
                pass

        return seccion

    def clean_materia(self):
        materia = self.cleaned_data.get("materia")

        if materia is not None:
            seccion_id = self.data.get("seccion")

            if seccion_id is not None and seccion_id is not int:
                seccion_id = int(seccion_id)

            año = Seccion.objects.get(id=seccion_id).año

            if año is None or materia.id not in AñoMateria.objects.filter(
                año=año
            ).values_list("materia_id", flat=True):
                raise forms.ValidationError(
                    "La materia no está asignada para el año de la sección seleccionada"
                )

        return materia
