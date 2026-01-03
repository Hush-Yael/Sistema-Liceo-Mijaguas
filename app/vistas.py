from typing import Type
from django import forms
from django.contrib import messages
from django.db import models
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django.urls import path
from django.views.generic import ListView
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, UpdateView
from app import HTTPResponseHXRedirect
from django.contrib.auth.mixins import PermissionRequiredMixin


class Vista(PermissionRequiredMixin):
    tipo_permiso: str
    nombre_modelo: str
    nombre_app_modelo: str
    nombre_objeto: str
    nombre_objeto_plural: str
    model: Type[models.Model]

    def __init__(self):
        self.nombre_modelo = self.model._meta.model_name  # type: ignore
        self.nombre_app_modelo = self.model._meta.app_label
        self.nombre_objeto = self.model._meta.verbose_name  # type: ignore
        self.nombre_objeto_plural = self.model._meta.verbose_name_plural  # type: ignore

        self.permission_required = (
            f"{self.nombre_app_modelo}.{self.tipo_permiso}_{self.nombre_modelo}"
        )

        super().__init__()


class VistaListaObjetos(Vista, ListView):
    model: Type[models.Model]  # type: ignore
    tipo_permiso = "view"
    context_object_name = "lista_objetos"
    articulo_nombre_plural = "los"
    columnas: "list[dict[str, str]]"
    columnas_a_evitar: "list[str]" = []
    columnas_ocultables: "list[str]"

    def __init__(self):
        setattr(self, "nombre_modelo_plural", self.model._meta.verbose_name_plural)
        self.obtener_columnas()

        super().__init__()

    def obtener_columnas(self):
        columnas = filter(
            lambda col: col.name != "id" and col.name not in self.columnas_a_evitar,
            self.model._meta.fields,  # type: ignore
        )
        self.columnas = list(
            map(lambda x: {"clave": x.name, "titulo": x.verbose_name}, columnas)
        )

        self.columnas_ocultables = list(
            map(lambda col: col["titulo"], self.columnas[1:])
        )

    def get_queryset(self, queryset: models.QuerySet) -> "list[dict]":  # type: ignore
        if queryset:
            return list(queryset)
        else:
            return []

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()

        try:
            ctx["modelos_relacionados"] = list(
                map(
                    lambda obj: obj.related_model._meta.verbose_name_plural,
                    self.model._meta.related_objects,  # type: ignore
                )
            )
        except Exception:
            ctx["modelos_relacionados"] = []

        ctx["permisos"] = {
            "editar": self.request.user.has_perm(  # type: ignore
                f"{self.nombre_app_modelo}.edit_{self.nombre_modelo}"
            ),
            "crear": self.request.user.has_perm(  # type: ignore
                f"{self.nombre_app_modelo}.add_{self.nombre_modelo}"
            ),
            "eliminar": self.request.user.has_perm(  # type: ignore
                f"{self.nombre_app_modelo}.delete_{self.nombre_modelo}"
            ),
        }
        return ctx

    def delete(self, request, *args, **kwargs):
        if not self.request.user.has_perm(  # type: ignore
            f"{self.nombre_app_modelo}.delete_{self.nombre_modelo}"
        ):
            return HttpResponseForbidden(
                f"No tienes permisos para eliminar {self.model._meta.verbose_name_plural}"
            )

        ids = request.GET.getlist("ids")

        if not ids or not isinstance(ids, list):
            return HttpResponseBadRequest("No se indicó una lista de ids")

        eliminados, _ = self.model.objects.filter(id__in=ids).delete()  # type: ignore

        if eliminados > 0:
            messages.success(
                request,
                f"Se eliminaron {self.articulo_nombre_plural} {self.model._meta.verbose_name_plural} seleccionad{'as' if self.articulo_nombre_plural == 'las' else 'os'}",
            )
        else:
            messages.error(
                request,
                f"No se eliminaron {self.articulo_nombre_plural} {self.model._meta.verbose_name_plural} seleccionad{'as' if self.articulo_nombre_plural == 'las' else 'os'}",
            )

        self.object_list = self.get_queryset(queryset=self.queryset)  # type: ignore

        ctx = self.get_context_data(self, *args, **kwargs)
        ctx["tabla_reemplazada_por_htmx"] = 1

        return render(
            request,
            "lista-objetos.html#respuesta_cambios_tabla",
            ctx,
        )


class VistaForm(SingleObjectTemplateResponseMixin, Vista):
    model: Type[models.Model]  # type: ignore
    accion_tipo_msg: str

    def __init__(self) -> None:
        super().__init__()

        self.permission_required = (
            f"{self.nombre_app_modelo}.add_{self.model._meta.verbose_name}"
        )

    def form_invalid(self, form: forms.ModelForm) -> HttpResponse:
        messages.error(self.request, "Corrige los errores en el formulario")

        r = super().form_invalid(form)  # type: ignore

        if self.template_name:
            r.template_name = self.template_name + "#invalido"

        return r

    def form_valid(self, form: forms.ModelForm) -> HttpResponse:
        self.object = form.save()

        nombre_modelo: str = self.model._meta.verbose_name  # type: ignore

        vocal = "a" if nombre_modelo.endswith("a") else "o"
        messages.success(
            self.request, f"{nombre_modelo} {self.accion_tipo_msg}{vocal} correctamente"
        )

        # ya que la petición se hace por HTMX, se debe usar la clase que permite redireccionar con este
        return HTTPResponseHXRedirect(self.get_success_url())  # type: ignore


class VistaCrearObjeto(VistaForm, CreateView):
    model: Type[models.Model]  # type: ignore
    tipo_permiso = "add"
    accion_tipo_msg = "cread"


class VistaActualizarObjeto(VistaForm, UpdateView):
    model: Type[models.Model]  # type: ignore
    tipo_permiso = "edit"
    accion_tipo_msg = "editad"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["editando"] = 1
        return ctx


def crear_crud_urls(
    nombre_objeto: str,
    nombre_objeto_plural: str,
    vista_lista: Type[VistaListaObjetos],
    vista_crear: Type[VistaCrearObjeto],
    vista_actualizar: Type[VistaActualizarObjeto],
):
    return [
        path(
            nombre_objeto_plural + "/",
            vista_lista.as_view(),
            name=nombre_objeto_plural,
        ),
        path(
            f"{nombre_objeto_plural}/crear/",
            vista_crear.as_view(),
            name=f"crear_{nombre_objeto}",
        ),
        path(
            f"{nombre_objeto_plural}/editar/<int:pk>/",
            vista_actualizar.as_view(),
            name=f"editar_{nombre_objeto}",
        ),
    ]
