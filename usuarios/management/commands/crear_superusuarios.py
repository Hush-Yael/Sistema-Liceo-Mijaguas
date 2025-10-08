from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from usuarios.models import User

        superuser = User.objects.filter(is_superuser=True).first()
        if superuser is None:
            User.objects.create_superuser("admin", "", "admin")
