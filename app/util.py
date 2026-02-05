from typing import Any, Mapping, Type
from django.db import models
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


def nombre_url_crear_auto(modelo: Type[models.Model]) -> str:
    return f"crear_{modelo._meta.model_name}"


def nombre_url_editar_auto(modelo: Type[models.Model]) -> str:
    return f"editar_{modelo._meta.model_name}"


def nombre_url_lista_auto(modelo: Type[models.Model]) -> str:
    return str(modelo._meta.model_name)
