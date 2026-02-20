from functools import reduce
from typing import Any, Type
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db import models
from django.urls import reverse
from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    QueryDict,
)
from django.shortcuts import redirect
from django.db.models import (
    Q,
    F,
    Case,
    Count,
    Prefetch,
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
from app.vistas.listas import VistaListaObjetos
from estudios.forms.gestion.personas import (
    FormEstudiante,
    FormMatricula,
    FormMatricularEstudiantes,
    FormProfesor,
    FormProfesorMateriaMasivo,
    FormTransferirProfesorMateria,
)
from estudios.forms.gestion.busqueda import (
    EstudianteBusquedaForm,
    MatriculaBusquedaForm,
    ProfesorBusquedaForm,
    ProfesorMateriaBusquedaForm,
)
from estudios.modelos.gestion.personas import (
    Estudiante,
    MatriculaEstados,
    Matricula,
    Profesor,
    ProfesorMateria,
)
from estudios.modelos.parametros import Lapso, Seccion
from django.contrib import messages
from estudios.modelos.parametros import obtener_lapso_actual
from usuarios.models import Grupo, GruposBase, Usuario
from usuarios.forms import FormUsuario


class ListaProfesores(VistaListaObjetos):
    model = Profesor
    template_name = "personas/profesores/index.html"
    plantilla_lista = "personas/profesores/lista.html"
    form_filtros = ProfesorBusquedaForm

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
    template_name = "personas/profesores/form/index.html"
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
    form_filtros = ProfesorMateriaBusquedaForm
    form_transferencia = FormTransferirProfesorMateria
    genero_sustantivo_objeto = "F"
    paginate_by = 10
    template_name = "personas/profesores_materias/index.html"
    plantilla_lista = "personas/profesores_materias/lista.html"
    # igual al nombre del campo del form de transferencia, para pasarle la lista y que verifique
    ids_objetos_kwarg = FormTransferirProfesorMateria.Campos.MATERIAS

    def get_queryset(self, *args, **kwargs):
        q = Profesor.objects.annotate(cantidad_materias=Count("profesormateria"))

        return super().get_queryset(q)

    def aplicar_filtros(self, queryset: models.QuerySet, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        # subconsulta que obtiene las materias de cada profesor
        pm_queryset = self.model.objects.all()

        # filtrar ambas consultas para que coincidan y se muestren los resultados correctamente
        if materias := datos_form.get("materias"):
            pm_queryset = pm_queryset.filter(materia__in=materias)

        if años := datos_form.get("anios"):
            pm_queryset = pm_queryset.filter(seccion__año__in=años)

        if secciones := datos_form.get("secciones"):
            pm_queryset = pm_queryset.filter(seccion__in=secciones)

        return queryset.filter(profesormateria__in=pm_queryset).prefetch_related(
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
    template_name = "personas/profesores_materias/form.html"
    genero_sustantivo_objeto = "F"

    def get_initial(self):
        """Seleccionar un profesor específico por defecto si se proporciona el id por GET"""
        if (
            profesor_id := self.request.GET.get("profesor_id", "")
        ) and profesor_id.isdigit():
            profesor = Profesor.objects.filter(id=profesor_id).first()

            if profesor and profesor.activo:
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


class ListaEstudiantes(VistaListaObjetos):
    model = Estudiante
    paginate_by = 20
    form_filtros = EstudianteBusquedaForm
    form_matricular = FormMatricularEstudiantes
    template_name = "personas/estudiantes/index.html"
    plantilla_lista = "personas/estudiantes/lista.html"
    # igual al nombre del campo del form de matricular, para pasarle la lista y que verifique
    ids_objetos_kwarg = "estudiantes"

    def get_queryset(self, *args, **kwargs):
        q = self.model.objects.all().annotate()

        lapsos = Lapso.objects.order_by("-id")

        try:
            lapso_actual = self.lapso_actual = lapsos[0]
        except IndexError:
            lapso_actual = self.lapso_actual = None

        if lapso_actual:
            matriculas_actuales = Matricula.objects.filter(lapso=lapso_actual).only(
                "seccion__nombre"
            )
            """ promedios_actuales = Nota.objects.annotate(promedio=Avg("valor")).filter(
                matricula__in=matriculas_actuales
            ) """

            q = q.prefetch_related(
                Prefetch(
                    "matricula_set",
                    queryset=matriculas_actuales,
                    to_attr="matricula_actual",
                )
            )

        try:
            lapso_anterior = lapsos[1]
        except IndexError:
            lapso_anterior = None

        if lapso_anterior:
            matriculas_anteriores = Matricula.objects.filter(lapso=lapso_anterior).only(
                "seccion__nombre"
            )

            q = q.prefetch_related(
                Prefetch(
                    "matricula_set",
                    queryset=matriculas_anteriores,
                    to_attr="matricula_anterior",
                )
            )

        return super().get_queryset(q)

    def aplicar_filtros(self, queryset: models.QuerySet, datos_form):
        q = super().aplicar_filtros(queryset, datos_form)

        if (
            matricula_actual := obtener_filtro_bool_o_nulo(
                EstudianteBusquedaForm.Campos.MATRICULA_ACTUAL, datos_form
            )
        ) is not None:
            if matricula_actual:
                q = q.filter(
                    matricula__isnull=False, matricula__lapso=self.lapso_actual
                )
            else:
                q = q.filter(matricula__isnull=True).exclude(
                    matricula__lapso=self.lapso_actual
                )

        if secciones := datos_form.get(EstudianteBusquedaForm.Campos.SECCIONES):
            q = q.filter(matricula__seccion__in=secciones)

        return q

    def actualizar(
        self, request: HttpRequest, ids: "list[str]", datos: QueryDict, *args, **kwargs
    ):
        form = self.form_matricular(datos)

        if form.is_valid():
            matriculas = form.save()

            if matriculas:
                messages.success(
                    request,
                    f"{len(matriculas)} estudiantes matriculados correctamente.",
                )
            else:
                return HttpResponseBadRequest("No se matricularon los estudiantes.")
        else:
            if form.has_error("estudiantes"):
                return HttpResponseBadRequest(
                    "Algunos estudiantes seleccionados ya están matriculados."
                )
            else:
                return HttpResponseBadRequest("El formulario no es válido.")

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        if self.request.method == "GET":
            ctx["form_matricular"] = self.form_matricular()

        ctx["puede_matricular"] = self.request.user.has_perm(  # type: ignore - sí existe "has_perm" como atributo
            f"{Matricula._meta.app_label}.add_{Matricula._meta.model_name}"
        )

        return ctx


class EstudianteVistaForm(VistaForm, FormView):
    model = Estudiante
    form_class = FormEstudiante
    template_name = "personas/estudiantes/form.html"


class CrearEstudiante(EstudianteVistaForm, VistaCrearObjeto):
    pass


class ActualizarEstudiante(EstudianteVistaForm, VistaActualizarObjeto):
    pass


class ListaMatriculas(VistaListaObjetos):
    template_name = "personas/matriculas/index.html"
    plantilla_lista = "personas/matriculas/lista.html"
    model = Matricula
    paginate_by = 5
    genero_sustantivo_objeto = "F"
    form_filtros = MatriculaBusquedaForm
    estados_opciones = dict(MatriculaEstados.choices)
    lapso_actual: "Lapso | None" = None

    def setup(self, request: HttpRequest, *args, **kwargs):
        self.lapso_actual = obtener_lapso_actual()
        return super().setup(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        datos_form = self.inicializar_form_filtros()

        # Obtener todas las combinaciones únicas de sección y lapso con sus conteos
        queryset = (
            Matricula.objects.values(
                "seccion__id",
                "seccion__nombre",
                "seccion__letra",
                "seccion__año__nombre",
                "lapso__id",
                "lapso__nombre",
                "lapso__numero",
            )
            .annotate(total_matriculas=Count("id"))
            .order_by("seccion__año__id", "seccion__letra", "lapso__numero")
        )

        self.modificar_paginacion(datos_form)

        queryset = self.aplicar_filtros(queryset, datos_form)

        return self.procesar_secciones(queryset, datos_form)

    def aplicar_filtros(self, queryset, datos_form):
        queryset = super().aplicar_filtros(queryset, datos_form)

        if lapsos := datos_form.get("lapsos"):
            queryset = queryset.filter(lapso__in=lapsos)

        if secciones := datos_form.get("secciones"):
            queryset = queryset.filter(seccion__in=secciones)

        if años := datos_form.get("anios"):
            queryset = queryset.filter(seccion__año__in=años)

        if estado := datos_form.get("estado"):
            queryset = queryset.filter(estado=estado)

        return queryset

    def eliminar(self, request: HttpRequest, ids: "list[str]"):
        return Matricula.objects.filter(id__in=ids, lapso=self.lapso_actual).delete()

    def obtener_total(self, ctx):
        self.total = self.model.objects.count()

    def paginate_queryset(self, queryset, page_size):
        """Sobrescribe el método de paginación para trabajar con la lista personalizada"""
        super().paginate_queryset(queryset, page_size)
        paginator = Paginator(queryset, page_size)

        page_kwarg = self.page_kwarg

        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1

        try:
            page_number = int(page)
        except ValueError:
            page_number = 1

        page_obj = paginator.get_page(page_number)

        return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())

    def procesar_secciones(
        self, queryset: "models.QuerySet[Matricula, dict[str, Any]]", datos_form
    ):
        """Transformar los datos en objetos más fáciles de usar en el template"""
        grupos_procesados = []

        for grupo in queryset:
            grupos_procesados.append(
                {
                    "seccion": {
                        "id": grupo["seccion__id"],
                        "nombre": grupo["seccion__nombre"],
                        "letra": grupo["seccion__letra"],
                        "año": grupo["seccion__año__nombre"],
                    },
                    "lapso": {
                        "id": grupo["lapso__id"],
                        "nombre": grupo["lapso__nombre"],
                        "numero": grupo["lapso__numero"],
                    },
                    "modificable": grupo["lapso__id"] == self.lapso_actual.pk
                    if isinstance(self.lapso_actual, Lapso)
                    else False,
                    "total_matriculas": grupo["total_matriculas"],
                    "matriculas": self.obtener_detalle_matriculas(
                        datos_form,
                        grupo["seccion__id"],
                        grupo["lapso__id"],
                    ),
                }
            )

        return grupos_procesados

    def obtener_detalle_matriculas(self, datos_form, seccion_id, lapso_id):
        """
        Obtiene el detalle de las matrículas para una sección y lapso específicos
        """

        queryset = (
            Matricula.objects.annotate(
                modificable=Case(
                    When(Q(lapso=self.lapso_actual), then=True), default=False
                )
            )
            .filter(seccion_id=seccion_id, lapso_id=lapso_id)
            .select_related("estudiante", "seccion", "lapso")
            .order_by("estudiante__apellidos", "estudiante__nombres")
        )

        queryset = self.aplicar_orden(queryset, datos_form)

        queryset = self.aplicar_busqueda(queryset, datos_form)

        return queryset

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        self.cantidad_filtradas = reduce(
            lambda x, y: x + len(y["matriculas"]), ctx["page_obj"].object_list, 0
        )

        return ctx


class MatriculaVistaForm(VistaForm, FormView):
    template_name = "personas/matriculas/form.html"
    model = Matricula
    form_class = FormMatricula
    genero_sustantivo_objeto = "F"


class CrearMatricula(MatriculaVistaForm, VistaCrearObjeto):
    def get_initial(self):
        initial = {}

        if (seccion := self.request.GET.get("seccion")) and seccion.isdecimal():
            if seccion := Seccion.objects.filter(id=seccion).first():
                initial["seccion"] = seccion

        if (
            estudiante := self.request.GET.get("estudiante_id")
        ) and estudiante.isdecimal():
            if estudiante := Estudiante.objects.filter(id=estudiante).first():
                initial["estudiante"] = estudiante

        return initial


class ActualizarMatricula(MatriculaVistaForm, VistaActualizarObjeto):
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
