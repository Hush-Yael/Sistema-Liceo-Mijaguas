from django.core.management.base import BaseCommand
from usuarios.models import Grupo, Usuario
from estudios.models import (
    Bachiller,
    Matricula,
    Nota,
    Seccion,
    Año,
    Materia,
    Estudiante,
    Profesor,
    Lapso,
    AñoMateria,
    ProfesorMateria,
)
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError


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


class Command(BaseCommand):
    help = "Llena la base de datos con datos estáticos (Años, materias, grupos, y un usuario admin)"

    def handle(self, *args, **options):
        self.stdout.write("Creando datos estáticos...")

        años_creados = 0

        for nombre, nombre_corto in AÑOS:
            _, created = Año.objects.get_or_create(
                nombre=nombre, nombre_corto=nombre_corto
            )
            if created:
                años_creados += 1
                self.stdout.write(f"✓ Año creado: {nombre}")

        materias_creadas = 0

        self.stdout.write("Creando secciones por defecto...")

        años = Año.objects.all()
        letras_secciones = ["A", "B", "C", "D", "E", "F", "G", "H", "U"]

        secciones_creadas = 0
        for año in años:
            for letra in letras_secciones:
                nombre = f"{año.nombre_corto} {letra}"
                _, created = Seccion.objects.get_or_create(
                    año=año,
                    letra=letra,
                    defaults={"nombre": nombre, "capacidad": 30},
                )
                if created:
                    secciones_creadas += 1
                    self.stdout.write(f"✓ Creada sección: {nombre}")

        self.stdout.write(f"✓ Total secciones creadas: {secciones_creadas}")

        for materia in MATERIAS:
            _, created = Materia.objects.get_or_create(nombre=materia)

            if created:
                materias_creadas += 1
                self.stdout.write(f"✓ Materia creada: {materia}")

        self.stdout.write("Asignando materias a años...")

        materias_asignadas = 0

        for materia in MATERIAS:
            for num in range(len(AÑOS)):
                # evitar asignar ciertas materias a todos los años, solo a algunos
                if (
                    materia in MATERIAS_PUNTUALES
                    and num not in MATERIAS_PUNTUALES[materia]
                ):
                    continue

                try:
                    _, asignada = AñoMateria.objects.get_or_create(
                        año=Año.objects.get(id=num),
                        materia=Materia.objects.get(nombre=materia),
                    )
                except:
                    continue

                if asignada:
                    self.stdout.write(f"✓ Asignada materia {materia} al año {num}")
                    materias_asignadas += 1

        self.stdout.write(f"✓ Total materias asignadas: {materias_asignadas}")

        self.stdout.write("Creando grupos...")

        grupos_creados = 0

        tablas_admin = [
            Usuario,
            Grupo,
            Nota,
            Año,
            Materia,
            Estudiante,
            Matricula,
            Profesor,
            Lapso,
            AñoMateria,
            ProfesorMateria,
            Seccion,
            Bachiller,
        ]

        grupo_admin, creado = Grupo.objects.get_or_create(
            name="Admin",
            descripcion="Provee todos los permisos de administración del sistema",
        )

        if creado or grupo_admin.permissions.count() == 0:
            for tabla in tablas_admin:
                content_type = ContentType.objects.get_for_model(tabla)

                permisos = Permission.objects.filter(content_type=content_type)

                for permiso in permisos:
                    grupo_admin.permissions.add(permiso)

            grupos_creados += 1

            self.stdout.write(f"✓ Grupo creado: {grupo_admin.name}")

        grupo_profesor, created = Grupo.objects.get_or_create(
            name="Profesor",
            descripcion="Provee todos los permisos relacionados a la carga de notas de acuerdo a los estudiantes asignados al usuario. También permite ver otros aspectos del sistema, pero no modificarlos",
        )

        if created or grupo_profesor.permissions.count() == 0:
            # no pueden ver usuarios
            tablas_admin.remove(Usuario)
            # se añaden todos los permisos de notas manualmente abajo
            tablas_admin.remove(Nota)

            nota_content_type = ContentType.objects.get_for_model(Nota)

            permisos_notas = Permission.objects.filter(
                content_type=nota_content_type,
            ).all()

            # todos los permisos de notas
            for permiso in permisos_notas:
                grupo_profesor.permissions.add(permiso)

            # solo lectura para todas las demás tablas
            for tabla in tablas_admin:
                content_type = ContentType.objects.get_for_model(tabla)

                permiso = Permission.objects.filter(
                    content_type=content_type, codename__startswith="view_"
                ).first()

                if permiso:
                    grupo_profesor.permissions.add(permiso)

            grupos_creados += 1

            self.stdout.write(f"✓ Grupo creado: {grupo_profesor.name}")

        self.stdout.write("Creando admin...")

        try:
            admin, creado = Usuario.objects.get_or_create(
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

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Datos estáticos creados exitosamente! "
                f"({años_creados} años, {materias_creadas} materias creadas, {materias_asignadas} materias asignadas, {secciones_creadas} secciones, {grupos_creados} grupos)"
            )
        )
