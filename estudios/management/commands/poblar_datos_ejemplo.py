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


class Command(BaseCommand):
    help = "Llena la base de datos con datos dinámicos (profesores, estudiantes, lapsos, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--año",
            type=int,
            default=1,
            help="Número del año académico para el cual crear los datos (1-5)",
        )
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Eliminar datos existentes antes de crear nuevos",
        )

    def handle(self, *args, **options):
        año_numero = options["año"]
        limpiar_datos = options["limpiar"]

        if limpiar_datos:
            self.limpiar_datos_ejemplo()

        self.stdout.write(f"Creando datos dinámicos para {año_numero}° año...")

        # Verificar que existe el año académico
        try:
            año_academico = AñoAcademico.objects.get(numero_año=año_numero)
        except AñoAcademico.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"No existe el año académico número {año_numero}. "
                    f"Ejecuta primero poblar_datos_ejemplo."
                )
            )
            return

        # Verificar que existen materias
        if not Materia.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    "No existen materias. Ejecuta primero poblar_datos_ejemplo."
                )
            )
            return

        # Crear profesores
        profesores = self.crear_profesores()

        # Crear estudiantes
        estudiantes = self.crear_estudiantes()

        # Crear lapsos académicos
        lapsos = self.crear_lapsos(año_academico)

        # Asignar materias al año
        self.asignar_materias_a_año(año_academico)

        # Asignar profesores a materias
        self.asignar_profesores_a_materias(profesores, año_academico)

        # Matricular estudiantes
        self.matricular_estudiantes(estudiantes, año_academico)

        # Crear calificaciones de ejemplo
        self.crear_calificaciones(estudiantes, lapsos)

        self.stdout.write(self.style.SUCCESS("¡Datos dinámicos creados exitosamente!"))

    def limpiar_datos_ejemplo(self):
        """Elimina todos los datos dinámicos existentes"""
        self.stdout.write("Eliminando datos dinámicos existentes...")

        modelos_a_limpiar = [
            Profesor,
            Estudiante,
            LapsoAcademico,
            AñoMateria,
            ProfesorMateria,
            Matricula,
            Calificacion,
        ]

        for modelo in modelos_a_limpiar:
            count, _ = modelo.objects.all().delete()
            if count > 0:
                self.stdout.write(
                    f"✓ Eliminados {count} registros de {modelo.__name__}"
                )

    def crear_profesores(self):
        """Crear profesores de ejemplo"""
        profesores_data = [
            ("María", "González", "maria.gonzalez@colegio.edu"),
            ("Carlos", "Rodríguez", "carlos.rodriguez@colegio.edu"),
            ("Ana", "Martínez", "ana.martinez@colegio.edu"),
            ("Pedro", "López", "pedro.lopez@colegio.edu"),
            ("Isabel", "Fernández", "isabel.fernandez@colegio.edu"),
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
                self.stdout.write(f"✓ Creado profesor: {nombre} {apellido}")

        return profesores

    def crear_estudiantes(self):
        """Crear estudiantes de ejemplo"""
        estudiantes_data = [
            ("Juan", "Pérez", date(2010, 3, 15)),
            ("Laura", "Díaz", date(2010, 7, 22)),
            ("Miguel", "Silva", date(2010, 11, 30)),
            ("Sofía", "Ramírez", date(2010, 5, 10)),
            ("Diego", "Hernández", date(2010, 9, 18)),
            ("Valentina", "Gómez", date(2010, 1, 25)),
            ("Andrés", "Castillo", date(2010, 12, 5)),
            ("Camila", "Rojas", date(2010, 4, 30)),
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
                self.stdout.write(f"✓ Creado estudiante: {nombre} {apellido}")

        return estudiantes

    def crear_lapsos(self, año_academico):
        """Crear lapsos académicos para el año especificado"""
        # Determinar el año base según el número del año académico
        año_base = 2023 + año_academico.numero_año

        lapsos_data = [
            (1, "Primer Lapso", date(año_base, 9, 1), date(año_base, 11, 30)),
            (2, "Segundo Lapso", date(año_base, 12, 1), date(año_base + 1, 2, 28)),
            (3, "Tercer Lapso", date(año_base + 1, 3, 1), date(año_base + 1, 6, 30)),
        ]

        lapsos = []
        for num, nombre, inicio, fin in lapsos_data:
            lapso, created = LapsoAcademico.objects.get_or_create(
                año=año_academico,
                numero_lapso=num,
                defaults={
                    "nombre_lapso": nombre,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                },
            )
            lapsos.append(lapso)
            if created:
                self.stdout.write(f"✓ Creado lapso: {nombre}")

        return lapsos

    def asignar_materias_a_año(self, año_academico):
        """Asignar todas las materias al año académico"""
        materias = Materia.objects.all()
        asignaciones_creadas = 0

        for materia in materias:
            _, created = AñoMateria.objects.get_or_create(
                año=año_academico, materia=materia
            )
            if created:
                asignaciones_creadas += 1

        if asignaciones_creadas > 0:
            self.stdout.write(f"✓ Asignadas {asignaciones_creadas} materias al año")

    def asignar_profesores_a_materias(self, profesores, año_academico):
        """Asignar profesores a materias específicas"""
        materias = Materia.objects.all()
        asignaciones = [
            (profesores[0], materias[0], True),  # María - Matemáticas (Principal)
            (profesores[1], materias[1], True),  # Carlos - Lengua (Principal)
            (profesores[2], materias[2], True),  # Ana - Ciencias Naturales (Principal)
            (profesores[3], materias[3], True),  # Pedro - Ciencias Sociales (Principal)
            (profesores[4], materias[4], True),  # Isabel - Inglés (Principal)
            (
                profesores[0],
                materias[5],
                False,
            ),  # María - Educación Física (Secundario)
            (profesores[1], materias[6], False),  # Carlos - Arte (Secundario)
        ]

        asignaciones_creadas = 0
        for profesor, materia, principal in asignaciones:
            _, created = ProfesorMateria.objects.get_or_create(
                profesor=profesor,
                materia=materia,
                año=año_academico,
                defaults={"es_profesor_principal": principal},
            )
            if created:
                asignaciones_creadas += 1
                tipo = "principal" if principal else "secundario"
                self.stdout.write(
                    f"✓ Asignado {profesor} a {materia.nombre_materia} ({tipo})"
                )

    def matricular_estudiantes(self, estudiantes, año_academico):
        """Matricular estudiantes en el año académico"""
        matriculas_creadas = 0

        for estudiante in estudiantes:
            _, created = Matricula.objects.get_or_create(
                estudiante=estudiante, año=año_academico, defaults={"estado": "activo"}
            )
            if created:
                matriculas_creadas += 1

        if matriculas_creadas > 0:
            self.stdout.write(f"✓ Matriculados {matriculas_creadas} estudiantes")

    def crear_calificaciones(self, estudiantes, lapsos):
        """Crear calificaciones de ejemplo para los estudiantes"""
        materias = Materia.objects.all()
        primer_lapso = lapsos[0]  # Usar solo el primer lapso para ejemplo

        # Crear algunas calificaciones de ejemplo
        calificaciones_ejemplo = [
            (estudiantes[0], materias[0], 18.5),  # Juan - Matemáticas
            (estudiantes[0], materias[1], 16.0),  # Juan - Lengua
            (estudiantes[0], materias[2], 17.5),  # Juan - Ciencias
            (estudiantes[1], materias[0], 19.0),  # Laura - Matemáticas
            (estudiantes[1], materias[1], 18.0),  # Laura - Lengua
            (estudiantes[2], materias[0], 15.5),  # Miguel - Matemáticas
            (estudiantes[2], materias[3], 16.5),  # Miguel - Ciencias Sociales
        ]

        calificaciones_creadas = 0
        for estudiante, materia, nota in calificaciones_ejemplo:
            _, created = Calificacion.objects.get_or_create(
                estudiante=estudiante,
                materia=materia,
                lapso=primer_lapso,
                defaults={"valor_calificacion": nota},
            )
            if created:
                calificaciones_creadas += 1

        if calificaciones_creadas > 0:
            self.stdout.write(
                f"✓ Creadas {calificaciones_creadas} calificaciones de ejemplo"
            )
