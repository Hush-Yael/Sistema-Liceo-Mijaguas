from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("usuarios.urls")),
]

admin.site.site_title = "Liceo Mijaguas"
admin.site.site_header = "Panel de administración - Liceo Mijaguas"
admin.site.index_title = "Administración del sistema"
