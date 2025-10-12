from django.contrib.auth.models import AbstractUser

from dist.manejo._internal.django.db import models

AbstractUser._meta.get_field("email").verbose_name = "Correo"
AbstractUser._meta.get_field("is_staff").verbose_name = "Puede ingresar"
AbstractUser._meta.get_field("date_joined").verbose_name = "Fecha de ingreso"


class User(AbstractUser):
    foto_perfil = models.ImageField(null=True, blank=True, upload_to="fotos_perfil/")
    first_name = None
    last_name = None

    def save(self, *args, **kwargs):
        try:
            this = User.objects.get(id=self.id)  # type: ignore
            if this.foto_perfil != self.foto_perfil:
                this.foto_perfil.delete(save=False)
        except Exception as e:
            print(e)
            pass
        super(User, self).save(*args, **kwargs)
