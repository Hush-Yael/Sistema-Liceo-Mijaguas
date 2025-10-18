from django.contrib import admin
from unfold.admin import ModelAdmin

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
        "año",
        "letra_seccion",
        "tutor",
        "capacidad_maxima",
    ]
    list_filter = ["año", "letra_seccion"]
    search_fields = ["nombre_seccion", "letra_seccion"]
    autocomplete_fields = ["tutor"]
    readonly_fields = ["fecha_creacion"]

    # Alterar los resultados del autocompletado
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


@admin.register(Materia)
class MateriaAdmin(ModelAdmin):
    list_display = ["nombre_materia", "fecha_creacion"]
    search_fields = ["nombre_materia"]
    readonly_fields = ["fecha_creacion"]

    # Alterar los resultados del autocompletado
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

    # Alterar los resultados del autocompletado
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
        "año",
        "get_seccion_letra",
        "es_profesor_principal",
    ]
    list_filter = ["año", "es_profesor_principal", "seccion"]
    search_fields = ["profesor__nombre", "materia__nombre_materia"]
    autocomplete_fields = ["profesor", "materia", "año", "seccion"]
    list_editable = ["es_profesor_principal"]

    def get_seccion_letra(self, obj):
        letra = super().get_seccion_letra(obj)

        if letra is None:
            return "todas"

        return letra

    get_seccion_letra.admin_order_field = "seccion"  # type: ignore
    get_seccion_letra.short_description = "Sección"  # type: ignore


@admin.register(Matricula)
class MatriculaAdmin(LetraSeccionModelo, ModelAdmin):
    list_display = ["estudiante", "año", "get_seccion_letra", "fecha_matricula"]
    list_filter = [
        "año",
        "seccion",
    ]
    search_fields = ["estudiante__nombre", "estudiante__apellido"]
    autocomplete_fields = ["estudiante", "seccion"]
    ordering = ["-fecha_matricula"]


class ProfesorPermissionMixin:
    def get_profesor_materias_secciones(self, user):
        """Obtener las materias y secciones del profesor"""
        if hasattr(user, "profesor"):
            profesor = user.profesor
            materias = ProfesorMateria.objects.filter(profesor=profesor).values_list(
                "materia_id", flat=True
            )
            secciones = ProfesorMateria.objects.filter(profesor=profesor).values_list(
                "seccion_id", flat=True
            )
            return materias, secciones
        return [], []

    # solo obtener los datos de las notas del profesor según lo que imparte en el lapso actual
    def limitar_queryset_profesor(self, request, queryset):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            ultimo_lapso = Lapso.objects.last()
            materias, secciones = self.get_profesor_materias_secciones(request.user)

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

            materias, secciones = self.get_profesor_materias_secciones(user)
            return obj.materia_id in materias and obj.seccion_id in secciones
        return True


@admin.register(Nota)
class NotaAdmin(ProfesorPermissionMixin, LetraSeccionModelo, ModelAdmin):
    form = NotaAdminForm
    list_display = [
        "estudiante",
        "materia",
        "lapso",
        "get_seccion_letra",
        "valor_nota",
        "fecha_nota",
    ]
    list_filter = ["lapso", "materia", "seccion"]
    search_fields = [
        "estudiante__nombre",
        "estudiante__apellido",
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
