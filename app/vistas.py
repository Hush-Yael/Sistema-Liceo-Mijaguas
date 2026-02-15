from typing import Literal, Mapping, Type, Any, TypedDict
from typing_extensions import NotRequired
from django import forms
from django.contrib import messages
from django.db import models
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    QueryDict,
)
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.views.generic import ListView, View
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, UpdateView
from app import HTTPResponseHXRedirect
from django.contrib.auth.mixins import PermissionRequiredMixin
from app.forms import BusquedaFormMixin, DireccionesOrden, OrdenFormMixin
from app.util import (
    nombre_url_crear_auto,
    nombre_url_editar_auto,
    nombre_url_lista_auto,
)


class Vista(PermissionRequiredMixin):
    """Vista básica para todas las vistas de la app. Se encarga de validar los permisos pertinentes al modelo de la vista y de obtener datos relacionados al nombre de sus objetos."""

    tipo_permiso: Literal["add", "change", "delete", "view"]
    nombre_modelo: str
    nombre_app_modelo: str
    nombre_objeto: str
    nombre_objeto_plural: str
    genero_sustantivo_objeto: "Literal['M', 'F']" = "M"
    articulo_sustantivo: str
    articulo_sustantivo_plural: str
    vocal_del_genero: Literal["a", "o"]
    model: Type[models.Model]

    def __init__(self):
        self.nombre_modelo = self.model._meta.model_name  # type: ignore
        self.nombre_app_modelo = self.model._meta.app_label
        self.nombre_objeto = self.model._meta.verbose_name  # type: ignore
        self.nombre_objeto_plural = self.model._meta.verbose_name_plural  # type: ignore

        genero = self.genero_sustantivo_objeto

        if genero == "M":
            self.articulo_sustantivo = "el"
            self.articulo_sustantivo_plural = "los"
            self.vocal_del_genero = "o"

        elif genero == "F":
            self.articulo_sustantivo = "la"
            self.articulo_sustantivo_plural = "las"
            self.vocal_del_genero = "a"

        self.permission_required = (
            f"{self.nombre_app_modelo}.{self.tipo_permiso}_{self.nombre_modelo}"
        )

        super().__init__()


class VistaParaNoLogueados(View):
    """Clase para vistas a las que solo deben acceder los usuarios que no han iniciado sesión"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("inicio")

        return super().dispatch(request, *args, **kwargs)


class Columna(TypedDict):
    clave: str
    titulo: str
    alinear: NotRequired[Literal["derecha", "centro"]]


class ColumnaFija(Columna):
    anotada: NotRequired[bool]


class VistaListaObjetos(Vista, ListView):
    model: Type[models.Model]  # type: ignore
    tipo_permiso = "view"
    context_object_name = "lista_objetos"
    columnas_totales: "tuple[ColumnaFija, ...]"
    columnas_mostradas: "list[Columna]"
    columnas_a_evitar: "set[str]"
    columnas_ocultables: "list[str]"
    form_filtros: BusquedaFormMixin
    total: "int | None" = None
    plantilla_lista: str
    id_lista_objetos: str = "lista-objetos"
    tabla: bool = True
    url_crear: str
    url_editar: str

    def __init__(self):
        setattr(self, "nombre_modelo_plural", self.model._meta.verbose_name_plural)

        if not hasattr(self, "columnas_mostradas") or not self.columnas_mostradas:
            self.establecer_columnas()

        if not hasattr(self, "url_crear"):
            self.url_crear = nombre_url_crear_auto(self.model)

        if not hasattr(self, "url_editar"):
            self.url_editar = nombre_url_editar_auto(self.model)

        super().__init__()

    def establecer_columnas(self):
        tiene_columnas_totales = (
            hasattr(self, "columnas_totales") and self.columnas_totales
        )
        tiene_columnas_a_evitar = hasattr(self, "columnas_a_evitar")

        if not tiene_columnas_totales:
            if tiene_columnas_a_evitar:
                self.columnas_mostradas = [  # type: ignore
                    {"clave": col.name, "titulo": col.verbose_name}
                    for col in self.model._meta.fields
                    if col.name != "id" and col.name not in self.columnas_a_evitar
                ]
            else:
                self.columnas_mostradas = [  # type: ignore
                    {"clave": col.name, "titulo": col.verbose_name}
                    for col in self.model._meta.fields
                    if col.name != "id"
                ]
        else:
            if tiene_columnas_a_evitar:
                self.columnas_mostradas = [
                    col
                    for col in self.columnas_totales
                    if col.get("clave") not in self.columnas_a_evitar
                ]
            else:
                if isinstance(self.columnas_totales, tuple):
                    self.columnas_mostradas = list(self.columnas_totales)
                else:
                    self.columnas_mostradas = self.columnas_totales

        self.establecer_columnas_ocultables()

    def establecer_columnas_ocultables(self):
        self.columnas_ocultables = list(
            map(lambda col: col["titulo"], self.columnas_mostradas[1:])
        )

    def get_queryset(self, queryset: models.QuerySet) -> "list[dict]":  # type: ignore
        """Transforma el queryset en una lista, ya que esto permite utilizar cierto filtros específicos en la plantilla. Si se indica un form de filtros, se modifican los datos de acuerdo a los filtros indicados en el form."""

        if queryset:
            # se indicó un form de filtros
            if hasattr(self, "form_filtros"):
                datos_form = self.establecer_form_filtros()

                if isinstance(self.form_filtros, OrdenFormMixin):
                    queryset = self.aplicar_orden(queryset, datos_form)  # type: ignore

                # modificar paginación de acuerdo a los filtros
                self.modificar_paginacion_por_filtro(datos_form)

                # modificar queryset de acuerdo a los filtros
                queryset = self.aplicar_filtros(
                    queryset=queryset,
                    datos_form=datos_form,
                )

            return list(queryset)
        else:
            return []

    def establecer_form_filtros(self):
        """Establece el form de filtros para esta vista y retorna los datos del form"""

        # al crear el form de filtros, se debe distinguir entre GET y los otros métodos, ya que por alguna razón GET no funciona correctamente (evita que se recuperen los datos de las cookies) si se le pasan los datos
        if self.request.method == "GET":
            self.form_filtros = self.form_filtros(request=self.request)  # type: ignore
        else:
            if self.request.method == "POST":
                datos = self.request.POST
            elif self.request.method == "PUT" and self.request.body:
                datos = QueryDict(self.request.body)  # type: ignore
            elif self.request.method == "DELETE":
                datos = self.request.GET
            elif getattr(self.form_filtros, "initial", None):
                datos = self.form_filtros.initial
            else:
                datos = {}

            self.form_filtros = self.form_filtros(  # type: ignore
                datos, request=self.request
            )

        if self.form_filtros.is_valid():
            return self.form_filtros.cleaned_data
        else:
            return self.form_filtros.initial

    def modificar_paginacion_por_filtro(
        self, datos_form: "dict[str, Any] | Mapping[str, Any]"
    ):
        # ya que la paginación se hace por post, se debe modificar el kwarg que se usa para ella
        if self.form_filtros.fields.get("pagina"):
            self.kwargs[self.page_kwarg] = int(
                datos_form.get(
                    "pagina",
                    "1",
                )
            )
        elif p := self.request.POST.get("page"):
            self.kwargs[self.page_kwarg] = int(p)

        if self.form_filtros.fields.get("cantidad_por_pagina"):
            try:
                cantidad_por_pagina = int(
                    datos_form.get(
                        "cantidad_por_pagina",
                        "0",
                    )
                )
            except (TypeError, ValueError):
                cantidad_por_pagina = 0

            if cantidad_por_pagina > 0:
                self.paginate_by = cantidad_por_pagina

    def aplicar_filtros(
        self,
        queryset: models.QuerySet,
        datos_form: "dict[str, Any] | Mapping[str, Any]",
    ):
        """Modifica el queryset de acuerdo a los filtros indicados en el form de filtros"""
        if isinstance(self.form_filtros, BusquedaFormMixin):
            for campo in self.form_filtros:
                if not hasattr(campo.field, "nombre_columna_db"):
                    continue

                nombre_columna_db: "str | None" = getattr(
                    campo.field, "nombre_columna_db"
                )

                if not nombre_columna_db:
                    continue

                q: "str | None" = datos_form.get(campo.name)

                if not q:
                    continue

                tipo_q = datos_form.get(f"tipo_{campo.name}")

                if not tipo_q:
                    tipo_q = "icontains"

                if not isinstance(q, str):
                    continue

                q = q.strip()
                if q == "":
                    continue

                return queryset.filter(**{f"{nombre_columna_db}__{tipo_q}": q})

        return queryset

    def aplicar_orden(self, queryset: models.QuerySet, datos_form: "dict[str, Any]"):
        for nombre, _ in self.form_filtros.campos_orden:  # type: ignore
            if direccion := datos_form.get(nombre):
                columna = nombre.split("-")[0]

                if direccion == DireccionesOrden.ASC.value[0]:
                    columna = "-" + columna

                queryset = queryset.order_by(columna)

        return queryset

    def alternar_col_por_filtro(self, valor_filtro: "Any | None", columna: str):
        if valor_filtro:
            # no se deben ocultar columnas con un queryset de más de un elemento, pues esto evitaría distinguir entre objetos
            if (
                isinstance(valor_filtro, models.QuerySet)
                or isinstance(valor_filtro, list)
            ) and len(valor_filtro) != 1:
                return self.columnas_a_evitar.discard(columna)

            self.columnas_a_evitar.add(columna)
        else:
            self.columnas_a_evitar.discard(columna)

    def obtener_y_alternar(
        self,
        nombre_campo: str,
        datos_form: "dict[str, Any] | Mapping[str, Any]",
        nombre_columna: str,
    ):
        dato = datos_form.get(nombre_campo)
        self.alternar_col_por_filtro(dato, nombre_columna)
        return dato

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        try:
            ctx["modelos_relacionados"] = list(
                map(
                    lambda obj: obj.related_model._meta.verbose_name_plural,
                    self.model._meta.related_objects,  # type: ignore
                )
            )
        except Exception:
            ctx["modelos_relacionados"] = []

        ctx.update(
            {
                "form_filtros": self.form_filtros
                if hasattr(self, "form_filtros")
                else None,
                "form_con_orden": True
                if hasattr(self, "form_filtros")
                and isinstance(self.form_filtros, OrdenFormMixin)
                else False,
                "permisos": {
                    "editar": self.request.user.has_perm(  # type: ignore
                        f"{self.nombre_app_modelo}.change_{self.nombre_modelo}"
                    ),
                    "crear": self.request.user.has_perm(  # type: ignore
                        f"{self.nombre_app_modelo}.add_{self.nombre_modelo}"
                    ),
                    "eliminar": self.request.user.has_perm(  # type: ignore
                        f"{self.nombre_app_modelo}.delete_{self.nombre_modelo}"
                    ),
                },
                "no_hay_objetos": self.total == 0
                if self.total is not None
                else not self.model.objects.exists(),
            }
        )

        return ctx

    def get(self, request: HttpRequest, *args, **kwargs):
        respuesta = super().get(request, *args, **kwargs)

        # cambio de página
        if self.paginate_by is not None and request.GET.get("solo_tabla"):
            respuesta.context_data["lista_reemplazada_por_htmx"] = 1  # type: ignore
            respuesta.template_name = self.plantilla_lista  # type: ignore
        elif self.paginate_by:
            self.total = self.model.objects.count()

        return respuesta

    # aplicación de filtros por POST
    def post(self, request: HttpRequest, *args, **kwargs):
        if hasattr(self, "form_filtros"):
            respuesta = super().get(request, *args, **kwargs)

            respuesta.context_data["lista_reemplazada_por_htmx"] = 1  # type: ignore
            respuesta.template_name = self.plantilla_lista  # type: ignore

            return respuesta

        return HttpResponse("No se indicó un form de filtros", status=405)

    def put(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Actualizar un registro con PUT. Por defecto, si no tiene permisos, devuelve un HttpResponseForbidden. Si tiene permisos, obtiene una tupla con (los datos, los ids) de la petición. Debe implementarse la funcionalidad en la clase que hereda."""

        if not request.user.has_perm(  # type: ignore - sí se puede verificar el permiso al usuario
            f"{self.nombre_app_modelo}.change_{self.nombre_modelo}"
        ):
            return HttpResponseForbidden(
                f"No tienes permisos para editar {self.nombre_objeto_plural}"
            )

        datos = QueryDict(request.body)  # type: ignore - sí se obtienen los datos

        if not (ids := datos.getlist(self.ids_objetos_kwarg)):
            return HttpResponseBadRequest(
                f"No se indicó una lista de {self.ids_objetos_kwarg}"
            )

        respuesta = self.actualizar(request, ids, datos, *args, **kwargs)

        if isinstance(respuesta, HttpResponse):
            return respuesta

        return self.actualizar_lista(request, *args, **kwargs)

    def actualizar(
        self, request: HttpRequest, ids: "list[str]", datos: QueryDict, *args, **kwargs
    ) -> "HttpResponse | None":
        """Se usa para implementar la funcionalidad del método PUT en la clase que hereda"""
        raise NotImplementedError(
            "El metodo 'actualizar' debe ser implementado en la clase que hereda"
        )

    def delete(self, request: HttpRequest, *args, **kwargs):
        if not request.user.has_perm(  # type: ignore
            f"{self.nombre_app_modelo}.delete_{self.nombre_modelo}"
        ):
            return HttpResponseForbidden(
                f"No tienes permisos para eliminar {self.nombre_objeto_plural}"
            )

        ids = request.GET.getlist("ids")

        if not ids or not isinstance(ids, list):
            return HttpResponseBadRequest(
                "No se indicó una lista de ids"
            )

        respuesta = self.eliminar(request, ids)

        if isinstance(respuesta, HttpResponse):
            return respuesta

        cantidad_eliminados, ids_eliminados = respuesta

        self.mensaje_luego_eliminar(request, cantidad_eliminados, ids_eliminados)

        return self.actualizar_lista(
            request,
        )

    def eliminar(
        self, request: HttpRequest, ids: "list[str]"
    ) -> "HttpResponse | tuple[int, dict[str, int]]":
        """Se usa para implementar la funcionalidad del método DELETE en la clase que hereda. Por defecto, se eliminan los objetos del modelo indicado con los ids indicados. Necesita retornar la cantidad de registros eliminados y la lista de ids eliminados para indicarlo al usuario en el mensaje"""

        return self.model.objects.filter(id__in=ids).delete()

    def actualizar_lista(
        self,
        request: HttpRequest,
        *args,
        **kwargs,
    ) -> HttpResponse:
        """Se usa para actualizar la vista cambiando la lista de registros mostrados (por ejemplo, cuando se eliminan registros)"""

        self.object_list = self.get_queryset(queryset=self.queryset)  # type: ignore - el tipo del queryset es correcto

        contexto = self.get_context_data(*args, **kwargs)

        contexto["lista_reemplazada_por_htmx"] = (
            True  # indicar que solo se cambia la lista de objetos
        )

        contexto["mensajes_recibidos"] = True  # mostrar mensajes al actualizar

        return render(
            request,
            self.plantilla_lista,
            contexto,
        )

    def mensaje_luego_eliminar(
        self, request: HttpRequest, eliminados: int, ids_eliminados: "dict[str, int]"
    ):
        """Enviar el mensaje del resultado en la petición de eliminación de registros (llamado desde el método "eliminar" luego de las operaciones de eliminación)"""

        if eliminados > 0:
            messages.success(
                request,
                f"Se eliminaron {self.articulo_sustantivo_plural} {self.nombre_objeto_plural} seleccionad{self.vocal_del_genero}s",
            )
        else:
            messages.error(
                request,
                f"No se pudieron eliminar {self.articulo_sustantivo_plural} {self.nombre_objeto_plural} seleccionad{self.vocal_del_genero}s",
            )

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        # Guardar filtros en cookies si el formulario es válido
        if self.request.method == "POST" and hasattr(self, "form_filtros"):
            if self.form_filtros.is_valid():
                self.form_filtros.guardar_en_cookies(response)

            # Recalcular las columnas mostradas, pues pueden haberse ocultado o vuelto a mostrarse algunas
            self.establecer_columnas()

        return response


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
            f"{nombre_modelo} {self.tipo_accion_palabra}{self.vocal_del_genero} correctamente",
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


def crear_crud_urls(
    modelo: Type[models.Model],
    vista_lista: Type[VistaListaObjetos],
    vista_crear: Type[VistaCrearObjeto],
    vista_actualizar: Type[VistaActualizarObjeto],
):
    nombre_objeto_plural = f"{modelo._meta.verbose_name_plural}/"

    """Crear urls para el CRUD de un modelo"""
    return (
        path(
            nombre_objeto_plural,
            vista_lista.as_view(),
            name=nombre_url_lista_auto(modelo),
        ),
        path(
            f"{nombre_objeto_plural}crear/",
            vista_crear.as_view(),
            name=nombre_url_crear_auto(modelo),
        ),
        path(
            f"{nombre_objeto_plural}editar/<int:pk>/",
            vista_actualizar.as_view(),
            name=nombre_url_editar_auto(modelo),
        ),
    )
