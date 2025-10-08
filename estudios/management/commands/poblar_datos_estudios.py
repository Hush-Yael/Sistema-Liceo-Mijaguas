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

        for materia in MATERIAS:
            _, created = Materia.objects.get_or_create(
                defaults={"nombre_materia": materia}
            )
            if created:
                materias_creadas += 1
                self.stdout.write(f"✓ Materia creada: {materia}")

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Datos estáticos creados exitosamente! "
                f"({años_creados} años, {materias_creadas} materias)"
            )
        )
