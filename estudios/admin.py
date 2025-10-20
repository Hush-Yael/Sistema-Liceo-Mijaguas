from django.contrib import admin
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from estudios.admin_filtros import (
    NotaLapsoFiltro,
    NotaSeccionFiltro,
    SeccionLetraFiltro,
    AñosAPartirSeccionesFiltro,
)
from estudios.admin_forms import LapsoAdminForm, NotaAdminForm, ProfesorMateriaAdminForm
from .models import (
    Seccion,
    Año,
    Materia,
    Profesor,
    Estudiante,
    Lapso,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Nota,
)
from django.core.exceptions import PermissionDenied


@admin.register(Año)
class AñoAdmin(ModelAdmin):
    list_display = ["numero_año", "nombre_año", "nombre_año_corto", "fecha_creacion"]
    list_filter = ["numero_año"]
    search_fields = ["nombre_año", "numero_año"]
    readonly_fields = ["fecha_creacion"]


@admin.register(Seccion)
class SeccionAdmin(ModelAdmin):
    list_display = [
        "nombre_seccion",
        "letra_seccion",
        "vocero",
        "capacidad_maxima",
    ]
    list_filter = ["año", "letra_seccion"]
    search_fields = ["nombre_seccion", "letra_seccion"]
    autocomplete_fields = ["vocero"]
    readonly_fields = ["fecha_creacion"]

    # Alterar los resultados del autocompletado para solo mostrar las secciones del profesor (si están pidiendo desde ProfesorMateria)
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Si es profesor, solo retornar sus secciones asignadas
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            profesor = request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]
            secciones_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("seccion_id", flat=True)

            queryset = queryset.filter(id__in=secciones_profesor)

        return queryset, use_distinct

    def get_list_display(self, request: HttpRequest):
        columnas = [*super().get_list_display(request)]

        if "año__id__exact" in request.GET:
            columnas.remove("año")

        if "letra_seccion" in request.GET:
            columnas.remove("letra_seccion")

        return columnas


@admin.register(Materia)
class MateriaAdmin(ModelAdmin):
    list_display = ["nombre_materia", "fecha_creacion"]
    search_fields = ["nombre_materia"]
    readonly_fields = ["fecha_creacion"]

    # Alterar los resultados del autocompletado para solo mostrar las secciones del profesor (si están pidiendo desde ProfesorMateria)
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Si es profesor, solo retornar sus materias asignadas
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            profesor = request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]
            materias_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("materia_id", flat=True)

            queryset = queryset.filter(id__in=materias_profesor)

        return queryset, use_distinct


@admin.register(Profesor)
class ProfesorAdmin(ModelAdmin):
    list_display = [
        "nombres",
        "apellidos",
        "esta_activo",
    ]
    list_filter = ["esta_activo"]
    search_fields = ["nombres", "apellidos"]
    autocomplete_fields = ["usuario"]
    list_editable = ["esta_activo"]
    readonly_fields = ["fecha_ingreso"]


@admin.register(Estudiante)
class EstudianteAdmin(ModelAdmin):
    list_display = [
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "fecha_ingreso",
        "estado",
    ]
    list_filter = ["estado"]
    list_editable = ["estado"]
    search_fields = ["nombres", "apellidos"]

    # Alterar los resultados del autocompletado para solo mostrar las secciones del profesor (si están pidiendo desde ProfesorMateria)
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Si es profesor, solo retornar sus estudiantes asignados
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            profesor = request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]
            secciones_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("seccion_id", flat=True)

            queryset = queryset.filter(
                estado="activo",
                matricula__seccion_id__in=secciones_profesor,
            ).distinct()

        return queryset, use_distinct


@admin.register(Lapso)
class LapsoAdmin(ModelAdmin):
    form = LapsoAdminForm
    list_display = ["numero_lapso", "nombre_lapso", "fecha_inicio", "fecha_fin"]
    list_filter = ["numero_lapso"]
    search_fields = ["nombre_lapso"]


@admin.register(AñoMateria)
class AñoMateriaAdmin(ModelAdmin):
    list_display = ["año", "materia"]
    list_filter = ["año", "materia"]
    search_fields = ["materia__nombre_materia"]
    autocomplete_fields = ["materia"]


class LetraSeccionModelo:
    def get_seccion_letra(self, obj):
        if obj is not None:
            if hasattr(obj, "letra_seccion"):
                return obj.letra_seccion
            elif hasattr(obj, "seccion"):
                if (seccion := obj.seccion) is not None:
                    return seccion.letra_seccion

    get_seccion_letra.admin_order_field = "seccion"  # type: ignore
    get_seccion_letra.short_description = "Sección"  # type: ignore


@admin.register(ProfesorMateria)
class ProfesorMateriaAdmin(LetraSeccionModelo, ModelAdmin):
    form = ProfesorMateriaAdminForm
    list_display = [
        "profesor",
        "materia",
        "seccion",
    ]
    list_filter = [
        "materia",
        AñosAPartirSeccionesFiltro,
        SeccionLetraFiltro,
    ]
    search_fields = ["profesor__nombres", "profesor__apellidos"]
    autocomplete_fields = ["profesor", "materia", "seccion"]

    def get_list_display(self, request: HttpRequest):
        filtros = request.GET
        columnas = [*super().get_list_display(request)]

        if "anio" in filtros and "seccion" in filtros:
            columnas.remove("seccion")

        if "materia__id__exact" in filtros:
            columnas.remove("materia")

        return columnas


@admin.register(Matricula)
class MatriculaAdmin(ModelAdmin):
    list_display = ["estudiante", "seccion", "fecha_matricula"]
    list_filter = [
        AñosAPartirSeccionesFiltro,
        SeccionLetraFiltro,
    ]
    search_fields = ["estudiante__nombres", "estudiante__apellidos"]
    autocomplete_fields = ["estudiante", "seccion"]
    ordering = ["-fecha_matricula"]
    readonly_fields = ["fecha_matricula"]

    def get_list_display(self, request: HttpRequest):
        columnas = [*super().get_list_display(request)]
        filtros = request.GET

        if "seccion" in filtros:
            columnas.remove("seccion")

        return columnas


class ProfesorPermissionMixin:
    @staticmethod
    def get_profesor_secciones(user):
        """Obtener secciones del profesor"""
        if hasattr(user, "profesor"):
            profesor = user.profesor
            secciones = ProfesorMateria.objects.filter(profesor=profesor).values_list(
                "seccion_id", flat=True
            )
            return secciones
        return []

    @staticmethod
    def get_profesor_materias(user):
        """Obtener las materias del profesor"""
        if hasattr(user, "profesor"):
            profesor = user.profesor
            materias = ProfesorMateria.objects.filter(profesor=profesor).values_list(
                "materia_id", flat=True
            )
            return materias
        return []

    # solo obtener los datos de las notas del profesor según lo que imparte en el lapso actual
    def limitar_queryset_profesor(self, request, queryset):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            ultimo_lapso = Lapso.objects.last()
            materias = self.get_profesor_materias(request.user)
            secciones = self.get_profesor_secciones(request.user)

            return queryset.filter(
                materia_id__in=materias,
                seccion_id__in=secciones,
                lapso__id=ultimo_lapso.id,  # type: ignore
            )
        return queryset

    def profesor_tiene_acceso(self, user, obj):
        """Verificar si el profesor tiene acceso a las materias y secciones del objeto, y si es el lapso actual"""
        if hasattr(user, "profesor") and not user.is_superuser:
            lapso_actual = Lapso.objects.last()
            if obj.lapso_id != lapso_actual.id:  # type: ignore
                return False

            materias = self.get_profesor_materias(user)
            secciones = self.get_profesor_secciones(user)

            return obj.materia_id in materias and obj.seccion_id in secciones
        return True


@admin.register(Nota)
class NotaAdmin(ProfesorPermissionMixin, ModelAdmin):
    form = NotaAdminForm
    list_display = [
        "estudiante",
        "materia",
        "seccion",
        "valor_nota",
        "fecha_nota",
    ]
    list_filter = [NotaLapsoFiltro, "materia", NotaSeccionFiltro]
    search_fields = [
        "estudiante__nombres",
        "estudiante__apellidos",
        "materia__nombre_materia",
    ]
    autocomplete_fields = ["estudiante", "seccion", "materia"]
    list_editable = ["valor_nota"]
    readonly_fields = ["fecha_nota"]
    ordering = ["-fecha_nota"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return self.limitar_queryset_profesor(request, qs)

    def get_form(self, request, obj=None, *args, **kwargs):
        form = super().get_form(request, obj, *args, **kwargs)
        form.request = request  # type: ignore

        # Desactivar el campo lapso y dejar un valor estático, ya que no se pueden editar notas de un lapso anterior o al momento de crear, no puede ser diferente al actual
        form.base_fields["lapso"].disabled = True  # type: ignore
        if not obj:
            form.base_fields["lapso"].initial = Lapso.objects.last()  # type: ignore

        return form

    def get_list_display(self, request: HttpRequest):
        columnas = [*super().get_list_display(request)]
        filtros = request.GET

        if "materia__id__exact" in filtros:
            columnas.remove("materia")

        if "seccion" in filtros:
            columnas.remove("seccion")

        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            return columnas

        if "lapso" not in filtros:
            return columnas + ["lapso"]

        return columnas

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "materia":
            kwargs["queryset"] = Materia.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or hasattr(request.user, "profesor")

    def has_add_permission(self, request):
        return request.user.is_superuser or hasattr(request.user, "profesor")

    def has_change_permission(self, request, obj=None):
        if not (request.user.is_superuser or hasattr(request.user, "profesor")):
            return False

        if obj:
            return self.profesor_tiene_acceso(request.user, obj)

        return True

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            # no se pueden alterar notas de otro profesor o de un lapso anterior
            if not self.profesor_tiene_acceso(request.user, obj):
                raise PermissionDenied(
                    "No tiene permisos para modificar esta calificación"
                )

        super().save_model(request, obj, form, change)
