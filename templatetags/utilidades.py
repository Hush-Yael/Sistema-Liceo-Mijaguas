import json
from django import template
import re

register = template.Library()


@register.filter
def multiplicar(value: float, arg: float):
    try:
        return value * arg
    except (ValueError, TypeError):
        return ""


@register.filter(is_safe=True)
def es_entero(value):
    try:
        int(str(value))
        return True
    except (ValueError, TypeError):
        return False


@register.filter(is_safe=True)
def valor_por_clave(obj, clave):
    if not obj:
        return None
    elif isinstance(obj, dict):
        return obj.get(clave)
    return getattr(obj, clave)


@register.filter(is_safe=True)
def valor_por_indice(lista: list, indice: int):
    try:
        return lista[indice]
    except IndexError:
        return None


# 4 -> "1234" -> luego se usa como rango en un for
@register.filter(is_safe=True)
def convertir_a_rango(value, desde=-1):
    i = desde
    r = ""

    if not es_entero(value):
        return r

    value = int(value)

    if value < desde:
        return r

    while i <= value:
        i += 1
        r += str(i)

    return r


@register.filter
def a_negativo(valor):
    return -valor


@register.filter
def obtener_lista_opciones(campo):
    """
    Convierte las opciones de un ModelChoiceField o ModelMultipleChoiceField
    a una lista de objetos JSON con id y label.

    Uso en templates:
    {{ campo|choices_to_json }}
    """
    try:
        opciones = []

        if hasattr(campo.field, "choices"):
            for value, label in campo.field.choices:
                if value:  # Ignorar opciones vacías
                    opciones.append({"id": str(value), "label": label})

        return opciones
    except Exception:
        return "[]"


@register.filter
def obtener_lista_opciones_json(campo):
    return json.dumps(obtener_lista_opciones(campo))


@register.filter
def reemplazar_espacios(value: str, arg=None):
    return re.sub(r"\s{2,}|\ng", arg or "", value)


@register.filter
def encontrar_retraso(value: str):
    r = re.search(r"retraso=(\d+)", value)
    if r:
        return r.group(1)
