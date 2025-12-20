from django import template

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
def valor_por_clave(dicc, clave):
    if not dicc:
        return None
    return getattr(dicc, clave)


@register.filter(is_safe=True)
def valor_por_indice(lista: list, indice: int):
    try:
        return lista[indice]
    except IndexError:
        return None


@register.simple_tag
def actualizar_var(variable):
    return variable


# 4 -> "1234" -> luego se usa como rango en un for usando make_list
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
def negativo(valor):
    return -valor
