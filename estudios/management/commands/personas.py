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
from estudios.modelos.parametros import Materia, Seccion, AñoMateria
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
            if not Materia.objects.exists():
                return self.stdout.write(self.style.ERROR("No se han creado materias"))

            if not Seccion.objects.exists():
                return self.stdout.write(self.style.ERROR("No se han creado secciones"))

            elif not Profesor.objects.exists():
                return self.stdout.write(
                    self.style.ERROR("No se han creado profesores")
                )

            self.asignar_profesores_a_materias()

        if self.si_accion("estudiantes"):
            self.crear_estudiantes(options["estudiantes"])

        if self.si_accion("matriculas"):
            if not Estudiante.objects.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Matriculando estudiantes: No se han añadido estudiantes"
                    )
                )
            elif not Seccion.objects.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Matriculando estudiantes: No se han creado secciones"
                    )
                )

            self.matricular_estudiantes(
                options["lapso"],
                options["seccion"],
                options["año"],
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

    def asignar_profesores_a_materias(self):
        """Asignar profesores a materias por sección. Crea las combinaciones (seccion_id, materia_id) sin especificar el profesor, y luego se asignan aleatoriamente a los profesores."""

        self.stdout.write("Asignando profesores a materias por cada sección...")

        asignaciones_existentes = ProfesorMateria.objects.values(
            "seccion_id", "materia_id"
        )

        # Construimos una subconsulta para excluir asignaciones existentes
        combinaciones_excluir = tuple(
            f"{asignacion['seccion_id']}_{asignacion['materia_id']}"
            for asignacion in asignaciones_existentes
        )

        materias_disponibles: "list[str]" = []

        # Primero obtenemos todas las materias por año
        años_materias = AñoMateria.objects.select_related(
            nc(AñoMateria.año), nc(AñoMateria.materia)
        ).values(
            f"{nc(AñoMateria.año)}_id",
            f"{nc(AñoMateria.materia)}_id",
        )

        for año_materia in años_materias:
            # Obtenemos todas las secciones de este año
            secciones = Seccion.objects.values("id").filter(
                año__id=año_materia["año_id"]
            )

            for seccion in secciones:
                id_combinacion = f"{seccion['id']}_{año_materia['materia_id']}"
                # Verificamos si esta combinación ya está asignada
                if id_combinacion not in combinaciones_excluir:
                    materias_disponibles.append(id_combinacion)

        if len(materias_disponibles) > 0:
            profesores_ids = tuple(Profesor.objects.values_list("id", flat=True))
            asignadas = 0

            while asignadas < len(materias_disponibles):
                profesor_id = self.faker.random_element(profesores_ids)
                materia = self.faker.random_element(materias_disponibles)
                seccion_id, materia_id = materia.split("_")

                _, creado = ProfesorMateria.objects.get_or_create(
                    seccion_id=seccion_id,
                    materia_id=materia_id,
                    defaults={
                        "profesor_id": profesor_id,
                    },
                )

                if creado:
                    asignadas += 1

            self.stdout.write(
                f"✓ {asignadas} asignaciones de profesores a materias creadas"
            )
        else:
            self.stdout.write(
                "✓ No se asignaron profesores a materias, ya que todas ya están asignadas"
            )

    def matricular_estudiantes(
        self,
        lapso_objetivo: "int | None",
        seccion_objetivo: "int | None",
        año_objetivo: "int | None",
    ):
        """Matricular a los estudiantes en la sección indicada o, si no se indica, en todas las secciones del año indicado."""

        self.stdout.write("Matriculando estudiantes")

        # siempre se necesita un lapso
        if (lapso := self.obtener_lapso_objetivo(lapso_objetivo)) is None:
            return

        distribuir = input(
            "Desea distribuir los estudiantes en las secciones? (s/n): "
        ).lower()

        # Distribuir los estudiantes en las secciones existentes equitativamente
        if distribuir == "s":
            estudiantes = Estudiante.objects.all()

            secciones = Seccion.objects.all()

            año = self.obtener_año_objetivo(año_objetivo, True)

            if año:
                self.stdout.write(f"Buscando secciones para el año {año}")

                secciones = Seccion.objects.filter(año=año)

                if not secciones.exists():
                    self.stdout.write(
                        self.style.ERROR("No hay secciones creadas para este año.")
                    )
                    return
            else:
                self.stdout.write("Matriculando estudiantes en todas las secciones.")

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

                    matriculas = Matricula.objects.bulk_create(
                        tuple(
                            Matricula(
                                estudiante=estudiante,
                                lapso=lapso,
                                seccion=seccion,
                                estado=self.faker.random_element(
                                    OrderedDict(
                                        [
                                            (MatriculaEstados.ACTIVO, 0.9),
                                            (MatriculaEstados.INACTIVO, 0.1),
                                        ]
                                    ),
                                ),
                            )
                            for estudiante in estudiantes_seccion
                        )
                    )

                    self.stdout.write(f"✓ {len(matriculas)} Estudiantes matriculados")

        # Asignar un rango de estudiantes a una sección
        else:
            seccion = self.obtener_seccion_objetivo(seccion_objetivo)

            if (seccion := Seccion.objects.filter(id=seccion_objetivo).first()) is None:
                return self.stdout.write(
                    self.style.ERROR(
                        "Matriculando estudiantes: no se encontró la sección proporcionada."
                    )
                )

            rango = input(
                f"Indique el rango de estudiantes a matricular (secciones: {seccion.letra}): "
            )

            estudiantes = Estudiante.objects.filter(pk__in=rango.split("-"))

            if not estudiantes.exists():
                return self.stdout.write(
                    self.style.ERROR(
                        "Matriculando estudiantes: no se encontraron estudiantes en el rango proporcionado."
                    )
                )

            matriculas_creadas = Matricula.objects.bulk_create(
                tuple(
                    (
                        Matricula(
                            estudiante=estudiante,
                            seccion=seccion,
                            lapso=lapso,
                            estado=self.faker.random_element(
                                OrderedDict(
                                    [
                                        (MatriculaEstados.ACTIVO, 0.9),
                                        (MatriculaEstados.INACTIVO, 0.1),
                                    ]
                                ),
                            ),
                        )
                    )
                    for estudiante in estudiantes
                ),
                ignore_conflicts=True,
            )

            self.stdout.write(f"✓ {len(matriculas_creadas)} Estudiantes matriculados")
