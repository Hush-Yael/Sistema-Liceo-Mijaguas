from django import template

register = template.Library()


@register.filter
def multiplicar(value: float, arg: float) -> float:
    try:
        return value * arg
    except (ValueError, TypeError):
        return ""
