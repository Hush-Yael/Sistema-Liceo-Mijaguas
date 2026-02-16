from django.shortcuts import redirect
from django.views.generic.base import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from typing import Literal, Type
from django.db import models


class VistaProtegidaMixin(PermissionRequiredMixin):
    """Mixin para vistas que requieren permisos. Se encarga de validar automáticamente los permisos pertinentes al modelo de la vista"""

    model: Type[models.Model]
    tipo_permiso: Literal["add", "change", "delete", "view"]
    nombre_modelo: str
    nombre_app_modelo: str

    def __init__(self):
        self.nombre_modelo = str(self.model._meta.model_name)
        self.nombre_app_modelo = self.model._meta.app_label

        self.permission_required = (
            f"{self.nombre_app_modelo}.{self.tipo_permiso}_{self.nombre_modelo}"
        )

        super().__init__()


class VistaParaNoLogueadosMixin(View):
    """Mixin para vistas a las que solo deben acceder los usuarios que no han iniciado sesión"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("inicio")

        return super().dispatch(request, *args, **kwargs)
