# variant_group.py
import re
from typing import Dict, List, Any, Set


# Cache para regex (similar al de TypeScript)
_regex_cache: Dict[str, re.Pattern] = {}


class HighlightAnnotation:
    """Representa una anotación de resaltado con posición y clase CSS"""

    def __init__(self, offset: int, length: int, class_name: str):
        self.offset = offset
        self.length = length
        self.class_name = class_name

    def __repr__(self):
        return f"HighlightAnnotation(offset={self.offset}, length={self.length}, class_name='{self.class_name}')"


class VariantGroup:
    """Representa un grupo de variantes con sus items"""

    def __init__(self, length: int, items: List[HighlightAnnotation] = None):
        self.length = length
        self.items = items if items is not None else []

    def __repr__(self):
        return f"VariantGroup(length={self.length}, items={self.items})"


def make_regex_class_group(separators: List[str] = None) -> re.Pattern:
    """
    Crea o obtiene del cache un regex para detectar grupos de variantes

    Args:
        separators: Lista de separadores (por defecto [":"])

    Returns:
        Pattern: Expresión regular compilada
    """
    if separators is None:
        separators = [":"]

    # Crear clave de cache
    key = "|".join(separators)

    if key not in _regex_cache:
        # Patrón regex equivalente al de TypeScript
        pattern = rf"((?:[!@<~\w+:_-]|\[&?>?:?\S*\])+?)({key})\(((?:[~!<>\w\s:/\\,%#.$?-]|\[[^\]]*?\])+?)\)(?!\s*?=>)"
        _regex_cache[key] = re.compile(pattern, re.MULTILINE)

    return _regex_cache[key]


def analizar_grupo_variantes(
    input_str: str, separators: List[str] = None, depth: int = 5
) -> Dict[str, Any]:
    """
    Parsea y expande grupos de variantes CSS

    Args:
        input_str: Cadena con clases CSS que pueden contener grupos de variantes
        separators: Separadores a expandir (por defecto ["-", ":"])
        depth: Profundidad máxima de procesamiento recursivo

    Returns:
        Dict: Resultado con prefijos, grupos y el string expandido
    """
    if separators is None:
        separators = ["-", ":"]

    regex_class_group = make_regex_class_group(separators)
    has_changed = False
    content = str(input_str)
    prefixes: Set[str] = set()
    groups_by_offset: Dict[int, VariantGroup] = {}

    # Contador para controlar la profundidad
    current_depth = depth

    while current_depth > 0:
        has_changed = False
        last_end = 0
        new_content_parts = []

        for match in regex_class_group.finditer(content):
            # Agregar la parte antes del match
            new_content_parts.append(content[last_end : match.start()])

            full_match = match.group(0)
            pre = match.group(1)  # Prefijo
            sep = match.group(2)  # Separador
            body = match.group(3)  # Contenido del paréntesis
            group_offset = match.start()

            if sep not in separators:
                # No procesar si el separador no está en la lista
                new_content_parts.append(full_match)
            else:
                has_changed = True
                prefixes.add(pre + sep)

                # Calcular offset del cuerpo
                body_offset = (
                    group_offset + len(pre) + len(sep) + 1
                )  # +1 para el paréntesis

                # Crear grupo para este offset
                group = VariantGroup(length=len(full_match), items=[])
                groups_by_offset[group_offset] = group

                # Procesar cada item dentro del cuerpo
                # Encontrar todos los tokens no-espacio
                for item_match in re.finditer(r"\S+", body):
                    item_offset = body_offset + item_match.start()
                    item_text = item_match.group(0)

                    # Verificar si hay un grupo interno en este offset
                    inner_items = None
                    if item_offset in groups_by_offset:
                        inner_group = groups_by_offset.pop(item_offset)
                        inner_items = inner_group.items

                    if inner_items:
                        # Usar items del grupo interno
                        for item in inner_items:
                            if item.class_name == "~":
                                item.class_name = pre
                            else:
                                # Aplicar prefijo y separador
                                item.class_name = re.sub(
                                    r"^(!?)(.*)",
                                    rf"\g<1>{pre}{sep}\g<2>",
                                    item.class_name,
                                )
                            group.items.append(item)
                    else:
                        # Crear nuevo item
                        if item_text == "~":
                            class_name = pre
                        else:
                            class_name = re.sub(
                                r"^(!?)(.*)", rf"\g<1>{pre}{sep}\g<2>", item_text
                            )

                        annotation = HighlightAnnotation(
                            offset=item_offset,
                            length=len(item_text),
                            class_name=class_name,
                        )
                        group.items.append(annotation)

                # Reemplazar con marcador de posición de la misma longitud
                placeholder = "$" * len(full_match)
                new_content_parts.append(placeholder)

            last_end = match.end()

        # Agregar la parte final después del último match
        new_content_parts.append(content[last_end:])
        content = "".join(new_content_parts)

        current_depth -= 1
        if not has_changed:
            break

    # Construir string expandido
    expanded = ""
    prev_offset = 0

    # Ordenar offsets para procesar en orden
    sorted_offsets = sorted(groups_by_offset.keys())

    for offset in sorted_offsets:
        group = groups_by_offset[offset]

        # Agregar texto antes del grupo
        expanded += input_str[prev_offset:offset]

        # Agregar items expandidos
        expanded += " ".join(item.class_name for item in group.items)

        prev_offset = offset + group.length

    # Agregar el resto del texto
    expanded += input_str[prev_offset:]

    # Propiedad lazy (similar al getter de TypeScript)
    class LazyExpanded:
        def __init__(self, value: str):
            self._value = value

        def __str__(self):
            return self._value

        def __repr__(self):
            return repr(self._value)

    return {
        "prefixes": list(prefixes),
        "has_changed": has_changed,
        "groups_by_offset": groups_by_offset,
        "expanded": LazyExpanded(expanded),
    }


class TransformerVariantGroupOptions:
    """
    Opciones para el transformador de grupos de variantes

    Args:
        separators: Separadores a expandir (por defecto [":", "-"])
    """

    def __init__(self, separators: List[str] = None):
        if separators is None:
            separators = [":", "-"]
        self.separators = separators


def transformador_grupo_variantes(options: TransformerVariantGroupOptions = None):
    """
    Crea un transformador para grupos de variantes CSS

    Args:
        options: Opciones de configuración

    Returns:
        Dict: Transformador con nombre y función de transformación
    """
    if options is None:
        options = TransformerVariantGroupOptions()

    def transform(s: str) -> Dict[str, Any]:
        """
        Transforma una cadena con grupos de variantes

        Args:
            s: Cadena con clases CSS

        Returns:
            Dict: Resultado con anotaciones de resaltado
        """
        result = analizar_grupo_variantes(s, options.separators)

        # Obtener todas las anotaciones de resaltado
        highlight_annotations = []
        for group in result["groups_by_offset"].values():
            highlight_annotations.extend(group.items)

        return {"highlight_annotations": highlight_annotations}

    return {
        "name": "@unocss/transformer-variant-group",
        "enforce": "pre",
        "transform": transform,
    }
