# ============================================================================
# FILTROS PERSONALIZADOS PARA DJANGO
# ============================================================================

from django import template
from django.template.defaultfilters import stringfilter

from .core import analizar_grupo_variantes


register = template.Library()


@register.filter(name="expandir_variantes")
@stringfilter
def expandir_variantes_filtro(value: str) -> str:
    """
    Filtro de Django para expandir grupos de variantes CSS en plantillas

    Uso en plantilla:
        {{ "min-md:(bg-red text-blue)"|variant_group }}

    Resultado:
        "min-md:bg-red min-md:text-blue"
    """
    result = analizar_grupo_variantes(value)
    return str(result["expanded"])


@register.filter(name="expandir_variantes_safe")
@stringfilter
def expandir_variantes_safe_filtro(value: str) -> str:
    """
    Filtro de Django que marca como seguro el resultado HTML

    Uso en plantilla:
        {{ class_string|variant_group_safe }}
    """
    result = analizar_grupo_variantes(value)
    from django.utils.safestring import mark_safe

    return mark_safe(str(result["expanded"]))


def expandir_grupo_variantes(html_content: str) -> str:
    """
    Función para expandir grupos de variantes en todo un fragmento HTML

    Args:
        html_content: Contenido HTML con clases que pueden contener grupos

    Returns:
        str: HTML con clases expandidas
    """
    import re

    # Patrón para encontrar atributos class en tags HTML
    class_pattern = re.compile(r'class=["\']([^"\']+)["\']')

    def replace_class(match):
        classes = match.group(1)
        expanded = analizar_grupo_variantes(classes)["expanded"]
        return f'class="{expanded}"'

    # Reemplazar todas las clases en el HTML
    return class_pattern.sub(replace_class, html_content)


@register.filter(name="expandir_variantes_de_html")
@stringfilter
def expandir_variantes_de_html_filtro(html_content: str) -> str:
    """
    Filtro para expandir grupos de variantes en todo el contenido HTML

    Uso en plantilla:
        {{ html_content|expand_html_variants|safe }}

    Args:
        html_content: Fragmento HTML con clases

    Returns:
        str: HTML con clases expandidas (marcado como seguro)
    """
    expanded = expandir_grupo_variantes(html_content)
    from django.utils.safestring import mark_safe

    return mark_safe(expanded)
