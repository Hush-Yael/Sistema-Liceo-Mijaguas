import random
from typing import Any, OrderedDict
from app.util import nc
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
from usuarios.models import Grupo, GruposBase, Usuario
from django.utils import timezone


class ArgumentosPersonasMixin(BaseComandos):
    def añadir_argumentos_personas(self, parser):
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

        nombres = (
            self.faker.first_name_female()
            if sexo == Persona.OpcionesSexo.FEMENINO
            else self.faker.first_name_male()
        )

        if nombres.find(" ") == -1:
            nombres += " " + (
                self.faker.first_name_female()
                if sexo == Persona.OpcionesSexo.FEMENINO
                else self.faker.first_name_male()
            )

        apellidos = f"{self.faker.last_name()} {self.faker.last_name()}"

        return cedula, sexo, nombres, apellidos

    def crear_estudiantes(self, cantidad):
        self.stdout.write(f"Creando {cantidad} estudiantes...")

        estudiantes_creados = 0

        for _ in range(cantidad):
            # Generar datos con Faker (edades entre 13-18 años para secundaria)
            cedula, sexo, nombre, apellido = self.crear_datos_persona()
            # Verificar si ya existe

            # Fecha de nacimiento para estudiantes de secundaria (13-18 años)
            fecha_nacimiento = self.faker.date_of_birth(minimum_age=13, maximum_age=18)

            datos = {
                "sexo": sexo,
                "nombres": nombre,
                "apellidos": apellido,
                "fecha_nacimiento": fecha_nacimiento,
                "fecha_ingreso": timezone.make_aware(
                    self.faker.date_time_between(start_date="-2y"),
                    timezone=timezone.get_current_timezone(),
                ),
            }

            _, creado = Estudiante.objects.get_or_create(cedula=cedula, defaults=datos)

            if not creado:
                continue

            estudiantes_creados += 1
            if estudiantes_creados % 10 == 0:  # Mostrar progreso cada 10 estudiantes
                self.stdout.write(f"✓ Creados {estudiantes_creados} estudiantes...")

        self.stdout.write(f"✓ Total estudiantes creados: {estudiantes_creados}")

    def crear_profesores(self, cantidad):
        self.stdout.write(f"Creando {cantidad} profesores...")

        # Pre-cargar el grupo una sola vez
        grupo_prof = Grupo.objects.get(name=GruposBase.PROFESOR.value)

        # Listas para bulk_create
        usuarios_crear = []
        profesores_crear = []

        # Conjunto para tracking de cédulas
        cedulas_existentes = set(Profesor.objects.values_list("cedula", flat=True))
        cedulas_usadas = set()

        for i in range(cantidad):
            # Generar datos con Faker
            cedula, sexo, nombre, apellido = self.crear_datos_persona()

            # Validar cédula única
            while cedula in cedulas_existentes or cedula in cedulas_usadas:
                cedula = self.faker.random_int(min=1, max=32_000_000)

            cedulas_usadas.add(cedula)

            # Crear email
            email = f"{quitar_diacriticos(nombre.lower().split(' ')[0])}.{quitar_diacriticos(apellido.lower().split(' ')[0])}@liceo.edu"
            username = email.split("@")[0]

            # Crear usuario
            usuario = Usuario(
                username=username,
                email=email,
                is_staff=True,
            )
            usuario.set_password("1234")
            usuarios_crear.append(usuario)

            # Crear profesor
            profesor = Profesor(
                cedula=cedula,
                sexo=sexo,
                nombres=nombre,
                apellidos=apellido,
                telefono=self.faker.random_element(
                    [None, "", self.faker.phone_number()]
                ),
                activo=self.faker.boolean(chance_of_getting_true=90),
                usuario=usuario,  # Temporal, se actualizará después del bulk_create
            )
            profesores_crear.append(profesor)

            self.stdout.write(f"✓ Creado profesor: {nombre} {apellido} ({i})")

        # Bulk create usuarios
        Usuario.objects.bulk_create(usuarios_crear)

        # Asignar usuarios a profesores y hacer bulk create
        for i, profesor in enumerate(profesores_crear):
            profesor.usuario = usuarios_crear[i]

        Profesor.objects.bulk_create(profesores_crear)

        # Asignar grupos usando through model directamente para mejor performance
        Usuario_grupos = Usuario.grupos.through

        usuario_grupos_crear = [
            Usuario_grupos(usuario_id=usuario.id, grupo_id=grupo_prof.pk)
            for usuario in usuarios_crear
        ]

        Usuario_grupos.objects.bulk_create(usuario_grupos_crear)

        self.stdout.write(f"✓ Total profesores creados: {cantidad}")

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
