from django.contrib.auth.models import AbstractUser
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile

AbstractUser._meta.get_field("email").verbose_name = "Correo"
AbstractUser._meta.get_field("is_staff").verbose_name = "Puede ingresar"
AbstractUser._meta.get_field("date_joined").verbose_name = "Fecha de ingreso"


class User(AbstractUser):
    foto_perfil = models.ImageField(null=True, blank=True, upload_to="fotos_perfil/")
    miniatura_foto = models.ImageField(
        null=True, blank=True, upload_to="fotos_perfil/thumbs/"
    )
    first_name = None
    last_name = None

    tamaño_maximo = 1024
    tamaño_miniatura = 150

    def save(self, *args, **kwargs):
        foto = self.foto_perfil
        usuario = User.objects.get(id=self.id)  # type: ignore

        # elimina las fotos anteriores al subirse una nueva
        if usuario.foto_perfil != foto:
            usuario.foto_perfil.delete(save=False)

            if hasattr(usuario, "miniatura_foto") and usuario.miniatura_foto:
                usuario.miniatura_foto.delete(save=False)

        self.foto_perfil = self.reducir_tamaño_imagen(foto)

        super(User, self).save(*args, **kwargs)

    def reducir_tamaño_imagen(self, foto):
        bytes_io = BytesIO()
        img = Image.open(foto)

        alto = img.height
        ancho = img.width

        # Determinar la dimensión menor para recortar la mayor
        if alto > ancho:
            tamaño_final = alto
            # Recortar arriba y abajo
            izquierda = 0
            derecha = ancho
            arriba = (alto - ancho) // 2
            abajo = (alto + ancho) // 2
        else:
            tamaño_final = ancho
            # Recortar izquierda y derecha
            izquierda = (ancho - alto) // 2
            derecha = (ancho + alto) // 2
            arriba = 0
            abajo = alto

        if tamaño_final > self.tamaño_maximo:
            tamaño_final = self.tamaño_maximo

        # Recortar la imagen a un cuadrado
        img = img.crop((izquierda, arriba, derecha, abajo))

        # miniatura
        miniatura_bytes = BytesIO()
        miniatura = img.copy()

        miniatura.thumbnail(
            (self.tamaño_miniatura, self.tamaño_miniatura), Image.Resampling.LANCZOS
        )
        miniatura.save(
            miniatura_bytes,
            "WEBP",
            quality=80,
            optimize=True,
            lossless=False,
            method=6,
        )

        archivo_miniatura = InMemoryUploadedFile(
            miniatura_bytes,
            "ImageField",
            f"{self.username}_thumb.webp",
            "image/webp",
            miniatura_bytes.getbuffer().nbytes,
            None,
        )

        # Redimensionar la imagen manteniendo la proporción
        img.thumbnail((tamaño_final, tamaño_final), Image.Resampling.LANCZOS)

        # Convertir a RGB si es necesario (para evitar problemas con PNG con canal alpha)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        # Guardar en formato WebP con optimización
        img.save(bytes_io, "WEBP", quality=80, optimize=True, lossless=False, method=6)

        new_image = File(bytes_io, name=f"{self.username}.webp")
        new_image.seek(0)

        # Asignar la miniatura al campo correspondiente si existe
        if hasattr(self, "miniatura_foto"):
            self.miniatura_foto = archivo_miniatura

        return new_image

    # Eliminar archivos de imagen antes de eliminar la instancia
    def delete(self, *args, **kwargs):
        if hasattr(self, "foto_perfil") and self.foto_perfil:
            self.foto_perfil.delete(save=False)

        if hasattr(self, "miniatura_foto") and self.miniatura_foto:
            self.miniatura_foto.delete(save=False)

        super().delete(*args, **kwargs)
