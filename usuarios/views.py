from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import Usuario
from django.db import connection

from django.http import HttpRequest, HttpResponse
import json

from usuarios.forms import FormularioPerfil


def login(request: HttpRequest):
    if not request.user.is_authenticated:  # type: ignore
        return LoginView.as_view(
            template_name="login.html",
        )(request)
    else:
        return redirect("/")


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
    )(request)


@login_required
def perfil(request: HttpRequest):
    if request.method == "DELETE":
        try:
            request.user.foto_perfil.delete(save=False)  # type: ignore
            request.user.miniatura_foto.delete(save=False)  # type: ignore

            # eliminar las urls de la base de datos, ya que por alguna razón no se borran al eliminar los archivos (¿A quién se le ocurre? >:( )
            with connection.cursor() as cursor:
                tabla_nombre = Usuario._meta.db_table  # type: ignore
                foto_col_nombre = Usuario._meta.get_field("foto_perfil").column  # type: ignore
                miniatura_col_nombre = Usuario._meta.get_field("miniatura_foto").column  # type: ignore

                cursor.execute(
                    f"UPDATE {tabla_nombre} SET {foto_col_nombre} = NULL, {miniatura_col_nombre} = NULL WHERE id = %s",  # type: ignore
                    [request.user.id],  # type: ignore
                )

                if cursor.rowcount < 1:
                    print("No se pudo dejar en blanco los campos de las fotos")

            messages.success(request, "Foto eliminada")
            return render(request, "perfil/index.html#foto_eliminada")
        except Exception as e:
            print("Error al eliminar la foto", e)
            return HttpResponse("Error al eliminar la foto: ", status=204)  # type: ignore
    else:
        form = FormularioPerfil(instance=request.user)  # type: ignore
        # se guardan los datos iniciales, para evitar que usar los que se intentaron cambiar al fallar la validación
        datos_iniciales = json.dumps(
            {
                **form.initial,
                "foto_perfil": request.user.foto_perfil.url  # type: ignore
                if request.user.foto_perfil  # type: ignore
                else "",
            }
        )

        if request.method == "POST":
            form = FormularioPerfil(request.POST, request.FILES, instance=request.user)  # type: ignore

            if form.is_valid():
                form.save()

        return render(
            request,
            "perfil/index.html",
            {
                "form": form,
                "datos_iniciales": datos_iniciales,
            },
        )


@login_required
def cambiar_contraseña(request: HttpRequest):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)  # type: ignore
        if form.is_valid():
            user = form.save()
            # actualizar la sesión
            update_session_auth_hash(request, user)
            return redirect("perfil")
    else:
        form = PasswordChangeForm(request.user)  # type: ignore

    return PasswordChangeView.as_view(
        template_name="cambiar-contraseña.html",
    )(request)
