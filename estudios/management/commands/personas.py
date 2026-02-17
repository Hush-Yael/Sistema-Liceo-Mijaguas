import random
from typing import Any, OrderedDict
from estudios.management.commands import BaseComandos, quitar_diacriticos
from estudios.modelos.gestion.personas import (
    Matricula,
    MatriculaEstados,
    Persona,
    Profesor,
    Estudiante,
    ProfesorMateria,
)
from estudios.modelos.parametros import Materia, Seccion
from usuarios.models import Grupo, Usuario


class ArgumentosPersonasMixin(BaseComandos):
    def añadir_argumentos_gestion(self, parser):
        parser.add_argument(
            "--profesores",
            type=int,
            help="Crear solo profesores",
        )

        parser.add_argument(
            "--estudiantes",
            type=int,
            help="Crear solo estudiantes",
        )

        parser.add_argument(
            "--matriculas",
            action="store_true",
            help="Crear solo matrículas",
        )

        parser.add_argument(
            "--asignar-materias",
            action="store_true",
            help="Crear solo asignaciones de materias y profesores",
        )

    def handle_personas(self, options: "dict[str, Any]"):
        if self.si_accion("profesores"):
            self.crear_profesores(options["profesores"])

        if self.si_accion("asignar_materias"):
            profesores = Profesor.objects.all()
            self.asignar_profesores_a_materias(profesores)

        if self.si_accion("estudiantes"):
            self.crear_estudiantes(options["estudiantes"])

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

    def crear_datos_persona(self):
        cedula = self.faker.random_int(min=1, max=32_000_000)
        sexo = self.faker.random_element(Persona.OpcionesSexo.values)

        nombre = (
            self.faker.first_name_female()
            if sexo == Persona.OpcionesSexo.FEMENINO
            else self.faker.first_name_male()
        )

        if nombre.find(" ") == -1:
            nombre += " " + (
                self.faker.first_name_female()
                if sexo == Persona.OpcionesSexo.FEMENINO
                else self.faker.first_name_male()
            )

        apellido = f"{self.faker.last_name()} {self.faker.last_name()}"

        return cedula, sexo, nombre, apellido

    def crear_estudiantes(self, cantidad):
        self.stdout.write(f"Creando {cantidad} estudiantes...")

        estudiantes_creados = 0
        for i in range(cantidad):
            # Verificar si ya existe
            if Estudiante.objects.filter(cedula=i + 1).exists():
                continue

            # Generar datos con Faker (edades entre 13-18 años para secundaria)
            cedula, sexo, nombre, apellido = self.crear_datos_persona()

            # Fecha de nacimiento para estudiantes de secundaria (13-18 años)
            fecha_nacimiento = self.faker.date_of_birth(minimum_age=13, maximum_age=18)

            Estudiante.objects.create(
                cedula=cedula,
                sexo=sexo,
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

    def crear_profesores(self, cantidad):
        self.stdout.write(f"Creando {cantidad} profesores...")

        profesores_creados = 0
        for i in range(cantidad):
            # Generar datos con Faker
            cedula, sexo, nombre, apellido = self.crear_datos_persona()

            d = {
                "sexo": sexo,
                "nombres": nombre,
                "apellidos": apellido,
                "telefono": self.faker.random_element(
                    [None, "", self.faker.phone_number()]
                ),
                "activo": self.faker.boolean(chance_of_getting_true=90),
            }

            no_debe_usarse_otra_cedula = False
            profesor = None

            while not no_debe_usarse_otra_cedula:
                profesor, creado = Profesor.objects.get_or_create(
                    cedula=cedula,
                    defaults=d,
                )

                if creado:
                    no_debe_usarse_otra_cedula = True
                else:
                    cedula = self.faker.random_int(min=1, max=32_000_000)

            if not profesor:
                raise Exception("No se pudo crear el profesor")

            email = f"{quitar_diacriticos(nombre.lower().split(' ')[0])}.{quitar_diacriticos(apellido.lower().split(' ')[0])}@liceo.edu"

            grupo_prof = Grupo.objects.get(name="Profesor")

            prof_usuario, creado = Usuario.objects.get_or_create(
                username=email.split("@")[0],
                defaults={
                    "email": email,
                    "is_staff": True,
                },
            )

            prof_usuario.set_password("1234")
            prof_usuario.save()

            prof_usuario.grupos.add(grupo_prof)

            profesor.save()
            profesores_creados += 1

            self.stdout.write(f"✓ Creado profesor: {nombre} {apellido} ({i})")

        self.stdout.write(f"✓ Total profesores creados: {profesores_creados}")

    def eliminar_usuarios_profesores(self):
        usuarios_profesores = Profesor.objects.values_list("usuario", flat=True)

        if len(usuarios_profesores) > 0:
            self.stdout.write("Eliminando usuarios de profesores...")
            Usuario.objects.filter(id__in=usuarios_profesores).delete()
            self.stdout.write("✓ Usuarios de profesores eliminados")

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
