from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from usuarios.models import Usuario

        superuser = Usuario.objects.filter(is_superuser=True).first()
        if superuser is None:
            Usuario.objects.create_superuser("admin", "", "admin")
