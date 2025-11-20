from django import template

register = template.Library()


@register.filter
def valor_dict_por_clave(value: dict, arg):
    return value.get(arg)
