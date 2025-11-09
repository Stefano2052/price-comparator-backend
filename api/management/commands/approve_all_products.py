from django.core.management.base import BaseCommand
from api.models import Product

class Command(BaseCommand):
    help = "Approva tutti i prodotti in attesa"

    def handle(self, *args, **options):
        prodotti_in_attesa = Product.objects.filter(is_approved=False)
        count = prodotti_in_attesa.update(is_approved=True)
        self.stdout.write(self.style.SUCCESS(f"✅ {count} prodotti approvati con successo."))
