from typing import OrderedDict
from django.core.management.base import BaseCommand
from estudios.models import (
    Seccion,
    Año,
    Materia,
    Profesor,
    Estudiante,
    Lapso,
    AñoMateria,
    ProfesorMateria,
    Matricula,
    Nota,
)
from datetime import date
from faker import Faker
import random

from usuarios.models import User
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "LLena la base de datos con datos de ejemplo usando Faker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker("es_ES")  # Español de España
        self.faker.seed_instance(1234)  # Para resultados consistentes

    def add_arguments(self, parser):
        parser.add_argument(
            "--año",
            type=int,
            default=1,
            help="Número del año para el cual crear los datos (1-5)",
        )

        parser.add_argument(
            "--limpiar-todo",
            action="store_true",
            help="Eliminar todos los datos de ejemplo existentes",
        )

        parser.add_argument(
            "--profesores",
            action="store_true",
            help="Crear solo profesores",
        )

        parser.add_argument(
            "--estudiantes",
            action="store_true",
            help="Crear solo estudiantes",
        )

        parser.add_argument(
            "--lapsos",
            action="store_true",
            help="Crear solo lapsos",
        )

        parser.add_argument(
            "--asignaciones",
            action="store_true",
            help="Crear solo asignaciones de materias y profesores",
        )

        parser.add_argument(
            "--matriculas",
            action="store_true",
            help="Crear solo matrículas",
        )

        parser.add_argument(
            "--notas",
            action="store_true",
            help="Crear solo notas",
        )

        parser.add_argument(
            "--todo",
            action="store_true",
            help="Crear todos los datos de ejemplo (por defecto si no se especifica nada)",
        )

        parser.add_argument(
            "--cantidad-estudiantes",
            type=int,
            default=20,
            help="Cantidad de estudiantes a crear (por defecto: 20)",
        )

        parser.add_argument(
            "--cantidad-profesores",
            type=int,
            default=8,
            help="Cantidad de profesores a crear (por defecto: 8)",
        )

        parser.add_argument(
            "--secciones",
            action="store_true",
            help="Crear solo secciones",
        )

        parser.add_argument(
            "--secciones-por-año",
            type=int,
            default=3,
            help="Número de secciones a crear por año (por defecto: 3)",
        )

    def handle(self, *args, **options):
        añonumero = options["año"]
        limpiar_todo = options["limpiar_todo"]

        # Determinar qué acciones ejecutar
        acciones = {
            "profesores": options["profesores"],
            "estudiantes": options["estudiantes"],
            "lapsos": options["lapsos"],
            "asignaciones": options["asignaciones"],
            "matriculas": options["matriculas"],
            "notas": options["notas"],
        }

        # Si no se especifica ninguna acción particular, hacer todo
        hacer_todo = options["todo"] or not any(acciones.values())

        if limpiar_todo:
            self.limpiar_todos_datos_ejemplo()

        # Obtener el año
        try:
            año = Año.objects.get(numero_año=añonumero)
        except Año.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"No existe el año número {añonumero}. "
                    f"Ejecuta primero poblar_datos_estudios"
                )
            )
            return

        # Ejecutar acciones
        if hacer_todo or acciones["profesores"]:
            self.crear_profesores(options["cantidad_profesores"])

        if hacer_todo or acciones["estudiantes"]:
            self.crear_estudiantes(options["cantidad_estudiantes"])

        if hacer_todo or acciones["lapsos"]:
            self.crear_lapsos()

        if hacer_todo or acciones["asignaciones"]:
            self.asignar_materias_a_año(año)
            profesores = Profesor.objects.all()
            self.asignar_profesores_a_materias(profesores, año)

        if hacer_todo or acciones["matriculas"]:
            estudiantes = Estudiante.objects.all()
            self.matricular_estudiantes(estudiantes, año)

        if hacer_todo or acciones["notas"]:
            estudiantes = Estudiante.objects.all()
            lapsos = Lapso.objects.all()
            self.crear_notas(estudiantes, lapsos)
        acciones["secciones"] = options["secciones"]

        if hacer_todo or acciones["secciones"]:
            self.crear_secciones(año, options["secciones_por_año"])

            self.stdout.write(self.style.SUCCESS("¡Operación completada exitosamente!"))

    def limpiar_todos_datos_ejemplo(self):
        """Elimina todos los datos de ejemplo existentes"""
        self.stdout.write("Eliminando todos los datos de ejemplo existentes...")

        modelos_a_limpiar = [
            Nota,
            Matricula,
            ProfesorMateria,
            AñoMateria,
            Lapso,
            Estudiante,
            Profesor,
        ]

        for modelo in modelos_a_limpiar:
            count, _ = modelo.objects.all().delete()
            if count > 0:
                self.stdout.write(
                    f"✓ Eliminados {count} registros de {modelo.__name__}"
                )

    def limpiar_por_tipo(self, tipo):
        """Elimina datos específicos por tipo"""
        modelos = {
            "profesores": [ProfesorMateria, Profesor],
            "estudiantes": [Nota, Matricula, Estudiante],
            "lapsos": [Nota, Lapso],
            "asignaciones": [ProfesorMateria, AñoMateria],
            "matriculas": [Nota, Matricula],
            "notas": [Nota],
        }

        if tipo in modelos:
            for modelo in modelos[tipo]:
                count, _ = modelo.objects.all().delete()
                if count > 0:
                    self.stdout.write(
                        f"✓ Eliminados {count} registros de {modelo.__name__}"
                    )

    def crear_profesores(self, cantidad):
        """Crear profesores usando Faker"""
        self.stdout.write(f"Creando {cantidad} profesores...")

        profesores_creados = 0
        for i in range(cantidad + 1):
            # Verificar si ya existe
            if Profesor.objects.filter(cedula=i).exists():
                continue

            # Generar datos con Faker
            nombre = self.faker.first_name()
            apellido = self.faker.last_name()
            email = f"{nombre.lower()}.{apellido.lower()}@colegio.edu"

            # Asegurar que el email sea único
            contador_email = 1
            email_original = email

            while User.objects.filter(email=email).exists():
                email = f"{email_original.split('@')[0]}{contador_email}@colegio.edu"
                contador_email += 1

            grupo_prof = Group.objects.get(name="Profesor")

            prof_usuario = User.objects.create(
                username=email.split("@")[0],
                email=email,
                is_staff=True,
            )

            prof_usuario.set_password("1234")
            prof_usuario.save()

            Profesor.objects.create(
                cedula=i,
                nombres=nombre,
                apellidos=apellido,
                telefono=self.faker.random_element(
                    [None, "", self.faker.phone_number()]
                ),
                fecha_ingreso=self.faker.date_between(
                    start_date="-10y", end_date="today"
                ),
                esta_activo=self.faker.boolean(chance_of_getting_true=90),
                usuario=prof_usuario,
            )

            prof_usuario.groups.add(grupo_prof)

            profesores_creados += 1
            self.stdout.write(f"✓ Creado profesor: {nombre} {apellido} ({i})")

        self.stdout.write(f"✓ Total profesores creados: {profesores_creados}")

    def crear_estudiantes(self, cantidad):
        """Crear estudiantes usando Faker"""
        self.stdout.write(f"Creando {cantidad} estudiantes...")

        estudiantes_creados = 0
        for i in range(cantidad + 1):
            # Verificar si ya existe
            if Estudiante.objects.filter(cedula=i).exists():
                continue

            # Generar datos con Faker (edades entre 13-18 años para secundaria)
            nombre = self.faker.first_name()
            apellido = self.faker.last_name()

            # Fecha de nacimiento para estudiantes de secundaria (13-18 años)
            fecha_nacimiento = self.faker.date_of_birth(minimum_age=13, maximum_age=18)

            Estudiante.objects.create(
                cedula=i,
                nombres=nombre,
                apellidos=apellido,
                fecha_nacimiento=fecha_nacimiento,
                fecha_ingreso=self.faker.date_between(
                    start_date="-2y", end_date="today"
                ),
                estado=self.faker.random_element(
                    OrderedDict(
                        [("activo", 0.8), ("inactivo", 0.1), ("graduado", 0.1)]
                    ),
                ),
            )

            estudiantes_creados += 1
            if estudiantes_creados % 10 == 0:  # Mostrar progreso cada 10 estudiantes
                self.stdout.write(f"✓ Creados {estudiantes_creados} estudiantes...")

        self.stdout.write(f"✓ Total estudiantes creados: {estudiantes_creados}")

    def crear_lapsos(self):
        # Determinar el año base según el número del año
        año_base = date.today().year

        lapsos_data = [
            (1, "Primer Lapso", date(año_base, 9, 1), date(año_base, 11, 30)),
            (2, "Segundo Lapso", date(año_base, 12, 1), date(año_base + 1, 2, 28)),
            (3, "Tercer Lapso", date(año_base + 1, 3, 1), date(año_base + 1, 6, 30)),
        ]

        lapsos_creados = 0
        for num, nombre, inicio, fin in lapsos_data:
            _, created = Lapso.objects.get_or_create(
                numero_lapso=num,
                defaults={
                    "nombre_lapso": nombre,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                },
            )
            if created:
                lapsos_creados += 1
                self.stdout.write(f"✓ Creado lapso: {nombre}")

        self.stdout.write(f"✓ Total lapsos creados: {lapsos_creados}")

    def asignar_materias_a_año(self, año):
        """Asignar todas las materias al año"""
        self.stdout.write(f"Asignando materias a {año.nombre_año}...")

        materias = Materia.objects.all()
        asignaciones_creadas = 0

        for materia in materias:
            _, created = AñoMateria.objects.get_or_create(año=año, materia=materia)
            if created:
                asignaciones_creadas += 1

        self.stdout.write(f"✓ Asignadas {asignaciones_creadas} materias al año")

    def asignar_profesores_a_materias(self, profesores, año):
        """Asignar profesores a materias por sección"""
        self.stdout.write("Asignando profesores a materias por sección...")

        materias = Materia.objects.all()
        secciones = Seccion.objects.filter(año=año)
        asignaciones_creadas = 0

        # Para cada materia y sección, asignar 1-2 profesores
        for materia in materias:
            for seccion in secciones:
                # Seleccionar 1-2 profesores aleatorios
                num_profesores = random.randint(1, 2)
                profesores_asignados = random.sample(
                    list(profesores), min(num_profesores, len(profesores))
                )

                for i, profesor in enumerate(profesores_asignados):
                    es_principal = i == 0  # El primero es principal

                    _, created = ProfesorMateria.objects.get_or_create(
                        profesor=profesor,
                        materia=materia,
                        seccion=seccion,
                    )
                    if created:
                        asignaciones_creadas += 1
                        tipo = "principal" if es_principal else "secundario"
                        self.stdout.write(
                            f"✓ {profesor} → {materia.nombre_materia} - {seccion.letra_seccion} ({tipo})"
                        )

        self.stdout.write(f"✓ Total asignaciones creadas: {asignaciones_creadas}")

    def matricular_estudiantes(self, estudiantes, año):
        """Matricular estudiantes en secciones del año académico"""
        self.stdout.write(
            f"Matriculando estudiantes en secciones de {año.nombre_año}..."
        )

        secciones = Seccion.objects.filter(año=año)
        if not secciones.exists():
            self.stdout.write(
                self.style.ERROR(
                    "No hay secciones creadas para este año. Ejecuta --secciones primero."
                )
            )
            return

        matriculas_creadas = 0

        # Distribuir estudiantes entre secciones
        estudiantes_por_seccion = len(estudiantes) // len(secciones)

        for i, seccion in enumerate(secciones):
            inicio = i * estudiantes_por_seccion
            fin = inicio + estudiantes_por_seccion

            # Para la última sección, tomar todos los estudiantes restantes
            if i == len(secciones) - 1:
                estudiantes_seccion = estudiantes[inicio:]
            else:
                estudiantes_seccion = estudiantes[inicio:fin]

            for estudiante in estudiantes_seccion:
                _, created = Matricula.objects.get_or_create(
                    estudiante=estudiante,
                    año=año,
                    defaults={
                        "seccion": seccion,
                        "fecha_matricula": self.faker.date_between(
                            start_date="-1y", end_date="today"
                        ),
                    },
                )
                if created:
                    matriculas_creadas += 1

        self.stdout.write(f"✓ Total matriculas creadas: {matriculas_creadas}")

    def crear_notas(self, estudiantes, lapsos):
        """Crear notas por sección"""
        self.stdout.write("Creando notas por sección...")

        materias = Materia.objects.all()
        notas_creadas = 0

        for estudiante in estudiantes:
            # Obtener la matrícula del estudiante para saber su sección
            try:
                matricula = Matricula.objects.get(
                    estudiante=estudiante,
                )
                seccion_estudiante = matricula.seccion
            except Matricula.DoesNotExist:
                continue

            for lapso in lapsos:
                for materia in materias:
                    # Verificar si ya existe calificación
                    if Nota.objects.filter(
                        estudiante=estudiante, materia=materia, lapso=lapso
                    ).exists():
                        continue

                    # Generar calificación realista
                    if random.random() < 0.05:  # 5% de probabilidad de nota baja
                        nota = round(random.uniform(5.0, 9.9), 1)
                    else:
                        nota = round(random.uniform(10.0, 19.9), 1)

                    # Algunas notas pueden tener comentarios
                    comentarios = None
                    if random.random() < 0.3:  # 30% de probabilidad de comentario
                        comentarios = self.faker.sentence()

                    Nota.objects.create(
                        estudiante=estudiante,
                        materia=materia,
                        lapso=lapso,
                        seccion=seccion_estudiante,
                        valor_nota=nota,
                        fecha_nota=self.faker.date_between(
                            start_date=lapso.fecha_inicio, end_date=lapso.fecha_fin
                        ),
                        comentarios=comentarios,
                    )

                    notas_creadas += 1

                    if notas_creadas % 100 == 0:  # Mostrar progreso
                        self.stdout.write(f"✓ Creadas {notas_creadas} notas...")

        self.stdout.write(f"✓ Total notas creadas: {notas_creadas}")

    def crear_secciones(self, año, cantidad_secciones):
        """Crear secciones para el año académico"""
        self.stdout.write(
            f"Creando {cantidad_secciones} secciones para {año.nombre_año}..."
        )

        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        secciones_creadas = 0

        for i in range(cantidad_secciones):
            letra = letras[i]
            nombre_seccion = f"{año.nombre_año} - Sección {letra}"

            _, creada = Seccion.objects.get_or_create(
                año=año,
                letra_seccion=letra,
                defaults={"nombre_seccion": nombre_seccion, "capacidad_maxima": 30},
            )

            if creada:
                secciones_creadas += 1
                self.stdout.write(f"✓ Creada sección: {nombre_seccion}")

        self.stdout.write(f"✓ Total secciones creadas: {secciones_creadas}")
