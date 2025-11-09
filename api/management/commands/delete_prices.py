from django.core.management.base import BaseCommand
from api.models import Price

class Command(BaseCommand):
    help = "Cancella tutti i prezzi presenti nel database"

    def handle(self, *args, **kwargs):
        count = Price.objects.count()
        Price.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"🗑️ Cancellati {count} prezzi dal database."))
