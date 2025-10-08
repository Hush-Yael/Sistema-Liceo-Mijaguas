from django.core.management.base import BaseCommand
from estudios.models import AñoAcademico, Materia


AÑOS = [
    (1, "Primer Año"),
    (2, "Segundo Año"),
    (3, "Tercer Año"),
    (4, "Cuarto Año"),
    (5, "Quinto Año"),
]

MATERIAS = [
    ("MAT", "Matemática"),
    ("CAS", "Castellano"),
    ("CIE", "Ciencias Naturales"),
    ("ING", "Inglés"),
    ("EDF", "Educación Física"),
    ("GHC", "G.H.C"),
    ("CRP", "C.R.P"),
    ("QUI", "Química"),
    ("ORI", "Orientación"),
    ("FIS", "Física"),
    ("PRE", "Premilitar"),
]


class Command(BaseCommand):
    help = "Llena la base de datos con datos estáticos (años académicos y materias)"

    def handle(self, *args, **options):
        self.stdout.write("Creando datos estáticos...")

        años_creados = 0

        for num, nombre in AÑOS:
            _, created = AñoAcademico.objects.get_or_create(
                numero_año=num, defaults={"nombre_año": nombre}
            )
            if created:
                años_creados += 1
                self.stdout.write(f"✓ Año creado: {nombre}")

        materias_creadas = 0

        for codigo, nombre in MATERIAS:
            _, created = Materia.objects.get_or_create(
                codigo_materia=codigo, defaults={"nombre_materia": nombre}
            )
            if created:
                materias_creadas += 1
                self.stdout.write(f"✓ Materia creada: {nombre}")

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Datos estáticos creados exitosamente! "
                f"({años_creados} años, {materias_creadas} materias)"
            )
        )
