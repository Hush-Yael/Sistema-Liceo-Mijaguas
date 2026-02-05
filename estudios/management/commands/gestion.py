from typing import Any, OrderedDict
import random
from estudios.management.commands import BaseComandos
from estudios.modelos.parametros import Lapso, Año, Materia, Seccion
from usuarios.models import Grupo, Usuario
from estudios.modelos.gestion.personas import (
    Profesor,
    Estudiante,
    ProfesorMateria,
    Matricula,
    MatriculaEstados,
)
from estudios.modelos.gestion.calificaciones import Nota


class ArgumentosGestionMixin(BaseComandos):
    def añadir_argumentos_gestion(self, parser):
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
            "--asignar-materias",
            action="store_true",
            help="Crear solo asignaciones de materias y profesores",
        )

    def handle_parametros(self, options: "dict[str, Any]") -> None:
        if self.si_accion("profesores"):
            self.crear_profesores(options["cantidad_profesores"])

        if self.si_accion("estudiantes"):
            self.crear_estudiantes(options["cantidad_estudiantes"])

        if self.si_accion("asignar_materias"):
            profesores = Profesor.objects.all()
            self.asignar_profesores_a_materias(profesores)

        if self.si_accion("matriculas"):
            estudiantes = Estudiante.objects.all()

            if estudiantes.first() is None:
                return self.stdout.write(
                    self.style.ERROR("No se han añadido estudiantes")
                )

            self.matricular_estudiantes(
                estudiantes,
                options["lapso"],
                options["seccion"],
            )

        if self.si_accion("notas"):
            estudiantes = Estudiante.objects.all()

            if estudiantes.first() is None:
                return self.stdout.write(
                    self.style.ERROR("No se han añadido estudiantes")
                )

            cantidad = options["cantidad_notas"]
            self.crear_notas(estudiantes, cantidad, options["lapso"])

    def crear_estudiantes(self, cantidad):
        self.stdout.write(f"Creando {cantidad} estudiantes...")

        estudiantes_creados = 0
        for i in range(cantidad):
            # Verificar si ya existe
            if Estudiante.objects.filter(cedula=i + 1).exists():
                continue

            # Generar datos con Faker (edades entre 13-18 años para secundaria)
            nombre = self.faker.first_name()
            apellido = self.faker.last_name()

            # Fecha de nacimiento para estudiantes de secundaria (13-18 años)
            fecha_nacimiento = self.faker.date_of_birth(minimum_age=13, maximum_age=18)

            Estudiante.objects.create(
                cedula=i + 1,
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

    def obtener_año_id(self, año_id: "int | None"):
        if año_id is None:
            return self.stdout.write(
                self.style.ERROR(
                    "Debes proporcionar el número del año objetivo para esta operación."
                )
            )

        try:
            return Año.objects.get(id=año_id)
        except Año.DoesNotExist:
            return self.stdout.write(
                self.style.ERROR(
                    f"No existe el año número {año_id}. "
                    f"Ejecuta primero poblar_datos_estudios para crear los años por defecto."
                )
            )

    def crear_profesores(self, cantidad):
        self.stdout.write(f"Creando {cantidad} profesores...")

        profesores_creados = 0
        for i in range(cantidad):
            # Verificar si ya existe
            if Profesor.objects.filter(cedula=i + 1).exists():
                continue

            # Generar datos con Faker
            nombre = self.faker.first_name()
            apellido = self.faker.last_name()
            email = f"{nombre.lower()}.{apellido.lower()}@colegio.edu"

            # Asegurar que el email sea único
            contador_email = 1
            email_original = email

            while Usuario.objects.filter(email=email).exists():
                email = f"{email_original.split('@')[0]}{contador_email}@colegio.edu"
                contador_email += 1

            grupo_prof = Grupo.objects.get(name="Profesor")

            prof_usuario = Usuario.objects.create(
                username=email.split("@")[0],
                email=email,
                is_staff=True,
            )

            prof_usuario.set_password("1234")
            prof_usuario.save()

            Profesor.objects.create(
                cedula=i + 1,
                nombres=nombre,
                apellidos=apellido,
                telefono=self.faker.random_element(
                    [None, "", self.faker.phone_number()]
                ),
                esta_activo=self.faker.boolean(chance_of_getting_true=90),
                usuario=prof_usuario,
            )

            prof_usuario.grupos.add(grupo_prof)

            profesores_creados += 1
            self.stdout.write(f"✓ Creado profesor: {nombre} {apellido} ({i})")

        self.stdout.write(f"✓ Total profesores creados: {profesores_creados}")

    def asignar_profesores_a_materias(self, profesores):
        if (año := self.obtener_año_id(self.año_id)) is None:
            return

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
                            f"✓ {profesor} → {materia.nombre} - {seccion.letra} ({tipo})"
                        )

        self.stdout.write(f"✓ Total asignaciones creadas: {asignaciones_creadas}")

    def eliminar_usuarios_profesores(self):
        usuarios_profesores = Profesor.objects.values_list("usuario", flat=True)

        if len(usuarios_profesores) > 0:
            self.stdout.write("Eliminando usuarios de profesores...")
            Usuario.objects.filter(id__in=usuarios_profesores).delete()
            self.stdout.write("✓ Usuarios de profesores eliminados")

    def obtener_lapso_objetivo(self, lapso_objetivo: "int | None"):
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

    def matricular_estudiantes(
        self,
        estudiantes,
        lapso_objetivo: int,
        seccion_objetivo: int,
    ):
        self.stdout.write(
            f"Matriculando estudiantes {f'en todas las secciones del año {self.año_id}...' if seccion_objetivo is None else f'en la sección {seccion_objetivo}...'}"
        )

        if (lapso := self.obtener_lapso_objetivo(lapso_objetivo)) is None:
            return

        matriculas_creadas = 0
        ya_matriculados = 0

        if seccion_objetivo is not None:
            if self.año_id is not None:
                self.stdout.write(
                    self.style.WARNING(
                        "Advertencia: al indicar la sección, el año indicado es ignorado."
                    )
                )

            if (seccion := Seccion.objects.filter(id=seccion_objetivo).first()) is None:
                return self.stdout.write(
                    self.style.ERROR("No se encontró la sección proporcionada.")
                )

            for estudiante in estudiantes:
                _, creada = Matricula.objects.get_or_create(
                    estudiante=estudiante,
                    seccion=seccion,
                    lapso=lapso,
                    defaults={
                        "estado": self.faker.random_element(
                            OrderedDict(
                                [
                                    (MatriculaEstados.ACTIVO, 0.9),
                                    (MatriculaEstados.INACTIVO, 0.1),
                                ]
                            ),
                        ),
                    },
                )

                if creada:
                    matriculas_creadas += 1
                    self.stdout.write(f"✓ Matriculado: {estudiante}")
                else:
                    ya_matriculados += 1
        else:
            if (año := self.obtener_año_id(self.año_id)) is None:
                return

            secciones = Seccion.objects.filter(año=año)

            if not secciones.exists():
                self.stdout.write(
                    self.style.ERROR("No hay secciones creadas para este año.")
                )
                return

            # Distribuir estudiantes entre secciones de manera equitativa
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
                        seccion=seccion,
                        defaults={
                            "estado": self.faker.random_element(
                                OrderedDict(
                                    [
                                        (MatriculaEstados.ACTIVO, 0.9),
                                        (MatriculaEstados.INACTIVO, 0.1),
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

    def crear_notas(self, estudiantes, cantidad_notas: int, lapso_objetivo: int):
        self.stdout.write("Creando notas por sección...")

        if (año := self.obtener_año_id(self.año_id)) is None or (
            lapso := self.obtener_lapso_objetivo(lapso_objetivo)
        ) is None:
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

                    Nota.objects.create(
                        matricula=matricula,
                        materia=materia,
                        valor=nota,
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
