from django import template

register = template.Library()


@register.filter(is_safe=True)
def es_entero(value):
    try:
        int(str(value))
        return True
    except (ValueError, TypeError):
        return False
