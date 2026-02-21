from typing import Mapping, Sequence, Type, Any
from django.db import models
from django.shortcuts import render
from django.views.generic import ListView
from app.forms import BusquedaFormMixin, DireccionesOrden, OrdenFormMixin
from app.vistas._tipos import (
    Columna,
    ColumnaFija,
    Metodo,
    VistaListaContexto,
)
from app.vistas import (
    Vista,
    nombre_url_crear_auto,
    nombre_url_editar_auto,
)
from django.contrib import messages
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    QueryDict,
)


class FormFiltrosMixin:
    request: HttpRequest
    form_filtros: Type[BusquedaFormMixin]
    kwargs: dict
    page_kwarg: str

    def usar_filtros(self, queryset: models.QuerySet):
        if hasattr(self, "form_filtros"):
            datos_form = self.inicializar_form_filtros()

            queryset = self.aplicar_orden(queryset, datos_form)

            # modificar paginación de acuerdo a los filtros
            self.modificar_paginacion(datos_form)

            # modificar queryset de acuerdo a los filtros
            queryset = self.aplicar_filtros(
                queryset=queryset,
                datos_form=datos_form,
            )

        return queryset

    def aplicar_filtros(
        self,
        queryset: models.QuerySet,
        datos_form: "dict[str, Any] | Mapping[str, Any]",
    ):
        queryset = self.aplicar_busqueda(queryset, datos_form)
        return queryset

    def aplicar_busqueda(
        self,
        queryset: models.QuerySet,
        datos_form: "dict[str, Any] | Mapping[str, Any]",
    ):
        """Modifica el queryset de acuerdo a los filtros indicados en el form de filtros. Por defecto, verifica si se trata de un form de busqueda textual y aplica las búsquedas si es necesario."""

        if isinstance(self.form_filtros, BusquedaFormMixin):
            for campo in self.form_filtros:
                # cada campo debe tener el atributo "nombre_columna_db" que indica el nombre de la columna de la base de datos
                if not hasattr(campo.field, "nombre_columna_db"):
                    continue

                nombre_columna_db: "str | None" = getattr(
                    campo.field, "nombre_columna_db"
                )

                if not nombre_columna_db:
                    continue

                # obtener el valor de la búsqueda
                q: "str | None" = datos_form.get(campo.name)

                if not q:
                    continue

                # cada campo debe tener el atributo "tipo_" + nombre del campo. Este indica el tipo de búsqueda a realizar
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

    def aplicar_orden(
        self,
        queryset: models.QuerySet,
        datos_form: "dict[str, Any] | Mapping[str, Any]",
    ):
        """Ordena el queryset de acuerdo a los filtros de orden indicados en el form de filtros"""
        if isinstance(self.form_filtros, OrdenFormMixin):
            for nombre, _ in self.form_filtros.campos_orden:  # type: ignore
                if direccion := datos_form.get(nombre):
                    columna = nombre.split("-")[0]

                    if direccion == DireccionesOrden.ASC.value[0]:
                        columna = "-" + columna

                    queryset = queryset.order_by(columna)
        elif self.ordering:  # type: ignore - sí es del tipo que se espera
            ordering: str | Sequence[str] = self.ordering  # type: ignore - sí es del tipo que se espera

            if isinstance(ordering, str):
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by(*ordering)

        return queryset

    def inicializar_form_filtros(self):
        """Establece los datos del form de filtros según el método de la request, los valida y, si son válidos los retorna, si no retorna los valores por defecto."""

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

            self.form_filtros = self.form_filtros(  # type: ignore - sí es una clase
                datos, request=self.request
            )

        if self.form_filtros.is_valid():  # type: ignore - sí se pasa "self"
            return self.form_filtros.cleaned_data
        else:
            return self.form_filtros.initial

    # aplicación de filtros por POST
    def post(self, request: HttpRequest, *args, **kwargs):
        respuesta = super().get(request, *args, **kwargs)  # type: ignore

        if hasattr(self, "form_filtros"):
            respuesta.template_name = self.plantilla_lista  # type: ignore

            # Validar el formulario y guardar en cookies los valores
            if self.form_filtros.is_valid():  # type: ignore - sí se pasa "self"
                self.form_filtros.guardar_en_cookies(respuesta)  # type: ignore - sí se pasa "self"

            return respuesta

        return HttpResponse("No se indicó un form de filtros", status=405)

    def modificar_paginacion(self, datos_form: "dict[str, Any] | Mapping[str, Any]"):
        """Modifica la paginación de acuerdo a los campos "pagina" y "cantidad_por_pagina" """

        # Ya que la paginación se hace por POST con HTMX, se debe modificar el kwarg que la vista usa para ella

        # En caso de pasar la página actual desde el componente de la paginación (Por defecto)
        if self.form_filtros.fields.get("pagina"):
            self.kwargs[self.page_kwarg] = int(
                datos_form.get(
                    "pagina",
                    "1",
                )
            )

        # Si se pasa la página actual desde un formulario
        elif p := self.request.POST.get("page"):
            self.kwargs[self.page_kwarg] = int(p)

        # Modificar la cantidad de registros por pagina
        if self.form_filtros.fields.get("cantidad_por_pagina"):
            cantidad_por_pagina = datos_form.get(
                "cantidad_por_pagina",
            )

            # Si se pasa por el form de filtros
            if cantidad_por_pagina is not None:
                try:
                    cantidad_por_pagina = int(cantidad_por_pagina)
                except (TypeError, ValueError):
                    cantidad_por_pagina = 0

                if cantidad_por_pagina > 0:
                    self.paginate_by = cantidad_por_pagina
            # no hay un valor por defecto, se usa el de la clase
            elif self.paginate_by:
                datos_form["cantidad_por_pagina"] = self.paginate_by  # type: ignore - sí se puede modificar

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)  # type: ignore

        if self.request.method == "POST":
            ctx["lista_reemplazada_por_htmx"] = 1  # type: ignore

        return ctx


class VistaListaObjetos(Vista, FormFiltrosMixin, ListView):
    """Clase base para vistas que muestran una lista de objetos."""

    model: Type[models.Model]  # type: ignore
    tipo_permiso = "view"
    context_object_name = "lista_objetos"
    total: "int | None" = None
    cantidad_filtradas: "int | None" = None
    plantilla_lista: str
    id_lista_objetos: str = "lista-objetos"
    url_crear: str
    url_editar: str
    # nombre del campo o atributo que contiene los ids de los objetos seleccionados
    ids_objetos_kwarg = "ids"
    http_method_names: "list[Metodo] | tuple[Metodo, ...]" = (  # type: ignore - cualquier string sirve
        "get",
        "post",
        "put",
        "delete",
    )
    ordering = "id"
    # si se quiere agrupar los resultados
    agrupados = False

    def __init__(self):
        """Establece automáticamente los atributos url_crear y url_editar si no se han establecido. Estos se usan en el html de la vista para indicar los enlaces para crear y editar el tipo de objeto de la vista en cuestión."""

        if not hasattr(self, "url_crear"):
            self.url_crear = nombre_url_crear_auto(self.model)

        if not hasattr(self, "url_editar"):
            self.url_editar = nombre_url_editar_auto(self.model)

        super().__init__()

    def get_queryset(
        self, queryset: "models.QuerySet | None" = None
    ) -> "models.QuerySet":
        """Retorna el queryset. Si se indica un form de orden, se ordenan los datos de acuerdo a los valores indicados. Si se indica un form de filtros, se filtran los datos de acuerdo a los valores indicados."""
        if queryset is None:
            raise ValueError("Se debe indicar un queryset")

        queryset = self.usar_filtros(queryset)

        return queryset

    def agrupar_queryset(self, lista_objetos: models.QuerySet) -> models.QuerySet:
        """Agrupa el queryset de acuerdo otro modelo relacionado. Retorna una lista con los objetos del modelo principal para cada objeto del modelo relacionado"""
        raise NotImplementedError

    def get_context_data(self, *args, **kwargs):
        """Agrega los datos necesarios al context para la vista. Por defecto obtiene la instancia del form de filtros, los modelos relacionados, los permisos del usuario en relación al modelo y una variable que indica si no hay objetos del modelo indicado en la base de datos"""

        ctx = super().get_context_data(*args, **kwargs)

        try:
            ctx["modelos_relacionados"] = tuple(
                map(
                    lambda obj: obj.related_model._meta.verbose_name_plural,
                    self.model._meta.related_objects,  # type: ignore
                )
            )
        except Exception:
            ctx["modelos_relacionados"] = ()

        if self.agrupados:
            """ Al agrupar el queryset, se debe cambiar la lista de objetos del contexto"""
            ctx[self.context_object_name or "object_list"] = self.agrupar_queryset(
                self.object_list  # type: ignore - sí es un queryset
            )

        ctx.update(
            VistaListaContexto(
                form_filtros=self.form_filtros
                if hasattr(self, "form_filtros")
                else None,
                form_con_orden=True
                if hasattr(self, "form_filtros")
                and isinstance(self.form_filtros, OrdenFormMixin)
                else False,
                permisos={
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
                no_hay_objetos=self.total == 0
                if self.total is not None
                else not self.al_menos_uno(),
                sin_resultados=self.sin_resultados(),
            )
        )

        return ctx

    def obtener_total(self):
        """Obtiene el total de objetos del modelo indicado en la base de datos"""
        self.total = self.model.objects.count()

    def al_menos_uno(self):
        """Verifica si hay al menos un objeto del modelo indicado en la base de datos. Se usa cuando no se define el atributo "total" """
        return self.model.objects.exists()

    def sin_resultados(self):
        """Verifica si la búsqueda no arroja resultados."""
        return self.object_list.count() == 0  # type: ignore - sí es un queryset

    def get(self, request: HttpRequest, *args, **kwargs):
        respuesta = super().get(request, *args, **kwargs)

        # cambio de página
        if self.paginate_by is not None:
            if request.GET.get("solo_tabla"):
                respuesta.context_data["lista_reemplazada_por_htmx"] = 1  # type: ignore
                respuesta.template_name = self.plantilla_lista  # type: ignore

        self.obtener_total()

        return respuesta

    def http_method_not_allowed(self, request, *args, **kwargs):
        # Customize the response for unsupported methods
        return HttpResponseNotAllowed(
            permitted_methods=self.http_method_names,
            content=f"Se usó un método no permitido. Solo se acepta {', '.join(self.http_method_names)}",
        )

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

        ids = request.GET.getlist(self.ids_objetos_kwarg)

        if not ids or not isinstance(ids, list):
            return HttpResponseBadRequest(
                f"No se indicó una lista de {self.ids_objetos_kwarg}"
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


class VistaTablaAdaptable(VistaListaObjetos):
    """Vista especializada para mostrar listas de registros usado el componente de la tabla adaptable. Se encarga de establecer los elementos necesarios para su correcto funcionamiento."""

    columnas_totales: "tuple[ColumnaFija, ...]"  # Columnas fijas
    columnas_mostradas: "list[Columna]"
    columnas_a_evitar: "set[str]"
    columnas_ocultables: "list[str]"

    def __init__(self):
        """Establece automáticamente los atributos "columnas_mostradas" y "columnas_ocultables", si no se indicaron al instanciar la clase. Estos se usan en el HTML de la vista para indicar las columnas de la tabla mostrada."""

        if not hasattr(self, "columnas_mostradas") or not self.columnas_mostradas:
            self.establecer_columnas()

        super().__init__()

    def establecer_columnas(self):
        """Establece las columnas mostradas y las columnas ocultables. Estas corresponden a las columnas de la tabla en el HTML. Verifica si no se definieron las columnas al instanciar para hacerlo automáticamente a partir del modelo. En cualquier caso se encarga de evitar incluir las columnas que se quieran ocultar"""

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
        """Establece las columnas que no se debe mostrar cuando la tabla adaptable no mide el ancho indicado. Por defecto oculta todas menos la segunda, por lo que quedan (#, nombre / identificador y  el campo X)"""

        self.columnas_ocultables = list(
            map(lambda col: col["titulo"], self.columnas_mostradas[1:])
        )

    def alternar_col_por_filtro(self, valor_filtro: "Any | None", columna: str):
        """Indica que una columna de la tabla debe o no mostrarse según un filtros usado"""

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
        """Devuelve el dato de un campo de un formulario al mismo tiempo que alterna la visibilidad de una columna de la tabla mostrada."""

        dato = datos_form.get(nombre_campo)
        self.alternar_col_por_filtro(dato, nombre_columna)

        return dato

    def post(self, request: HttpRequest, *args, **kwargs):
        r = super().post(request, *args, **kwargs)

        if hasattr(self, "form_filtros"):
            # Recalcular las columnas mostradas, pues pueden haberse ocultado o vuelto a mostrarse algunas
            self.establecer_columnas()

        return r
