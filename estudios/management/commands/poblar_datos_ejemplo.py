from django.core.management.base import BaseCommand
from estudios.models import (
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
            self.crear_lapsos(año)

        if hacer_todo or acciones["asignaciones"]:
            self.asignar_materias_a_año(año)
            profesores = Profesor.objects.all()
            self.asignar_profesores_a_materias(profesores, año)

        if hacer_todo or acciones["matriculas"]:
            estudiantes = Estudiante.objects.all()
            self.matricular_estudiantes(estudiantes, año)

        if hacer_todo or acciones["notas"]:
            estudiantes = Estudiante.objects.all()
            lapsos = Lapso.objects.filter(año=año)
            self.crear_notas(estudiantes, lapsos)

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
            if Profesor.objects.filter(id=i).exists():
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
            if Estudiante.objects.filter(id=i).exists():
                continue

            # Generar datos con Faker (edades entre 13-18 años para secundaria)
            nombre = self.faker.first_name()
            apellido = self.faker.last_name()

            # Fecha de nacimiento para estudiantes de secundaria (13-18 años)
            fecha_nacimiento = self.faker.date_of_birth(minimum_age=13, maximum_age=18)

            Estudiante.objects.create(
                nombres=nombre,
                apellidos=apellido,
                fecha_nacimiento=fecha_nacimiento,
                fecha_matricula=self.faker.date_between(
                    start_date="-2y", end_date="today"
                ),
                esta_activo=self.faker.boolean(chance_of_getting_true=85),
            )

            estudiantes_creados += 1
            if estudiantes_creados % 10 == 0:  # Mostrar progreso cada 10 estudiantes
                self.stdout.write(f"✓ Creados {estudiantes_creados} estudiantes...")

        self.stdout.write(f"✓ Total estudiantes creados: {estudiantes_creados}")

    def crear_lapsos(self, año):
        """Crear lapsos para el año especificado"""
        self.stdout.write(f"Creando lapsos para {año.nombre_año}...")

        # Determinar el año base según el número del año
        año_base = 2023 + año.numero_año

        lapsos_data = [
            (1, "Primer Lapso", date(año_base, 9, 1), date(año_base, 11, 30)),
            (2, "Segundo Lapso", date(año_base, 12, 1), date(año_base + 1, 2, 28)),
            (3, "Tercer Lapso", date(año_base + 1, 3, 1), date(año_base + 1, 6, 30)),
        ]

        lapsos_creados = 0
        for num, nombre, inicio, fin in lapsos_data:
            _, created = Lapso.objects.get_or_create(
                año=año,
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
        """Asignar profesores a materias de manera aleatoria pero balanceada"""
        self.stdout.write("Asignando profesores a materias...")

        materias = Materia.objects.all()
        asignaciones_creadas = 0

        # Para cada materia, asignar 1-2 profesores
        for materia in materias:
            # Seleccionar 1-2 profesores aleatorios
            num_profesores = random.randint(1, 2)
            profesores_asignados = random.sample(list(profesores), num_profesores)

            for i, profesor in enumerate(profesores_asignados):
                es_principal = i == 0  # El primero es principal

                _, created = ProfesorMateria.objects.get_or_create(
                    profesor=profesor,
                    materia=materia,
                    año=año,
                    defaults={"es_profesor_principal": es_principal},
                )
                if created:
                    asignaciones_creadas += 1
                    tipo = "principal" if es_principal else "secundario"
                    self.stdout.write(
                        f"✓ {profesor} → {materia.nombre_materia} ({tipo})"
                    )

        self.stdout.write(f"✓ Total asignaciones creadas: {asignaciones_creadas}")

    def matricular_estudiantes(self, estudiantes, año):
        """Matricular estudiantes en el año"""
        self.stdout.write(f"Matriculando estudiantes en {año.nombre_año}...")

        matriculas_creadas = 0
        estados = ["activo", "activo", "activo", "inactivo"]  # 75% activos

        for estudiante in estudiantes:
            # Algunos estudiantes pueden estar inactivos
            estado = random.choice(estados)

            _, created = Matricula.objects.get_or_create(
                estudiante=estudiante,
                año=año,
                defaults={
                    "estado": estado,
                    "fecha_matricula": self.faker.date_between(
                        start_date="-1y", end_date="today"
                    ),
                },
            )
            if created:
                matriculas_creadas += 1

        self.stdout.write(f"✓ Total matriculas creadas: {matriculas_creadas}")

    def crear_notas(self, estudiantes, lapsos):
        """Crear notas realistas usando Faker"""
        self.stdout.write("Creando notas...")

        materias = Materia.objects.all()
        notas_creadas = 0

        for estudiante in estudiantes:
            for lapso in lapsos:
                for materia in materias:
                    # Solo crear notas para estudiantes activos en ese año
                    try:
                        Matricula.objects.get(
                            estudiante=estudiante, año=lapso.año, estado="activo"
                        )
                    except Matricula.DoesNotExist:
                        continue

                    # Verificar si ya existe calificación
                    if Nota.objects.filter(
                        estudiante=estudiante, materia=materia, lapso=lapso
                    ).exists():
                        continue

                    # Generar calificación realista (normalmente entre 10-20, ocasionalmente <10)
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
