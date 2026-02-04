from django.contrib import admin
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from estudios.modelos.gestion import ProfesorMateria
from estudios.admin.parametros.forms import LapsoAdminForm
from estudios.modelos.parametros import Lapso, Materia, Seccion, Año, AñoMateria


@admin.register(Año)
class AñoAdmin(ModelAdmin):
    list_display = ["nombre", "nombre_corto", "fecha_creacion"]
    search_fields = ["nombre"]
    readonly_fields = ["fecha_creacion"]


@admin.register(Seccion)
class SeccionAdmin(ModelAdmin):
    list_display = [
        "nombre",
        "letra",
        # "vocero",
        "capacidad",
    ]
    list_filter = ["año", "letra"]
    search_fields = ["nombre", "letra"]
    # autocomplete_fields = ["vocero"]
    readonly_fields = ["fecha_creacion"]

    def get_list_display(self, request: HttpRequest):
        columnas = [*super().get_list_display(request)]

        if "año__id__exact" in request.GET:
            columnas.remove("año")

        if "letra" in request.GET:
            columnas.remove("letra")

        return columnas


@admin.register(Materia)
class MateriaAdmin(ModelAdmin):
    list_display = ["nombre", "fecha_creacion"]
    search_fields = ["nombre"]
    readonly_fields = ["fecha_creacion"]

    # Alterar los resultados del autocompletado
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        modelo = request.GET.get("model_name")

        # Si se pide desde notas y es profesor, solo retornar sus materias asignadas
        if (
            modelo == "nota"
            and hasattr(request.user, "profesor")
            and not request.user.is_superuser  # pyright: ignore
        ):
            profesor = request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]
            materias_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("materia_id", flat=True)

            queryset = queryset.filter(id__in=materias_profesor)

        return queryset, use_distinct


@admin.register(Lapso)
class LapsoAdmin(ModelAdmin):
    form = LapsoAdminForm
    list_display = ["numero", "nombre", "fecha_inicio", "fecha_fin"]
    list_filter = ["numero"]
    search_fields = ["nombre"]


@admin.register(AñoMateria)
class AñoMateriaAdmin(ModelAdmin):
    list_display = ["año", "materia"]
    list_filter = ["año", "materia"]
    search_fields = ["materia__nombre"]
    autocomplete_fields = ["materia"]
