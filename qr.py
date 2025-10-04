import qrcode
import qrcode.image.svg
from constantes import RUTA_BASE


def generar_imagen_qr(ip: str, puerto: str):
    url = f"http://{ip}:{puerto}"

    png = qrcode.make(url)
    png.save(RUTA_BASE / "liceo" / "static/qr.png")  # type: ignore

    svg = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    svg.save(RUTA_BASE / "liceo" / "static/qr.svg")  # type: ignore
