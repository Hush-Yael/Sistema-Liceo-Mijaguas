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
    return getattr(dicc, clave)
