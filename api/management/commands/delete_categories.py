from django.core.management.base import BaseCommand
from api.models import Category

class Command(BaseCommand):
    help = "Cancella tutte le categorie presenti nel database"

    def handle(self, *args, **kwargs):
        count = Category.objects.count()
        Category.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"🗑️ Cancellate {count} categorie dal database."))
