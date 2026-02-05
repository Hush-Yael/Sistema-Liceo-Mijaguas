from typing import TypedDict
from django.core.management.base import BaseCommand
from faker import Faker


class Acciones(TypedDict):
    profesores: bool
    estudiantes: bool
    lapsos: bool
    asignar_materias: bool
    matriculas: bool
    notas: bool


class BaseComandos(BaseCommand):
    limpiar_todo: bool
    limpiar_modelo: str
    hacer_todo: bool
    año_id: int
    acciones: Acciones

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker("es_ES")  # Español de España
        self.faker.seed_instance(1234)  # Para resultados consistentes

    def si_accion(self, accion: str) -> bool:
        return self.hacer_todo or self.acciones[accion]
