from django.urls import path
from app.vistas import crear_crud_urls
from .models import Usuario, Grupo
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
    *crear_crud_urls(
        Usuario,
        views.ListaUsuarios,
        views.CrearUsuario,
        views.EditarUsuario,
    ),
    *crear_crud_urls(Grupo, views.ListaGrupos, views.CrearGrupo, views.EditarGrupo),
]
