from functools import reduce
from typing import Type
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.db import models
from django.db.models.functions.datetime import TruncMinute
from django.urls import reverse
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    QueryDict,
)
from django.shortcuts import redirect
from django.db.models import (
    Case,
    Q,
    F,
    Count,
    Prefetch,
    Value,
    When,
)
from django.views.generic import CreateView, FormView, ListView, UpdateView
from app import HTTPResponseHXRedirect
from app.util import mn, nc, obtener_filtro_bool_o_nulo
from app.vistas import nombre_url_lista_auto
from app.vistas.forms import (
    VistaActualizarObjeto,
    VistaCrearObjeto,
    VistaForm,
)
from app.vistas.listas import VistaListaObjetos, VistaTablaAdaptable
from estudios.forms.gestion.personas import (
    FormMatricula,
    FormProfesor,
    FormProfesorMateriaMasivo,
    FormTransferirProfesorMateria,
)
from estudios.forms.gestion.busqueda import (
    MatriculaBusquedaForm,
    ProfesorBusquedaForm,
    ProfesorMateriaBusquedaForm,
)
from estudios.modelos.gestion.personas import (
    MatriculaEstados,
    Matricula,
    Profesor,
    ProfesorMateria,
)
from estudios.modelos.parametros import Lapso
from django.db.models.functions import Concat
from django.contrib import messages
from estudios.modelos.parametros import obtener_lapso_actual
from estudios.vistas.gestion import aplicar_filtros_secciones_y_lapsos
from usuarios.models import Grupo, GruposBase, Usuario
from usuarios.forms import FormUsuario


class ListaMatriculas(VistaTablaAdaptable):
    template_name = "gestion/matriculas/index.html"
    plantilla_lista = "gestion/matriculas/lista.html"
    model = Matricula
    genero_sustantivo_objeto = "F"
    form_filtros = MatriculaBusquedaForm  # type: ignore
    paginate_by = 50
    columnas_totales = (
        {"titulo": "Estudiante", "clave": "estudiante_nombres"},
        {"titulo": "Cédula", "clave": "estudiante_cedula", "alinear": "derecha"},
        {"titulo": "Sección", "clave": "seccion_nombre"},
        {"titulo": "Estado", "clave": "estado"},
        {"titulo": "Lapso", "clave": "lapso_nombre"},
        {"titulo": "Fecha de añadida", "clave": "fecha"},
    )
    columnas_a_evitar = set()
    estados_opciones = dict(MatriculaEstados.choices)
    lapso_actual: "Lapso | None" = None

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(
            Matricula.objects.annotate(
                seccion_nombre=F("seccion__nombre"),
                estudiante_cedula=F("estudiante__cedula"),
                lapso_nombre=F("lapso__nombre"),
                estudiante_nombres=Concat(
                    "estudiante__nombres", Value(" "), "estudiante__apellidos"
                ),
                fecha=TruncMinute("fecha_añadida"),
                # no se pueden modificar las matriculas de un lapso distinto al actual
                no_modificable=Case(
                    When(Q(lapso=obtener_lapso_actual()), then=0), default=1
                ),
                # no se pueden seleccionar las matriculas de un lapso distinto al actual
                no_seleccionable=F("no_modificable"),
            ).order_by(
                "-lapso__id",
                "-fecha_añadida",
                "seccion__letra",
                "estudiante__apellidos",
                "estudiante__nombres",
            )
        )

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        queryset = aplicar_filtros_secciones_y_lapsos(
            self, queryset, datos_form, "seccion"
        )

        if estado := self.obtener_y_alternar("estado", datos_form, "estado"):
            queryset = queryset.filter(estado=estado)

        return queryset

    def get(self, request: HttpRequest, *args, **kwargs):
        self.lapso_actual = obtener_lapso_actual()
        return super().get(request, *args, **kwargs)

    def eliminar_seleccionados(self, ids):
        return Matricula.objects.filter(id__in=ids, lapso=self.lapso_actual).delete()


class CrearMatricula(VistaCrearObjeto):
    template_name = "gestion/matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"


class ActualizarMatricula(VistaActualizarObjeto):
    template_name = "gestion/matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"

    def no_se_puede_actualizar(self, request: HttpRequest):
        if self.object.lapso != obtener_lapso_actual():  # type: ignore
            messages.error(
                request,
                "No se puede actualizar una matricula de un lapso distinto al actual",
            )
            return True

    def get(self, request: HttpRequest, *args, **kwargs):
        r = super().get(request, *args, **kwargs)

        if self.no_se_puede_actualizar(request):
            return redirect(self.success_url)  # type: ignore

        return r

    def post(self, request: HttpRequest, *args, **kwargs):
        r = super().post(request, *args, **kwargs)

        if self.no_se_puede_actualizar(request):
            return redirect(self.success_url)  # type: ignore

        return r


class ListaProfesores(VistaListaObjetos):
    model = Profesor
    template_name = "gestion/profesores/index.html"
    plantilla_lista = "gestion/profesores/lista.html"
    form_filtros = ProfesorBusquedaForm  # type: ignore

    def get_queryset(self, *args, **kwargs):
        q = Profesor.objects.annotate(
            foto_perfil=F("usuario__foto_perfil"),
            miniatura_foto=F("usuario__miniatura_foto"),
            materias_asignadas=Count("profesormateria"),
        ).only(
            "id",
            *(
                nc(Profesor.cedula),
                nc(Profesor.telefono),
                nc(Profesor.usuario),
                nc(Profesor.fecha_ingreso),
            ),
        )

        return super().get_queryset(q)

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if (
            tiene_usuario := obtener_filtro_bool_o_nulo(
                ProfesorBusquedaForm.Campos.TIENE_USUARIO, datos_form
            )
        ) is not None:
            f = Q(usuario__isnull=False)
            queryset = queryset.filter(f if tiene_usuario else ~f)

        if (
            activo := obtener_filtro_bool_o_nulo(
                ProfesorBusquedaForm.Campos.ACTIVO, datos_form
            )
        ) is not None:
            f = Q(activo=True)
            queryset = queryset.filter(f if activo else ~f)

        if (
            tiene_telefono := obtener_filtro_bool_o_nulo(
                ProfesorBusquedaForm.Campos.TIENE_TELEFONO, datos_form
            )
        ) is not None:
            f = Q(telefono__isnull=False) & ~Q(telefono="")

            queryset = queryset.filter(f if tiene_telefono else ~f)

        return queryset


class ProfesorFormMixin(PermissionRequiredMixin, FormView):
    usuario_form_class: Type[FormUsuario] = FormUsuario
    model = Profesor
    object: "Profesor | None"
    template_name = "gestion/profesores/form/index.html"
    invalido_url = "objeto-form.html#invalido"
    mensaje_exito_con_usuario: str
    mensaje_exito: str

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if "usuario_form" not in ctx:
            ctx["usuario_form"] = self.get_usuario_form(
                self.request.POST.get("usuario_manual", False) == "on"
            )

        if self.object:
            ctx["editando"] = 1

        if self.request.method == "GET":
            filtros = ~Q(miniatura_foto__isnull=True) & ~Q(miniatura_foto="")
            q = Usuario.objects.values_list("id", "miniatura_foto").filter(
                filtros,
                profesor__isnull=True,
            )

            # Al editar, incluir la miniatura del usuario asociado al profesor
            if self.object and self.object.usuario:
                q |= Usuario.objects.values_list("id", "miniatura_foto").filter(
                    filtros, pk=self.object.usuario.pk
                )

            ctx["miniaturas"] = list(map(lambda x: (str(x[0]), x[1]), q))

        return ctx

    def get_usuario_form(self, usuario_manual=False):
        """Obtiene el formulario de usuario"""

        # solo crea el formulario de usuario si es necesario (se evita mostrar errores si no se indica usuario_manual)
        if self.request.method == "POST" and usuario_manual:
            f = self.usuario_form_class(self.request.POST, self.request.FILES)
            f.full_clean()
            return f

        return self.usuario_form_class()

    def render_to_response(self, context, **response_kwargs):
        r = super().render_to_response(context, **response_kwargs)

        if context["form"].errors or context["usuario_form"].errors:
            r.template_name = self.invalido_url  # type: ignore

        return r

    def get_form_kwargs(self):
        post = self.request.POST.copy()
        usuario_manual = post.get("usuario_manual", False) == "on"

        # Si se solicita crear usuario, no se envía el usuario seleccionado (en caso de haberlo hecho)
        if usuario_manual:
            post["usuario"] = ""
            self.request.POST = post  # type: ignore - Sí se puede modificar el POST

        return super().get_form_kwargs()

    def post(self, *args, **kwargs):
        profesor_form = self.get_form()
        usuario_manual = self.request.POST.get("usuario_manual", False) == "on"

        # Validar formularios según corresponda
        profesor_valido = profesor_form.is_valid()

        # Válido por defecto, ya que si no se solicita crear usuario manual, ya se valida el usuario escogido
        usuario_valido = True
        usuario_form = None

        # Si se solicita crear usuario, validar los campos para poder crear y asignar
        if usuario_manual:
            usuario_form = self.get_usuario_form(True)
            usuario_valido = usuario_form.is_valid()

        if profesor_valido and usuario_valido:
            return self.forms_validos(profesor_form, usuario_form, usuario_manual)
        else:
            return self.forms_invalidos()

    def forms_invalidos(self):
        """Maneja formularios inválidos"""

        messages.error(self.request, "Corrige los errores en el formulario")
        return self.render_to_response(self.get_context_data())

    @transaction.atomic
    def forms_validos(
        self,
        profesor_form: FormProfesor,
        usuario_form: "FormUsuario | None",
        usuario_manual: bool = False,
    ):
        """Procesa ambos formularios cuando son válidos"""

        # Guardar profesor
        profesor = self.object = profesor_form.save()

        if not isinstance(profesor, Profesor):
            raise Exception("Profesor no creado")

        # Si se solicita crear usuario
        if usuario_manual:
            if not isinstance(usuario_form, FormUsuario):
                raise Exception("Formulario de usuario no creado")

            usuario: Usuario = usuario_form.save(commit=False)
            usuario.is_active = True
            usuario.set_password(usuario_form.cleaned_data["password"])

            usuario.save()
            usuario_form.save_m2m()  # Guardar relaciones muchos-a-muchos
            usuario.grupos.add(Grupo.objects.get(name=GruposBase.PROFESOR.value))

            # Asignar el usuario creado al profesor
            profesor.usuario = usuario
            profesor.save()

            messages.success(
                self.request,
                f"Profesor {self.mensaje_exito_con_usuario}: {usuario.username}",
                "retraso=7000",
            )
        else:
            messages.success(self.request, self.mensaje_exito)

        # ya que la petición se hace por HTMX, se debe usar la clase que permite redireccionar con este
        return HTTPResponseHXRedirect(reverse(nombre_url_lista_auto(self.model)))


class CrearProfesor(ProfesorFormMixin, CreateView):
    form_class: Type[FormProfesor] = FormProfesor  # type: ignore - el tipo del form es correcto
    permission_required = f"{Profesor._meta.app_label}.add_{mn(Profesor)}"
    mensaje_exito = "Profesor creado exitosamente."
    mensaje_exito_con_usuario = "creado exitosamente con usuario"

    def post(self, *args, **kwargs):
        self.object = None
        return super().post(*args, **kwargs)


class ActualizarProfesor(ProfesorFormMixin, UpdateView):
    form_class: Type[FormProfesor] = FormProfesor  # type: ignore - el tipo del form es correcto
    permission_required = f"{Profesor._meta.app_label}.change_{mn(Profesor)}"
    mensaje_exito = "Profesor actualizado exitosamente."
    mensaje_exito_con_usuario = (
        "actualizado correctamente y asignado a un nuevo usuario"
    )

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        return super().post(*args, **kwargs)


class ListaProfesoresMaterias(VistaListaObjetos):
    model = ProfesorMateria
    form_filtros = ProfesorMateriaBusquedaForm  # type: ignore
    form_transferencia = FormTransferirProfesorMateria  # type: ignore
    genero_sustantivo_objeto = "F"
    template_name = "gestion/profesores_materias/index.html"
    plantilla_lista = "gestion/profesores_materias/lista.html"
    # igual al nombre del campo del form de transferencia, para pasarle la lista y que verifique
    ids_objetos_kwarg = FormTransferirProfesorMateria.Campos.MATERIAS

    def get_queryset(self, *args, **kwargs):
        profesores = (
            Profesor.objects.filter(activo=True, profesormateria__isnull=False)
            .annotate(cantidad_materias=Count("profesormateria"))
            .order_by("apellidos", "nombres")
        )

        return super().get_queryset(profesores)

    def aplicar_filtros(self, queryset: models.QuerySet, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        # subconsulta que obtiene las materias de cada profesor
        pm_queryset = ProfesorMateria.objects.select_related("materia", "seccion__año")

        # filtrar ambas consultas para que coincidan y se muestren los resultados correctamente
        if materias := datos_form.get("materias"):
            pm_queryset = pm_queryset.filter(materia__in=materias)
            queryset = queryset.filter(profesormateria__materia__in=materias)

        if años := datos_form.get("anios"):
            pm_queryset = pm_queryset.filter(seccion__año__in=años)
            queryset = queryset.filter(profesormateria__seccion__año__in=años)

        if secciones := datos_form.get("secciones"):
            pm_queryset = pm_queryset.filter(seccion__in=secciones)
            queryset = queryset.filter(profesormateria__seccion__in=secciones)

        return queryset.prefetch_related(
            Prefetch(
                "profesormateria_set",
                queryset=pm_queryset,
                to_attr="materias_asignadas",
            )
        )

    def get(self, request: HttpRequest, *args, **kwargs):
        r = super(ListView, self).get(request, *args, **kwargs)

        self.total = ProfesorMateria.objects.count()

        return r

    def actualizar(
        self, request: HttpRequest, ids: "list[str]", datos: QueryDict, *args, **kwargs
    ):
        form = self.form_transferencia(datos)

        if not form.is_valid():
            return HttpResponseBadRequest("El profesor escogido es inválido")

        profesor: Profesor = form.cleaned_data[
            FormTransferirProfesorMateria.Campos.PROFESOR
        ]
        # lista de profesores_materias ya existentes
        pms: "list[ProfesorMateria]" = form.cleaned_data[
            FormTransferirProfesorMateria.Campos.MATERIAS
        ]

        # ya que se puede seleccionar al mismo profesor que contiene las materias, se lleva la cuenta para evitar la transferencia
        a_transferir: "list[ProfesorMateria]" = []

        for pm in pms:
            if pm.profesor != profesor:
                pm.profesor = profesor
                a_transferir.append(pm)

        # No hay materias para transferir
        if len(a_transferir) == 0:
            messages.error(
                request,
                f"Todas las materias seleccionadas ya están asignadas a {profesor.nombre_completo}.",
                "retraso=8000",
            )
        else:
            cantidad = ProfesorMateria.objects.bulk_update(
                a_transferir,
                fields=[nc(ProfesorMateria.profesor)],
            )

            if cantidad:
                messages.success(
                    request,
                    f"Se transfiri{'eron' if cantidad > 1 else 'o'} {cantidad} materia{'s' if cantidad > 1 else ''} a {profesor.nombre_completo}.",
                    "retraso=7000",
                )
            else:
                messages.error(
                    request,
                    f"No se pud{'ieron' if cantidad > 1 else 'o'} transferir {cantidad} materia{'s' if cantidad > 1 else ''} a {profesor.nombre_completo}.",
                    "retraso=7000",
                )

    def mensaje_luego_eliminar(
        self, request: HttpRequest, eliminados: int, ids_eliminados: "dict[str, int]"
    ):
        n = eliminados

        if n > 0:
            messages.success(
                request,
                f"Se elimin{'aron' if n > 1 else 'o'} {'las' if n > 1 else 'la'} {n if n > 1 else ''} materia{'s'} asignada{'s' if n > 1 else ''} de los profesores seleccionados.",
                "retraso=10000",
            )
        else:
            messages.error(
                request,
                f"No se pud{'ieron' if n > 1 else 'o'} eliminar {'las' if n > 1 else 'la'} {n if n > 1 else ''} materia{'s' if n > 1 else ''} asignada{'s' if n > 1 else ''} de los profesores seleccionados.",
            )

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        if self.request.method == "GET":
            # mostrar la lista de profesores para escoger a la hora de transferir materias
            ctx["form_transferencia"] = self.form_transferencia()

            ctx["profesores_faltantes"] = Profesor.objects.filter(
                activo=True, profesormateria__isnull=True
            ).count()

        self.cantidad_filtradas = reduce(
            lambda x, y: x + len(y.materias_asignadas), ctx["object_list"], 0
        )

        return ctx


class CrearProfesorMateria(VistaForm, FormView):
    tipo_permiso = "add"
    tipo_accion_palabra = "cread"
    model = ProfesorMateria
    form_class = FormProfesorMateriaMasivo
    template_name = "gestion/profesores_materias/form.html"
    genero_sustantivo_objeto = "F"

    def get_initial(self):
        """Seleccionar un profesor específico por defecto si se proporciona el id por GET"""
        if profesor_id := self.request.GET.get("profesor_id"):
            if profesor_id.isdigit() and (
                profesor := Profesor.objects.filter(id=profesor_id).first()
            ):
                return {"profesor": profesor}

        return {}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["miniaturas"] = list(
            map(
                lambda x: (str(x[0]), x[1]),
                Profesor.objects.values_list("id", "usuario__miniatura_foto").filter(
                    ~Q(usuario__miniatura_foto__isnull=True)
                    & ~Q(usuario__miniatura_foto="")
                ),
            )
        )

        form: FormProfesorMateriaMasivo = ctx["form"]

        materias_disponibles_agrupadas = {}

        for materia in form.fields[f"{nc(ProfesorMateria.materia)}s"].choices:  # type: ignore - sí es un MultipleChoiceField
            label_opcion = materia[1].split("_", maxsplit=1)
            nombre_materia, nombre_seccion = label_opcion

            if nombre_materia not in materias_disponibles_agrupadas:
                materias_disponibles_agrupadas[nombre_materia] = []

            materias_disponibles_agrupadas[nombre_materia].append(
                {
                    "id": str(materia[0]),
                    "label": nombre_seccion,
                }
            )

        ctx["materias_disponibles_agrupadas"] = [
            {"label": pm[0], "opciones": pm[1]}
            for pm in materias_disponibles_agrupadas.items()
        ]

        return ctx
