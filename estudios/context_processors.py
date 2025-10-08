from django.http import HttpRequest
from estudios.management.commands.poblar_datos_estudios import AÑOS, MATERIAS


def contexto(request: HttpRequest):
    return {"AÑOS": AÑOS, "MATERIAS": MATERIAS}
