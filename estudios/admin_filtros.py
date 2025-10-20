from django.contrib import admin
from estudios.models import Lapso, Materia, ProfesorMateria, Seccion, Año


class SeccionLetraFiltro(admin.SimpleListFilter):
    title = "Sección"
    parameter_name = "seccion"

    def lookups(self, request, model_admin):
        letras = (
            Seccion.objects.values_list("letra_seccion", flat=True)
            .order_by("letra_seccion")
            .distinct()
        )

        return [(letra, letra) for letra in letras]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(seccion__letra_seccion=self.value())


class NotaSeccionFiltro(admin.SimpleListFilter):
    title = "Sección"
    parameter_name = "seccion"

    def lookups(self, request, model_admin):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            from estudios.admin import ProfesorPermissionMixin

            secciones_profesor = ProfesorPermissionMixin.get_profesor_secciones(
                request.user
            )

            secciones = Seccion.objects.filter(id__in=secciones_profesor).order_by(
                "letra_seccion"
            )

            return [(seccion.id, str(seccion)) for seccion in secciones]  # pyright: ignore[reportAttributeAccessIssue]

        return [
            (seccion.id, str(seccion))  # pyright: ignore[reportAttributeAccessIssue]
            for seccion in Seccion.objects.all().order_by(
                "año__numero_año", "letra_seccion"
            )
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(seccion__id=self.value())


class NotaLapsoFiltro(admin.SimpleListFilter):
    title = "Lapso"
    parameter_name = "lapso"

    def lookups(self, request, model_admin):
        # si es profesor, no se puede filtrar para ver las notas de otros lapso, ya que solo se muestran las del actual
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            return []
        # todos los lapsos
        else:
            return [
                (lapso.id, str(lapso))  # pyright: ignore[reportAttributeAccessIssue]
                for lapso in Lapso.objects.all().order_by("-id")
            ]

    def queryset(self, request, queryset):
        if (
            hasattr(request.user, "profesor") and not request.user.is_superuser
        ) or self.value() is None:
            return queryset
        return queryset.filter(lapso__id=self.value())


class AñosAPartirSeccionesFiltro(admin.SimpleListFilter):
    title = "Año"
    parameter_name = "anio"

    def lookups(self, request, model_admin):
        años = Año.objects.values("id", "nombre_año_corto")

        return [(a["id"], a["nombre_año_corto"]) for a in años]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        return queryset.filter(seccion__año_id=self.value())


class NotaMateriaFiltro(admin.SimpleListFilter):
    title = "Materia"
    parameter_name = "materia"

    def lookups(self, request, model_admin):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            materias = ProfesorMateria.objects.filter(
                profesor=request.user.profesor
            ).values("materia__id", "materia__nombre_materia")

            return [
                (materia["materia__id"], materia["materia__nombre_materia"])
                for materia in materias
            ]

        return [
            (materia.id, str(materia))  # pyright: ignore[reportAttributeAccessIssue]
            for materia in Materia.objects.all().order_by("nombre_materia")
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(materia__id=self.value())
