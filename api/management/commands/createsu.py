from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Crea un superuser automaticamente su Render"

    def handle(self, *args, **kwargs):
        username = "admin"
        email = "admin@example.com"
        password = "Admin123!"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"L'utente {username} esiste già."))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' creato con successo!"))
