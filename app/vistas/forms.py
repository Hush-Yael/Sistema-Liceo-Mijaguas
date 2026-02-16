from typing import Type
from django import forms
from django.contrib import messages
from django.db import models
from django.http import (
    HttpResponse,
)
from django.urls import reverse
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, UpdateView
from app import HTTPResponseHXRedirect
from app.vistas import (
    Vista,
    nombre_url_lista_auto,
)


class VistaForm(SingleObjectTemplateResponseMixin, Vista):
    model: Type[models.Model]  # type: ignore
    tipo_accion_palabra: str
    invalido_url = "objeto-form.html#invalido"

    def __init__(self) -> None:
        super().__init__()

        self.permission_required = (
            f"{self.nombre_app_modelo}.add_{self.model._meta.model_name}"
        )

    def form_invalid(self, form: forms.ModelForm) -> HttpResponse:
        if not (errores_generales := form.non_field_errors()):
            messages.error(self.request, "Corrige los errores en el formulario")
        else:
            for error in errores_generales:
                messages.error(self.request, error)  # type: ignore

        return super().form_invalid(form)  # type: ignore

    def render_to_response(self, context, **response_kwargs):
        r = super().render_to_response(context, **response_kwargs)

        if context["form"].errors:
            r.template_name = self.invalido_url  # type: ignore

        return r

    def form_valid(self, form: forms.ModelForm) -> HttpResponse:
        self.object = form.save()

        nombre_modelo: str = self.model._meta.verbose_name  # type: ignore - sí es una string

        messages.success(
            self.request,
            f"{nombre_modelo.capitalize()} {self.tipo_accion_palabra}{self.vocal_del_genero} correctamente",
        )

        # ya que la petición se hace por HTMX, se debe usar la clase que permite redireccionar con este
        return HTTPResponseHXRedirect(reverse(nombre_url_lista_auto(self.model)))  # type: ignore


class VistaCrearObjeto(VistaForm, CreateView):
    model: Type[models.Model]  # type: ignore
    tipo_permiso = "add"
    tipo_accion_palabra = "cread"


class VistaActualizarObjeto(VistaForm, UpdateView):
    model: Type[models.Model]  # type: ignore
    tipo_permiso = "change"
    tipo_accion_palabra = "editad"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["editando"] = 1
        return ctx
