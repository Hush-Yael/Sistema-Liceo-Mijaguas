from django.http import HttpRequest
from django.conf import settings


def contexto(request: HttpRequest):
    return {"DEBUG": settings.DEBUG}
