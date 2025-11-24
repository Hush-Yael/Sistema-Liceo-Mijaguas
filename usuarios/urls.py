from django.urls import path
from . import views


urlpatterns = [
    path(
        "login/",
        views.login,
        name="login",
    ),
    path(
        "cerrar-sesion/",
        views.cerrar_sesion,
        name="logout",
    ),
    path(
        "perfil",
        views.perfil,
        name="perfil",
    ),
    path(
        "cambiar_contraseña",
        views.cambiar_contraseña,
        name="cambiar_contraseña",
    ),
]
