from django.core.management.base import BaseCommand
from estudios.management.commands import (
    obtener_modelos_modulo,
    obtener_todos_los_modelos,
    ModelosParametros,
    ModelosCalificaciones,
    ModelosUsuarios,
)
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from estudios.modelos.gestion.calificaciones import TipoTarea
from estudios.modelos.parametros import Materia

AÑOS = [
    ("Primer Año", "1ero"),
    ("Segundo Año", "2do"),
    ("Tercer Año", "3ero"),
    ("Cuarto Año", "4to"),
    ("Quinto Año", "5to"),
]

MATERIAS = [
    "Matemática",
    "Castellano",
    "Ciencias Naturales",
    "Inglés",
    "Educación Física",
    "G.H.C",
    "C.R.P",
    "Química",
    "Orientación",
    "Física",
    "Premilitar",
]

MATERIAS_PUNTUALES = {"Premilitar": (5,), "Física": (3, 4, 5), "Química": (3, 4, 5)}

TAREAS = [
    "taller",
    "examen escrito",
    "examen oral",
    "defensa",
    "exposición",
    "trabajo completo",
    "trabajo de campo",
    "análisis",
    "ensayo",
    "presentación",
    "proyecto",
    "otra",
]


class Command(BaseCommand):
    help = "Llena la base de datos con datos estáticos (Años, materias, grupos, y un usuario admin)"

    def handle(self, *args, **options):
        self.stdout.write("Creando datos estáticos...")

        self.crear_años_y_secciones_por_defecto()

        self.crear_materias_por_defecto()

        self.crear_tareas_por_defecto()

        self.crear_grupos_por_defecto()

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Datos estáticos creados exitosamente! "
                f"({self.años_creados} años, {self.materias_creadas} materias, {self.materias_asignadas} materias asignadas, {self.tareas_creadas} tipos de tareas, {self.secciones_creadas} secciones, {self.grupos_creados} grupos)"
            )
        )

    def crear_años_y_secciones_por_defecto(self):
        años_creados = 0

        for nombre, nombre_corto in AÑOS:
            _, created = ModelosParametros.Año.objects.get_or_create(
                nombre=nombre, nombre_corto=nombre_corto
            )
            if created:
                años_creados += 1
                self.stdout.write(f"✓ Año creado: {nombre}")

        self.stdout.write("Creando secciones por defecto...")

        años = ModelosParametros.Año.objects.all()
        letras_secciones = ("A", "B")

        secciones_creadas = 0
        for año in años:
            for letra in letras_secciones:
                nombre = f"{año.nombre_corto} {letra}"
                _, created = ModelosParametros.Seccion.objects.get_or_create(
                    año=año,
                    letra=letra,
                    defaults={"nombre": nombre, "capacidad": 30},
                )
                if created:
                    secciones_creadas += 1
                    self.stdout.write(f"✓ Creada sección: {nombre}")

        self.stdout.write(f"✓ Total secciones creadas: {secciones_creadas}")

        self.años_creados = años_creados
        self.secciones_creadas = secciones_creadas

    def crear_materias_por_defecto(self):
        materias_creadas = 0
        materias_asignadas = 0

        Materia.objects.bulk_create(
            (Materia(nombre=materia) for materia in MATERIAS), ignore_conflicts=True
        )

        self.stdout.write("✓ Materias creadas")

        self.stdout.write("Asignando materias a años...")

        for materia in MATERIAS:
            for num in range(len(AÑOS)):
                num += 1
                # evitar asignar ciertas materias a todos los años, solo a algunos
                if (
                    materia in MATERIAS_PUNTUALES
                    and num not in MATERIAS_PUNTUALES[materia]
                ):
                    continue

                try:
                    _, asignada = ModelosParametros.AñoMateria.objects.get_or_create(
                        año=ModelosParametros.Año.objects.get(id=num),
                        materia=ModelosParametros.Materia.objects.get(nombre=materia),
                    )
                except:  # noqa: E722
                    continue

                if asignada:
                    self.stdout.write(f"✓ Asignada materia {materia} al año {num}")
                    materias_asignadas += 1

        self.stdout.write(f"✓ Total materias asignadas: {materias_asignadas}")

        self.materias_creadas = materias_creadas
        self.materias_asignadas = materias_asignadas

    def crear_grupos_por_defecto(self):
        self.stdout.write("Creando grupos...")
        grupos_creados = 0

        modelos_calificaciones = obtener_modelos_modulo(ModelosCalificaciones)

        modelos = obtener_todos_los_modelos()

        grupo_admin, creado = ModelosUsuarios.Grupo.objects.get_or_create(
            name=ModelosUsuarios.GruposBase.ADMIN.value,
            descripcion="Provee todos los permisos de administración del sistema",
        )

        if creado or grupo_admin.permissions.count() == 0:
            for modelo in modelos:
                content_type = ContentType.objects.get_for_model(modelo)
                permisos = Permission.objects.filter(content_type=content_type)

                for permiso in permisos:
                    # evitar asignar permisos que no sean de lectura para los modelos de calificaciones
                    if (
                        modelo in modelos_calificaciones
                        # para los tipos de tareas sí tienen permisos
                        and modelo != TipoTarea
                        and not permiso.codename.startswith("view_")
                    ):
                        continue

                    grupo_admin.permissions.add(permiso)

            grupos_creados += 1

            self.stdout.write(f"✓ Grupo creado: {grupo_admin.name}")

        grupo_profesor, creado = ModelosUsuarios.Grupo.objects.get_or_create(
            name=ModelosUsuarios.GruposBase.PROFESOR.value,
            descripcion="Provee todos los permisos relacionados a la carga de notas de acuerdo a los estudiantes asignados al usuario. También permite ver otros aspectos del sistema, pero no modificarlos",
        )

        if creado or grupo_profesor.permissions.count() == 0:
            for modelo in modelos:
                # se asignan todos los permisos de calificaciones
                if modelo in modelos_calificaciones:
                    content_type = ContentType.objects.get_for_model(modelo)

                    permisos = Permission.objects.filter(
                        content_type=content_type,
                    )

                    if modelo == TipoTarea:
                        permisos = permisos.filter(codename__startswith="view_")

                    for permiso in permisos:
                        grupo_profesor.permissions.add(permiso)

                # Solo permisos de lectura para todos los demás modelos
                else:
                    content_type = ContentType.objects.get_for_model(modelo)

                    permiso = Permission.objects.filter(
                        content_type=content_type, codename__startswith="view_"
                    ).first()

                    if permiso:
                        grupo_profesor.permissions.add(permiso)

            grupos_creados += 1

            self.stdout.write(f"✓ Grupo creado: {grupo_profesor.name}")

        self.stdout.write("Creando admin...")

        try:
            admin, creado = ModelosUsuarios.Usuario.objects.get_or_create(
                username="admin",
                email="",
                is_staff=True,
            )
            if creado:
                admin.set_password("admin")
                admin.grupos.add(grupo_admin)
                admin.save()
                self.stdout.write(self.style.SUCCESS("✓ Admin creado"))
        except IntegrityError:
            self.stdout.write("Admin ya creado")

        self.grupos_creados = grupos_creados

    def crear_tareas_por_defecto(self):
        self.stdout.write("Creando tareas por defecto...")
        tareas_creadas = 0

        if ModelosCalificaciones.TipoTarea.objects.count() > 0:
            self.stdout.write("Tareas por defecto ya creadas")
        else:
            t = ModelosCalificaciones.TipoTarea.objects.bulk_create(
                (ModelosCalificaciones.TipoTarea(nombre=tarea) for tarea in TAREAS),
                ignore_conflicts=True,
            )

            tareas_creadas = len(t)

            self.stdout.write(f"✓ {tareas_creadas} Tareas por defecto creadas")
        self.tareas_creadas = tareas_creadas
