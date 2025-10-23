from typing import OrderedDict
from django.core.management.base import BaseCommand
from estudios.models import (
    Bachiller,
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
from django.db import connection


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
            help="Número del año objetivo, al cual asignar datos específicos",
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
            "--lapsos-año",
            type=int,
            # año actual
            default=date.today().year,
            help="El año (fecha) para crear los lapsos",
        )

        parser.add_argument(
            "--lapso",
            type=int,
            help="Indicar el id del lapso para las acciones que lo requieran",
        )

        parser.add_argument(
            "--asignar-materias",
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
            "--cantidad-notas",
            type=int,
            default=1,
            help="Cantidad de notas a crear (por defecto: 1)",
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

    def handle(self, *args, **options):
        año_objetivo = options["año"]
        limpiar_todo = options["limpiar_todo"]
        hacer_todo = options["todo"]

        if limpiar_todo:
            self.limpiar_datos()

        # Determinar qué acciones ejecutar
        acciones = {
            "profesores": options["profesores"],
            "estudiantes": options["estudiantes"],
            "lapsos": options["lapsos"],
            "asignar-materias": options["asignar_materias"],
            "matriculas": options["matriculas"],
            "notas": options["notas"],
        }

        # no se indicaron acciones
        if not limpiar_todo and not hacer_todo and not any(acciones.values()):
            return self.stdout.write(
                self.style.ERROR("No se especificaron acciones a ejecutar.")
            )

        # Ejecutar acciones
        if hacer_todo or acciones["profesores"]:
            self.crear_profesores(options["cantidad_profesores"])

        if hacer_todo or acciones["estudiantes"]:
            self.crear_estudiantes(options["cantidad_estudiantes"])

        if hacer_todo or acciones["lapsos"]:
            self.crear_lapsos(options["lapsos_año"])

        if hacer_todo or acciones["asignar-materias"]:
            profesores = Profesor.objects.all()
            self.asignar_profesores_a_materias(profesores, año_objetivo)

        if hacer_todo or acciones["matriculas"]:
            estudiantes = Estudiante.objects.all()
            self.matricular_estudiantes(estudiantes, año_objetivo, options["lapso"])

        if hacer_todo or acciones["notas"]:
            estudiantes = Estudiante.objects.all()

            if estudiantes.first() is None:
                return self.stdout.write(
                    self.style.ERROR("No se han añadido estudiantes")
                )

            cantidad = options["cantidad_notas"]
            self.crear_notas(estudiantes, año_objetivo, cantidad, options["lapso"])

    def obtener_año_objetivo(self, año_objetivo: int):
        if año_objetivo is None:
            return self.stdout.write(
                self.style.ERROR(
                    "Debes proporcionar el número del año objetivo para esta operación."
                )
            )

        try:
            return Año.objects.get(numero_año=año_objetivo)
        except Año.DoesNotExist:
            return self.stdout.write(
                self.style.ERROR(
                    f"No existe el año número {año_objetivo}. "
                    f"Ejecuta primero poblar_datos_estudios para crear los años por defecto."
                )
            )

    def obtener_lapso_objetivo(self, lapso_objetivo: int):
        if lapso_objetivo is None:
            return self.stdout.write(
                self.style.ERROR("No se proporcionó un lapso para la operación.")
            )

        try:
            return Lapso.objects.get(pk=lapso_objetivo)
        except Lapso.DoesNotExist:
            return self.stdout.write(
                self.style.ERROR("No se encontró el lapso con el id proporcionado.")
            )

    def limpiar_datos(self):
        """Elimina todos los datos de ejemplo existentes"""
        self.stdout.write("Eliminando todos los datos dinámicos existentes...")

        modelos_a_limpiar = [
            Nota,
            Matricula,
            ProfesorMateria,
            Lapso,
            Estudiante,
            Profesor,
            Bachiller,
        ]

        for modelo in modelos_a_limpiar:
            count, _ = modelo.objects.all().delete()
            if count > 0:
                self.stdout.write(
                    f"✓ Eliminados {count} registros de {modelo.__name__}"
                )

            connection.cursor().execute(
                f"UPDATE SQLITE_SEQUENCE SET seq=0 WHERE name='{modelo._meta.db_table}';",
            )

    def limpiar_por_tipo(self, tipo):
        """Elimina datos específicos por tipo"""
        modelos = {
            "profesores": [ProfesorMateria, Profesor],
            "estudiantes": [Nota, Matricula, Estudiante],
            "lapsos": [Nota, Lapso],
            "asignar-materias": [ProfesorMateria, AñoMateria],
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
        for i in range(cantidad):
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
        for i in range(cantidad):
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
            )

            estudiantes_creados += 1
            if estudiantes_creados % 10 == 0:  # Mostrar progreso cada 10 estudiantes
                self.stdout.write(f"✓ Creados {estudiantes_creados} estudiantes...")

        self.stdout.write(f"✓ Total estudiantes creados: {estudiantes_creados}")

    def crear_lapsos(self, año):
        lapsos_data = [
            (1, f"{año}-I", date(año, 1, 9), date(año, 3, 31)),
            (
                2,
                f"{año}-II",
                date(año, 4, 1),
                date(año, 5, 28),
            ),
            (
                3,
                f"{año}-III",
                date(año, 5, 29),
                date(año, 6, 30),
            ),
        ]

        lapsos_creados = 0
        for num, nombre, inicio, fin in lapsos_data:
            _, creado = Lapso.objects.get_or_create(
                numero_lapso=num,
                defaults={
                    "nombre_lapso": nombre,
                    "fecha_inicio": inicio,
                    "fecha_fin": fin,
                },
            )
            if creado:
                lapsos_creados += 1
                self.stdout.write(f"✓ Creado lapso: {nombre}")

        self.stdout.write(f"✓ Total lapsos creados: {lapsos_creados}")

    def asignar_profesores_a_materias(self, profesores, año_objetivo: int):
        año = self.obtener_año_objetivo(año_objetivo)
        if año is None:
            return

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

    def matricular_estudiantes(
        self, estudiantes, año_objetivo: int, lapso_objetivo: int
    ):
        """Matricular estudiantes en secciones del año académico"""
        self.stdout.write(
            f"Matriculando estudiantes en secciones del año {año_objetivo}..."
        )

        año = self.obtener_año_objetivo(año_objetivo)
        lapso = self.obtener_lapso_objetivo(lapso_objetivo)

        if año is None or lapso is None:
            return

        secciones = Seccion.objects.filter(año=año)
        if not secciones.exists():
            self.stdout.write(
                self.style.ERROR(
                    "No hay secciones creadas para este año. Ejecuta --secciones primero."
                )
            )
            return

        matriculas_creadas = 0
        ya_matriculados = 0

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
                _, creada = Matricula.objects.get_or_create(
                    estudiante=estudiante,
                    lapso=lapso,
                    defaults={
                        "seccion": seccion,
                        "estado": self.faker.random_element(
                            OrderedDict(
                                [
                                    ("activo", 0.9),
                                    ("inactivo", 0.1),
                                ]
                            ),
                        ),
                    },
                )
                if creada:
                    matriculas_creadas += 1
                else:
                    ya_matriculados += 1

        if ya_matriculados > 0:
            self.stdout.write(
                f"Ya matriculados con los parámetros indicados: {ya_matriculados}"
            )
        if matriculas_creadas > 0:
            self.stdout.write(f"✓ Total matriculas creadas: {matriculas_creadas}")

    def crear_notas(
        self, estudiantes, año_objetivo: int, cantidad_notas: int, lapso_objetivo: int
    ):
        self.stdout.write("Creando notas por sección...")

        año = self.obtener_año_objetivo(año_objetivo)
        lapso = self.obtener_lapso_objetivo(lapso_objetivo)

        if año is None or lapso is None:
            return

        materias = Materia.objects.all()
        notas_creadas = 0
        no_matriculados = 0

        for estudiante in estudiantes:
            # Obtener la matrícula del estudiante para saber su sección
            try:
                matricula = Matricula.objects.get(
                    estudiante=estudiante,
                    seccion__año=año,
                    lapso=lapso,
                )
            except Matricula.DoesNotExist:
                no_matriculados += 1
                continue

            for materia in materias:
                for _ in range(cantidad_notas):
                    # Generar calificación realista
                    if random.random() < 0.1:  # 10% de probabilidad de nota baja
                        nota = round(random.uniform(1.0, 9.0), 1)
                    else:
                        nota = round(random.uniform(10.0, 20.0), 1)

                    # Algunas notas pueden tener comentarios
                    comentarios = None
                    if random.random() < 0.1:  # 10% de probabilidad de comentario
                        comentarios = self.faker.sentence()

                    Nota.objects.create(
                        matricula=matricula,
                        materia=materia,
                        valor_nota=nota,
                        comentarios=comentarios,
                    )

                    notas_creadas += 1

                    if notas_creadas % 100 == 0:  # Mostrar progreso
                        self.stdout.write(f"✓ Creadas {notas_creadas} notas...")

        if no_matriculados > 0:
            mensaje = f"No se pudieron crear notas para los {no_matriculados} estudiantes, pues no se encontraron matriculados con los parámetros proporcionados."
            self.stdout.write(
                self.style.ERROR(mensaje)
                if notas_creadas < 1
                else self.style.WARNING(mensaje)
            )

        if notas_creadas > 0:
            self.stdout.write(f"✓ Total notas creadas: {notas_creadas}")
