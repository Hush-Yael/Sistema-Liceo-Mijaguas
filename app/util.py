from typing import Any, Mapping
from app.campos import TextosBooleanos


def obtener_filtro_bool_o_nulo(
    nombre_campo: str, datos_form: "dict[str, Any] | Mapping[str, Any]"
):
    valor = datos_form.get(nombre_campo)
    if valor == TextosBooleanos.VERDADERO.value:
        return True
    elif valor == TextosBooleanos.FALSO.value:
        return False
    else:
        return None
