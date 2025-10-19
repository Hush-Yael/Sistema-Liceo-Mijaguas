from django.contrib import admin
from estudios.models import Seccion


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
