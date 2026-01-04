from django.contrib import admin
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from estudios.admin_filtros import (
    NotaLapsoFiltro,
    NotaSeccionFiltro,
    NotaMateriaFiltro,
    SeccionLetraFiltro,
    AñoNombreCortoFiltro,
    NotaAñoNombreCortoFiltro,
)
from estudios.admin_forms import (
    BachillerAdminForm,
    MatriculaAdminForm,
    LapsoAdminForm,
    NotaAdminForm,
    ProfesorMateriaAdminForm,
)
from .models import (
    Bachiller,
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
    list_display = ["nombre", "nombre_corto", "fecha_creacion"]
    search_fields = ["nombre"]
    readonly_fields = ["fecha_creacion"]


@admin.register(Seccion)
class SeccionAdmin(ModelAdmin):
    list_display = [
        "nombre",
        "letra",
        "vocero",
        "capacidad",
    ]
    list_filter = ["año", "letra"]
    search_fields = ["nombre", "letra"]
    autocomplete_fields = ["vocero"]
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
            and not request.user.is_superuser
        ):
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
    ]
    search_fields = ["nombres", "apellidos"]

    def get_search_results(self, request: HttpRequest, queryset, search_term: str):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        modelo = request.GET.get("model_name")

        # evitar mostrar alumnos ya matriculados
        if modelo == "matricula":
            lapso_actual = Lapso.objects.last()
            matriculados = Matricula.objects.filter(lapso=lapso_actual).values_list(
                "estudiante__cedula", flat=True
            )

            queryset = queryset.exclude(cedula__in=matriculados)
        # evitar mostrar alumnos ya bachilleres
        elif modelo == "bachiller":
            queryset = queryset.exclude(
                cedula__in=Bachiller.objects.values_list(
                    "estudiante__cedula", flat=True
                )
            )

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


class LetraSeccionModelo:
    def get_seccion_letra(self, obj):
        if obj is not None:
            if hasattr(obj, "letra"):
                return obj.letra
            elif hasattr(obj, "seccion"):
                if (seccion := obj.seccion) is not None:
                    return seccion.letra

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
    list_filter = ["materia", AñoNombreCortoFiltro, SeccionLetraFiltro]
    search_fields = ["profesor__nombres", "profesor__apellidos"]
    autocomplete_fields = ["profesor", "materia", "seccion"]

    def get_list_display(self, request: HttpRequest):
        filtros = request.GET
        columnas = [*super().get_list_display(request)]

        if "anio" in filtros and "seccion" in filtros:
            columnas.remove("seccion")

        if "materia__id__exact" in filtros:
            columnas.remove("materia")

        if "anio" in filtros and "letra" in filtros:
            columnas.remove("seccion")

        return columnas


@admin.register(Matricula)
class MatriculaAdmin(ModelAdmin):
    form = MatriculaAdminForm
    list_display = ["estudiante", "seccion", "fecha_añadida", "estado", "lapso"]
    list_filter = [AñoNombreCortoFiltro, SeccionLetraFiltro, "lapso"]
    search_fields = ["estudiante__nombres", "estudiante__apellidos"]
    autocomplete_fields = ["estudiante", "seccion"]
    ordering = ["-fecha_añadida"]

    def get_form(self, request, obj=None, *args, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Desactivar el campo lapso y dejar un valor estático, ya que no se matricular a un lapso diferente al actual
        form.base_fields["lapso"].disabled = True  # type: ignore
        if not obj:
            valor_lapso = form.base_fields["lapso"].initial  # pyright: ignore[reportAttributeAccessIssue]
            if valor_lapso is None:
                form.base_fields["lapso"].initial = Lapso.objects.last()  # pyright: ignore[reportAttributeAccessIssue]

        return form

    def get_list_display(self, request: HttpRequest):
        columnas = [*super().get_list_display(request)]
        filtros = request.GET

        if "anio" in filtros and "letra" in filtros:
            columnas.remove("seccion")

        return columnas

    # Si están pidiendo autocompletado desde el formulario de NotaAdmin, alterar los resultados para solo mostrar los estudiantes de las secciones del profesor
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        modelo = request.GET.get("model_name")

        # Si es profesor, limitar a lo ya mencionado
        if (
            modelo == "nota"
            and hasattr(request.user, "profesor")
            and not request.user.is_superuser
        ):
            profesor = request.user.profesor  # pyright: ignore[reportAttributeAccessIssue]
            secciones_profesor = ProfesorMateria.objects.filter(
                profesor=profesor
            ).values_list("seccion_id", flat=True)
            lapso_actual = Lapso.objects.last()

            queryset = queryset.filter(
                estado="activo",
                lapso=lapso_actual,
                seccion_id__in=secciones_profesor,
            ).distinct()

        return queryset, use_distinct


class MixinNotaPermisos:
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
    def get_profesor_materias(user) -> "list[int]":
        """Obtener las materias del profesor"""
        if hasattr(user, "profesor"):
            profesor = user.profesor
            materias = ProfesorMateria.objects.filter(profesor=profesor).values_list(
                "materia_id", flat=True
            )
            return materias  # pyright: ignore[reportReturnType]
        return []

    # solo obtener los datos de las notas del profesor según lo que imparte en el lapso actual
    def limitar_queryset_profesor(self, request, queryset):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            ultimo_lapso = Lapso.objects.last()
            materias = self.get_profesor_materias(request.user)
            secciones = self.get_profesor_secciones(request.user)

            return queryset.filter(
                materia_id__in=materias,
                matricula__seccion_id__in=secciones,
                matricula__lapso__id=ultimo_lapso.id,  # type: ignore
            )
        return queryset

    def profesor_tiene_acceso(self, user, obj: Nota):
        """Verificar si el profesor tiene acceso a las materias y secciones del objeto, y si es el lapso actual"""
        if hasattr(user, "profesor") and not user.is_superuser:
            lapso_actual = Lapso.objects.last()
            if lapso_actual is None:
                return False

            # nota no pertenece al lapso actual
            if obj.matricula.lapso.pk != lapso_actual.pk:
                return False

            materias = self.get_profesor_materias(user)
            secciones = self.get_profesor_secciones(user)

            # es del lapso actual, pero la materia y seccion debe pertenecer a las materias y secciones del profesor
            return obj.materia.pk in materias and obj.matricula.seccion.pk in secciones
        return True


@admin.register(Nota)
class NotaAdmin(MixinNotaPermisos, ModelAdmin):
    form = NotaAdminForm
    list_display = [
        "estudiante",
        "seccion",
        "materia",
        "valor",
        "fecha",
    ]
    list_filter = [
        NotaLapsoFiltro,
        NotaMateriaFiltro,
        NotaAñoNombreCortoFiltro,
        NotaSeccionFiltro,
    ]
    search_fields = [
        "matricula__estudiante__nombres",
        "matricula__estudiante__apellidos",
    ]
    autocomplete_fields = ["matricula", "materia"]
    list_editable = ["valor"]
    readonly_fields = ["fecha"]
    ordering = ["-fecha"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return self.limitar_queryset_profesor(request, qs)

    def get_form(self, request, obj=None, *args, **kwargs):
        form = super().get_form(request, obj, *args, **kwargs)
        form.request = request  # type: ignore

        return form

    def get_list_display(self, request: HttpRequest):
        columnas = [*super().get_list_display(request)]
        filtros = request.GET

        if "materia__id__exact" in filtros:
            columnas.remove("materia")

        if "anio" in filtros and "letra" in filtros:
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

    def has_add_permission(self, request):
        return request.user.is_superuser or hasattr(request.user, "profesor")

    def has_change_permission(self, request, obj=None):
        if not (request.user.is_superuser or hasattr(request.user, "profesor")):
            return False

        # se verifica el permiso para cada nota individual
        if obj:
            return self.profesor_tiene_acceso(request.user, obj)

        return True

    def has_delete_permission(self, request, obj=None):
        # al eliminar matriculas y tratarse de un admin se debe hacer una excepción, ya que esto requiere eliminar notas, y por defecto solo los profesores pueden hacerlo
        if (
            request.method == "POST"
            and request.path.endswith("/matricula/")
            and (
                request.user.is_superuser
                or request.user.groups.filter(name="Admin").exists()
            )
        ):
            return True

        return self.has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if hasattr(request.user, "profesor") and not request.user.is_superuser:
            # no se pueden alterar notas de otro profesor o de un lapso anterior
            if not self.profesor_tiene_acceso(request.user, obj):  # pyright: ignore[reportArgumentType]
                raise PermissionDenied(
                    "No tiene permisos para modificar esta calificación"
                )

        super().save_model(request, obj, form, change)


@admin.register(Bachiller)
class BachillerAdmin(ModelAdmin):
    form = BachillerAdminForm
    list_display = ["estudiante", "promocion", "fecha_graduacion"]
    autocomplete_fields = ["estudiante"]
