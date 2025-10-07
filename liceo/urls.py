from django.urls import path
from . import views

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
    path("cambiar-contraseña/", views.cambiar_contraseña, name="password_change"),
    path(
        "contraseña-cambiada/",
        views.contraseña_cambiada,
        name="contraseña-cambiada",
    )
]
