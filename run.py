import os

from django.core.management import execute_from_command_line


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

    comandos_apertura = ["manage.py", "runserver", "--insecure", "0.0.0.0:5000"]

    try:
        execute_from_command_line(comandos_apertura)
    except Exception as e:
        print("Error al iniciar el servidor: ", e)
