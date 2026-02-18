from django import template

register = template.Library()


@register.filter(name="dir")
def _dir(value):
    return print(dir(value))


@register.filter(name="type")
def _type(value):
    return print(type(value))


@register.filter(name="print")
def _print(value):
    print("------->", value)
