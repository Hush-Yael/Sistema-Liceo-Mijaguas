from django.shortcuts import redirect
from django.views.generic.base import View


class VistaParaNoLogueadosMixin(View):
    """Mixin para vistas a las que solo deben acceder los usuarios que no han iniciado sesión"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("inicio")

        return super().dispatch(request, *args, **kwargs)
