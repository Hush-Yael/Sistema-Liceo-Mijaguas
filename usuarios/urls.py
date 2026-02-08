from django.urls import path
from app.vistas import crear_crud_urls
from .models import Usuario, Grupo
import usuarios.vistas as vistas
import usuarios.vistas.auth as vistas_auth


urlpatterns = [
    path(
        "login/",
        vistas_auth.Login.as_view(),
        name="login",
    ),
    path(
        "cerrar-sesion/",
        vistas_auth.cerrar_sesion,
        name="logout",
    ),
    path(
        "perfil",
        vistas.config_perfil,
        name="perfil",
    ),
    path(
        "cambiar-contraseña",
        vistas.CambiarContraseña.as_view(),
        name="cambiar_contraseña",
    ),
    path(
        "cambiar-datos",
        vistas.DatosPerfil.as_view(),
        name="cambiar_datos",
    ),
    path(
        "recuperar-contraseña",
        vistas_auth.RecuperarContraseña.as_view(),
        name="recuperar_contraseña",
    ),
    path(
        "correo-recuperacion-enviado",
        vistas_auth.CorreoRecuperacionEnviado.as_view(),
        name="correo_recuperacion_enviado",
    ),
    path(
        "restablecer-contraseña/<uidb64>/<token>/",
        vistas_auth.RestablecerContraseña.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "contraseña-restablecida/",
        vistas_auth.ContraseñaRestablecida.as_view(),
        name="password_reset_complete",
    ),
    *crear_crud_urls(
        Usuario,
        vistas.ListaUsuarios,
        vistas.CrearUsuario,
        vistas.EditarUsuario,
    ),
    *crear_crud_urls(Grupo, vistas.ListaGrupos, vistas.CrearGrupo, vistas.EditarGrupo),
]
