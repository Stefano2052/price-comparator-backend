from django.core.management.base import BaseCommand
from api.models import Product, Price, Store, Category, ProductChangeRequest, UserProfile

class Command(BaseCommand):
    help = "Cancella tutto il contenuto del database (eccetto gli utenti)"

    def handle(self, *args, **kwargs):
        self.stdout.write("⚠️ Cancellazione di tutti i dati in corso...")

        Price.objects.all().delete()
        ProductChangeRequest.objects.all().delete()
        Product.objects.all().delete()
        Store.objects.all().delete()
        Category.objects.all().delete()
        UserProfile.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("✅ Tutti i dati eliminati (eccetto utenti)."))
