"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
from ipqr import ipqr

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_wsgi_application()


puerto = next(
    (item for item in sys.argv if item.startswith("0.0.0.0")),
    None,
)

if puerto is not None:
    puerto = puerto.split(":")[1]

ip = ipqr.get_local_ip()

if ip != "127.0.0.1" and puerto is not None:
    qr = ipqr.generate_qr_code(f"http://{ip}:{puerto}")
    print(qr)
    print("Escanea este código QR para acceder al servidor\n")
