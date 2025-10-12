from django.core.management.base import BaseCommand
from usuarios.models import User
from estudios.models import (
    Calificacion,
    AñoAcademico,
    Materia,
    Estudiante,
    Profesor,
    LapsoAcademico,
    AñoMateria,
    ProfesorMateria,
)
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError


AÑOS = [
    (1, "Primer Año", "1ero"),
    (2, "Segundo Año", "2do"),
    (3, "Tercer Año", "3ero"),
    (4, "Cuarto Año", "4to"),
    (5, "Quinto Año", "5to"),
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


class Command(BaseCommand):
    help = "Llena la base de datos con datos estáticos (años académicos, materias, grupos, y un usuario admin)"

    def handle(self, *args, **options):
        self.stdout.write("Creando datos estáticos...")

        años_creados = 0

        for num, nombre, nombre_corto in AÑOS:
            _, created = AñoAcademico.objects.get_or_create(
                numero_año=num, nombre_año=nombre, nombre_año_corto=nombre_corto
            )
            if created:
                años_creados += 1
                self.stdout.write(f"✓ Año creado: {nombre}")

        materias_creadas = 0

        for materia in MATERIAS:
            _, created = Materia.objects.get_or_create(nombre_materia=materia)

            if created:
                materias_creadas += 1
                self.stdout.write(f"✓ Materia creada: {materia}")

        grupos_creados = 0

        self.stdout.write("Creando grupos...")

        grupo_profesor, created = Group.objects.get_or_create(name="Profesor")

        if created:
            calificacion_content_type = ContentType.objects.get_for_model(Calificacion)

            permisos_calificaciones = Permission.objects.filter(
                content_type=calificacion_content_type,
            ).all()

            # todos los permisos de calificaciones
            for permiso in permisos_calificaciones:
                grupo_profesor.permissions.add(permiso)

            tablas_solo_lectura = (
                AñoAcademico,
                Materia,
                Estudiante,
                Profesor,
                LapsoAcademico,
                AñoMateria,
                ProfesorMateria,
            )

            # solo lectura para todas las demás tablas
            for tabla in tablas_solo_lectura:
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
            User.objects.get_or_create(
                username="admin",
                email="",
                is_superuser=True,
                password="admin",
            )
            self.stdout.write(self.style.SUCCESS("✓ Admin creado"))
        except IntegrityError:
            self.stdout.write("Admin ya creado")

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Datos estáticos creados exitosamente! "
                f"({años_creados} años, {materias_creadas} materias, {grupos_creados} grupos)"
            )
        )
