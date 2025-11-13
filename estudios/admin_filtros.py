from django.contrib import admin
from estudios.models import Lapso, Materia, ProfesorMateria, Seccion, Año


class SeccionLetraFiltro(admin.SimpleListFilter):
    title = "Letra de la sección"
    parameter_name = "letra"

    def lookups(self, request, model_admin):
        letras = (
            Seccion.objects.values_list("letra", flat=True).order_by("letra").distinct()
        )

        return [(letra, letra) for letra in letras]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(seccion__letra=self.value())


class AñoNombreCortoFiltro(admin.SimpleListFilter):
    title = "Año"
    parameter_name = "anio"

    def lookups(self, request, model_admin):
        años = Año.objects.values("id", "nombre_corto")

        return [(a["id"], a["nombre_corto"]) for a in años]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        return queryset.filter(seccion__año_id=self.value())


class NotaSeccionFiltro(admin.SimpleListFilter):
    title = "Letra de la sección"
    parameter_name = "letra"

    def lookups(self, request, model_admin):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            secciones_letras = (
                ProfesorMateria.objects.filter(profesor=request.user.profesor)
                .values_list("seccion__letra", flat=True)
                .order_by("seccion__letra")
                .distinct()
            )
            return [(letra, letra) for letra in secciones_letras]  # pyright: ignore[reportAttributeAccessIssue]

        return [
            (letra, letra)  # pyright: ignore[reportAttributeAccessIssue]
            for letra in Seccion.objects.values_list("letra", flat=True)
            .order_by("letra")
            .distinct()
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(matricula__seccion__letra=self.value())


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
        return queryset.filter(matricula__lapso__id=self.value())


class NotaAñoNombreCortoFiltro(admin.SimpleListFilter):
    title = "Año"
    parameter_name = "anio"

    def lookups(self, request, model_admin):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            años_profesor = (
                ProfesorMateria.objects.filter(profesor=request.user.profesor)
                .values_list("seccion__año__id", flat=True)
                .distinct()
            )

            años = (
                Año.objects.filter(id__in=años_profesor)
                .values("seccion__año__id", "seccion__año__nombre_corto")
                .order_by("seccion__año__numero")
                .distinct()
            )

            return [
                (año["seccion__año__id"], año["seccion__año__nombre_corto"])
                for año in años
            ]
        # todos los años
        else:
            años = Año.objects.values("id", "nombre_corto").order_by("numero")

            return [
                (año["id"], año["nombre_corto"])  # pyright: ignore[reportAttributeAccessIssue]
                for año in años
            ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        return queryset.filter(matricula__seccion__año_id=self.value())


class NotaMateriaFiltro(admin.SimpleListFilter):
    title = "Materia"
    parameter_name = "materia"

    def lookups(self, request, model_admin):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            materias = (
                ProfesorMateria.objects.filter(profesor=request.user.profesor)
                .values("materia__id", "materia__nombre")
                .distinct()
            )

            return [
                (materia["materia__id"], materia["materia__nombre"])
                for materia in materias
            ]

        return [
            (materia.pk, str(materia))
            for materia in Materia.objects.all().order_by("nombre")
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(materia__id=self.value())
