from django.urls import path
from estudios.vistas.gestion import inicio


urlpatterns = (path("", inicio, name="inicio"),)
