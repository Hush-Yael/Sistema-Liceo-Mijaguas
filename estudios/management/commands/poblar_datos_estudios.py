from django.core.management.base import BaseCommand
from estudios.models import (
    AñoAcademico,
    Materia,
    Profesor,
    Estudiante,
    LapsoAcademico,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Calificacion,
)
from datetime import date

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
    help = "Llena la base de datos con datos iniciales"

    def handle(self, *args, **options):
        self.stdout.write("Creando datos de ejemplo...")

        # Crear años académicos
        años = []
        for num, nombre in AÑOS:
            año, created = AñoAcademico.objects.get_or_create(
                numero_año=num, defaults={"nombre_año": nombre}
            )
            años.append(año)
            if created:
                self.stdout.write(f"Creado año: {nombre}")

        materias = []
        for codigo, nombre in MATERIAS:
            materia, created = Materia.objects.get_or_create(
                codigo_materia=codigo, defaults={"nombre_materia": nombre}
            )
            materias.append(materia)
            if created:
                self.stdout.write(f"Creada materia: {nombre}")

        # Crear profesores
        profesores_data = [
            ("María", "González", "maria.gonzalez@colegio.edu"),
            ("Carlos", "Rodríguez", "carlos.rodriguez@colegio.edu"),
            ("Ana", "Martínez", "ana.martinez@colegio.edu"),
        ]

        profesores = []
        for nombre, apellido, email in profesores_data:
            profesor, created = Profesor.objects.get_or_create(
                defaults={
                    "nombre": nombre,
                    "apellido": apellido,
                    "correo_electronico": email,
                },
            )
            profesores.append(profesor)
            if created:
                self.stdout.write(f"Creado profesor: {nombre} {apellido}")

        # Crear estudiantes
        estudiantes_data = [
            ("Juan", "Pérez", date(2010, 3, 15)),
            ("Laura", "Díaz", date(2010, 7, 22)),
            ("Miguel", "Silva", date(2010, 11, 30)),
        ]

        estudiantes = []
        for nombre, apellido, fecha_nac in estudiantes_data:
            estudiante, created = Estudiante.objects.get_or_create(
                defaults={
                    "nombre": nombre,
                    "apellido": apellido,
                    "fecha_nacimiento": fecha_nac,
                },
            )
            estudiantes.append(estudiante)
            if created:
                self.stdout.write(f"Creado estudiante: {nombre} {apellido}")

        # Crear lapsos para primer año
        primer_año = años[0]
        lapsos_data = [
            (1, "Primer Lapso", date(2024, 9, 1), date(2024, 11, 30)),
            (2, "Segundo Lapso", date(2024, 12, 1), date(2025, 2, 28)),
            (3, "Tercer Lapso", date(2025, 3, 1), date(2025, 6, 30)),
        ]

        lapsos = []
        for num, nombre, inicio, fin in lapsos_data:
            lapso, created = LapsoAcademico.objects.get_or_create(
                año=primer_año,
                numero_lapso=num,
                defaults={
                    "nombre_lapso": nombre,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                },
            )
            lapsos.append(lapso)
            if created:
                self.stdout.write(f"Creado lapso: {nombre}")

        # Asignar materias al primer año
        for materia in materias:
            _, created = AñoMateria.objects.get_or_create(
                año=primer_año, materia=materia
            )
            if created:
                self.stdout.write(
                    f"Asignada materia {materia.nombre_materia} a {primer_año.nombre_año}"
                )

        # Asignar profesores a materias
        asignaciones = [
            (profesores[0], materias[0], primer_año, True),  # María enseña Matemáticas
            (profesores[1], materias[1], primer_año, True),  # Carlos enseña Lengua
            (profesores[2], materias[2], primer_año, True),  # Ana enseña Ciencias
        ]

        for profesor, materia, año, principal in asignaciones:
            _, created = ProfesorMateria.objects.get_or_create(
                profesor=profesor,
                materia=materia,
                año=año,
                defaults={"es_profesor_principal": principal},
            )
            if created:
                self.stdout.write(
                    f"Asignado profesor {profesor} a {materia.nombre_materia}"
                )

        # Matricular estudiantes
        for estudiante in estudiantes:
            _, created = Matricula.objects.get_or_create(
                estudiante=estudiante, año=primer_año, defaults={"estado": "activo"}
            )
            if created:
                self.stdout.write(
                    f"Matriculado estudiante {estudiante} en {primer_año.nombre_año}"
                )

        # Insertar calificaciones de ejemplo
        calificaciones_data = [
            (estudiantes[0], materias[0], lapsos[0], 18.5),  # Juan en Matemáticas
            (estudiantes[0], materias[1], lapsos[0], 16.0),  # Juan en Lengua
            (estudiantes[1], materias[0], lapsos[0], 19.0),  # Laura en Matemáticas
        ]

        for estudiante, materia, lapso, calificacion in calificaciones_data:
            _, created = Calificacion.objects.get_or_create(
                estudiante=estudiante,
                materia=materia,
                lapso=lapso,
                defaults={"valor_calificacion": calificacion},
            )
            if created:
                self.stdout.write(
                    f"Creada calificación para {estudiante} en {materia.nombre_materia}: {calificacion}"
                )

        self.stdout.write(self.style.SUCCESS("¡Datos de ejemplo creados exitosamente!"))
