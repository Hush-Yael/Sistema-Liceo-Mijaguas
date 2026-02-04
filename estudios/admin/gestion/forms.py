from django import forms
from estudios.modelos.parametros import Año, AñoMateria, Seccion, Materia, Lapso
from estudios.modelos.gestion import (
    Bachiller,
    Matricula,
    ProfesorMateria,
    Nota,
)
from django.db.models import Avg


class MatriculaAdminForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = "__all__"

    def clean_estudiante(self):
        estudiante = self.cleaned_data.get("estudiante")

        if estudiante is not None:
            es_bachiller = Bachiller.objects.filter(estudiante=estudiante).exists()

            if es_bachiller:
                raise forms.ValidationError("El estudiante ya es bachiller")

        return estudiante

    def clean_seccion(self):
        seccion = self.cleaned_data.get("seccion")

        if seccion is not None:
            cantidad_maxima = Seccion.objects.get(id=seccion.id).capacidad
            cantidad_actual = Matricula.objects.filter(seccion=seccion).count()

            if cantidad_actual >= cantidad_maxima:
                raise forms.ValidationError(
                    f"La sección seleccionada se encuentra llena (capacidad máxima: {cantidad_maxima})"
                )

        return seccion

    def clean_lapso(self):
        return Lapso.objects.last()


class NotaAdminForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cambiar los widgets para autocompletado nativo de Django
        self.fields["matricula"].widget.attrs["data-ajax--url"] = (
            "/admin/sistema_escolar/matricula/autocomplete/"
        )

        self.fields["materia"].widget.attrs["data-ajax--url"] = (
            "/admin/sistema_escolar/materia/autocomplete/"
        )

        # Limitar los querysets como antes
        if hasattr(self.request.user, "profesor"):  # pyright: ignore[reportAttributeAccessIssue]
            profesor = self.request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]

            secciones_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("seccion_id", flat=True)

            self.fields["matricula"].queryset = Matricula.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                seccion__id__in=secciones_profesor
            )

            materias_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("materia_id", flat=True)

            self.fields["materia"].queryset = Materia.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                id__in=materias_profesor
            )

    def clean_materia(self):
        materia: Materia = self.cleaned_data.get("materia")  # pyright: ignore[reportAssignmentType]

        if materia is not None:
            matricula: Matricula = self.cleaned_data.get("matricula")  # pyright: ignore[reportAssignmentType]

            if not matricula:
                return materia

            seccion = matricula.seccion

            if not seccion:
                return materia

            año = seccion.año  # pyright: ignore[reportOptionalMemberAccess]

            if not año or materia.pk not in AñoMateria.objects.filter(
                año=año
            ).values_list("materia_id", flat=True):
                raise forms.ValidationError(
                    "La materia no está asignada para el año de matrícula seleccionada"
                )

        return materia

    def clean_matricula(self):
        matricula: Matricula = self.cleaned_data.get("matricula")  # pyright: ignore[reportAssignmentType]

        if matricula is not None:
            inactivo = matricula.estado == "inactivo"
            es_bachiller = Bachiller.objects.filter(
                estudiante=matricula.estudiante
            ).exists()

            if inactivo or es_bachiller:
                raise forms.ValidationError(
                    f"El estudiante {'no se encuentra activo' if inactivo else 'ya es bachiller'}"
                )

            lapso = matricula.lapso

            if lapso != Lapso.objects.last():
                raise forms.ValidationError(
                    "La matrícula seleccionada no pertenece al lapso actual"
                )

        return matricula


class ProfesorMateriaAdminForm(forms.ModelForm):
    class Meta:
        model = ProfesorMateria
        fields = "__all__"

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


class BachillerAdminForm(forms.ModelForm):
    class Meta:
        model = Bachiller
        fields = "__all__"

    def clean_estudiante(self):
        estudiante = self.cleaned_data.get("estudiante")

        if estudiante is not None:
            es_bachiller = Bachiller.objects.filter(estudiante=estudiante).exists()  # pyright: ignore[reportOptionalMemberAccess]

            if es_bachiller:
                raise forms.ValidationError("El estudiante ya es bachiller")

            ultimo_año = Año.objects.last()

            if ultimo_año is None:
                raise forms.ValidationError(
                    "No se encontró el último año académico disponible"
                )

            lapso_anterior = Lapso.objects.order_by("-id")[1:2]

            if len(lapso_anterior) == 0:
                raise forms.ValidationError("No se encontró el lapso anterior")

            try:
                matricula = Matricula.objects.get(
                    estudiante=estudiante, lapso=lapso_anterior
                )

                if matricula.seccion.año.numero < ultimo_año.numero:
                    raise forms.ValidationError(
                        f"El estudiante debe haberse matriculado en {ultimo_año.nombre} en el lapso anterior"
                    )

                promedio = (
                    Nota.objects.filter(matricula__estudiante=estudiante)
                    .aggregate(promedio=Avg("valor"))
                    .get("promedio")
                )

                if promedio is None:
                    raise forms.ValidationError(
                        "No se encontraron notas asociadas al estudiante"
                    )

                if promedio < 10:
                    raise forms.ValidationError(
                        "El promedio total del estudiante es menor a 10"
                    )
            except Matricula.DoesNotExist:
                raise forms.ValidationError(
                    "El estudiante no se encontró matriculado en el lapso anterior"
                )

        return estudiante
