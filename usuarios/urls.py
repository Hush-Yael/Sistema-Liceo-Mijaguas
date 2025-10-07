from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", views.inicio, name="inicio"),
    path(
        "login/",
        views.login,
        name="login",
    ),
    path("registro/", views.registro, name="registro"),
    path(
        "cerrar-sesion/",
        views.cerrar_sesion,
        name="logout",
    ),
    path("cambiar-contraseña/", views.cambiar_contraseña, name="cambiar-contraseña"),
    path(
        "contraseña-cambiada/",
        views.contraseña_cambiada,
        name="contraseña-cambiada",
    ),
    path(
        "perfil",
        views.perfil,
        name="perfil",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
