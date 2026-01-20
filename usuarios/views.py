from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelMultipleChoiceField
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django_group_model.models import Permission
from app.vistas import VistaActualizarObjeto, VistaCrearObjeto, VistaListaObjetos
from .models import Usuario, Grupo
from django.db import connection
from django.urls import reverse_lazy

from django.http import HttpRequest, HttpResponse
import json

from usuarios.forms import FormGrupo, FormularioPerfil


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


class ListaGrupos(VistaListaObjetos):
    model = Grupo
    template_name = "grupos/index.html"
    plantilla_lista = "grupos/lista.html"
    nombre_url_editar = "editar_grupo"

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        return super().get_queryset(Grupo.objects.all().order_by("name"))


def cambiar_lista_permisos(contexto: dict):
    return contexto


class VistaGrupoForm:
    request: HttpRequest

    def get_context_data(self, **kwargs):
        """Agrupar los permisos por sus modelos y así reducir la cantidad de texto que se muestra para cada uno"""
        ctx = super().get_context_data(**kwargs)  # type: ignore

        if self.request.method == "GET":
            permisos: ModelMultipleChoiceField = ctx["form"].fields["permissions"]

            # Se deben evitar algunos modelos de Django, ya que son parte del funcionamiento interno del sistema
            nombres_modelos_no_necesarios = (
                m._meta.model_name
                for m in (LogEntry, Permission, ContentType, Session, Group)
            )

            permisos.queryset = permisos.queryset.exclude(  # type: ignore
                content_type__model__in=nombres_modelos_no_necesarios
            )

            permisos_agrupados = {}

            for permiso in permisos.queryset:
                grupo_label = (
                    permiso.content_type.model_class()._meta.verbose_name_plural
                )

                if grupo_label not in permisos_agrupados:
                    permisos_agrupados[grupo_label] = []

                permisos_agrupados[grupo_label].append(
                    {"id": str(permiso.id), "label": self.traducir_permiso(permiso)}
                )

            ctx["permisos_agrupados"] = [
                {"label": p[0], "opciones": p[1]} for p in permisos_agrupados.items()
            ]

        return ctx

    def traducir_permiso(self, permiso: Permission):
        codename = permiso.codename
        empieza_con = codename.split("_")[0]

        if empieza_con == "change":
            return "modificar"
        elif empieza_con == "delete":
            return "eliminar"
        elif empieza_con == "view":
            return "ver"
        elif empieza_con == "add":
            return "agregar"
        else:
            return permiso.name


class CrearGrupo(VistaGrupoForm, VistaCrearObjeto):
    model = Grupo
    template_name = "grupos/form.html"
    form_class = FormGrupo
    success_url = reverse_lazy("grupos")


class EditarGrupo(VistaGrupoForm, VistaActualizarObjeto):
    model = Grupo
    template_name = "grupos/form.html"
    form_class = FormGrupo
    success_url = reverse_lazy("grupos")
