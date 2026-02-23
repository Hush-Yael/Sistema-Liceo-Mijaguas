from typing import TYPE_CHECKING, Any, Mapping, Type
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


if TYPE_CHECKING:
    from django.db.models.fields import _FieldDescriptor
    from django.db.models.fields.files import ImageFileDescriptor


def nc(campo: "_FieldDescriptor | ImageFileDescriptor") -> str:
    """Retorna el nombre del campo de acuerdo a su columna de la base de datos"""
    return campo.field.name


def mn(modelo: Type[models.Model]) -> str:
    """Retorna el nombre del modelo"""
    return str(modelo._meta.model_name)


def vn(modelo: Type[models.Model]) -> str:
    """Retorna el verbose name del modelo"""
    return str(modelo._meta.verbose_name)


def vnp(modelo: Type[models.Model]) -> str:
    """Retorna el verbose name plural del modelo"""
    return str(modelo._meta.verbose_name_plural)
