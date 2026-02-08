from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.functions.datetime import TruncMinute
from django.forms import ModelMultipleChoiceField
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.views.generic import UpdateView
from django_group_model.models import Permission
from app.util import obtener_filtro_bool_o_nulo
from app.vistas import VistaActualizarObjeto, VistaCrearObjeto, VistaListaObjetos
from usuarios.forms.auth import CambiarContraseñaForm
from usuarios.forms.busqueda import UsuarioBusquedaForm
from usuarios.models import Usuario, Grupo
from usuarios.forms import (
    FormGrupo,
    FormUsuario,
)
from django.http import HttpRequest
from usuarios.forms import FormularioDatosUsuario
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def config_perfil(request: HttpRequest):
    if request.method == "GET":
        return render(
            request,
            "perfil/index.html",
            {
                "forms": {
                    "datos": FormularioDatosUsuario(instance=request.user),
                    "contraseña": CambiarContraseñaForm(user=request.user),
                },
            },
        )
    else:
        return HttpResponse(status=405)


class VistaPestañaPerfil(LoginRequiredMixin):
    request: HttpRequest
    mensaje_exito: str

    def form_valid(self, form):
        super().form_valid(form)  # type: ignore
        messages.success(self.request, self.mensaje_exito)

        return render(
            self.request,
            self.template_name,  # type: ignore
            {"form": form, "datos_cambiados": True},
        )


class DatosPerfil(LoginRequiredMixin, UpdateView):
    form_class = FormularioDatosUsuario
    model = Usuario
    template_name = "perfil/index.html#datos"
    success_url = "perfil"
    mensaje_exito = "Datos actualizados correctamente"

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, *args, **kwargs):
        request = self.request
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
            return render(request, "componentes/mensajes.html#como_respuesta")
        except Exception as e:
            print("Error al eliminar la foto", e)
            return HttpResponse("Error al eliminar la foto: ", status=204)  # type: ignore


class CambiarContraseña(VistaPestañaPerfil, PasswordChangeView):
    form_class = CambiarContraseñaForm
    success_url = "perfil"
    template_name = "perfil/index.html#contraseña"
    mensaje_exito = "Contraseña cambiada correctamente"


class ListaUsuarios(VistaListaObjetos):
    model = Usuario
    template_name = "usuarios/index.html"
    plantilla_lista = "usuarios/lista.html"
    nombre_url_editar = "editar_usuario"
    form_filtros = UsuarioBusquedaForm  # type: ignore
    paginate_by = 4
    columnas_totales = (
        {"titulo": "Nombre", "clave": "username"},
        {"titulo": "Correo", "clave": "email"},
        {"titulo": "Estado", "clave": "is_active", "alinear": "centro"},
        {"titulo": "Grupos", "clave": "grupos"},
        {"titulo": "último inicio de sesión", "clave": "last_login"},
        {"titulo": "Fecha de añadido", "clave": "fecha_añadido", "anotada": True},
    )
    tabla = False

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        q = (
            Usuario.objects.prefetch_related("grupos")
            .annotate(fecha_añadido=TruncMinute("date_joined"))
            .only(
                "id",
                "foto_perfil",
                "miniatura_foto",
                *(
                    col["clave"]
                    for col in self.columnas_totales
                    if not col.get("anotada", False)
                ),
            )
            .filter(is_superuser=False)
        )
        return super().get_queryset(q)

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if grupos := datos_form.get(UsuarioBusquedaForm.Campos.GRUPOS):
            queryset = queryset.filter(grupos__in=grupos)

        if (
            tiene_email := obtener_filtro_bool_o_nulo(
                UsuarioBusquedaForm.Campos.TIENE_EMAIL, datos_form
            )
        ) is not None:
            valor_filtro = Q(email="")

            if tiene_email:
                queryset = queryset.exclude(valor_filtro)
            else:
                queryset = queryset.filter(valor_filtro)

        if (
            activo := obtener_filtro_bool_o_nulo(
                UsuarioBusquedaForm.Campos.ACTIVO, datos_form
            )
        ) is not None:
            queryset = queryset.filter(is_active=True if activo else False)

        return queryset

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["media_url"] = settings.MEDIA_URL
        return ctx


class VistaGrupoForm:
    request: HttpRequest
    nombre_campo_permisos = "permissions"

    def get_context_data(self, **kwargs):
        """Agrupar los permisos por sus modelos y así reducir la cantidad de texto que se muestra para cada uno"""
        ctx = super().get_context_data(**kwargs)  # type: ignore

        if self.request.method == "GET":
            permisos: ModelMultipleChoiceField = ctx["form"].fields[
                self.nombre_campo_permisos
            ]

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


class CrearUsuario(VistaGrupoForm, VistaCrearObjeto):
    template_name = "usuarios/form.html"
    form_class = FormUsuario
    model = Usuario
    nombre_campo_permisos = "user_permissions"


class EditarUsuario(VistaGrupoForm, VistaActualizarObjeto):
    template_name = "usuarios/form.html"
    form_class = FormUsuario
    model = Usuario
    nombre_campo_permisos = "user_permissions"


class ListaGrupos(VistaListaObjetos):
    model = Grupo
    template_name = "grupos/index.html"
    plantilla_lista = "grupos/lista.html"
    nombre_url_editar = "editar_grupo"

    def get_queryset(self, *args, **kwargs) -> "list[dict]":
        return super().get_queryset(Grupo.objects.all().order_by("name"))


class CrearGrupo(VistaGrupoForm, VistaCrearObjeto):
    model = Grupo
    template_name = "grupos/form.html"
    form_class = FormGrupo


class EditarGrupo(VistaGrupoForm, VistaActualizarObjeto):
    model = Grupo
    template_name = "grupos/form.html"
    form_class = FormGrupo
