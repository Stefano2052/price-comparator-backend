from django.core.management.base import BaseCommand
from api.models import Product

class Command(BaseCommand):
    help = "Stampa per ogni prodotto il nome e le categorie assegnate (nome e tag)"

    def handle(self, *args, **options):
        prodotti = Product.objects.all()

        for prodotto in prodotti:
            print(f"\n📦 Prodotto: {prodotto.name} (EAN: {prodotto.ean})")

            ufficiali = prodotto.categories.all()
            if ufficiali.exists():
                for cat in ufficiali:
                    nome_cat = cat.translations.get("it", {}).get("name", cat.name)
                    print(f"  🏷️ Categoria ufficiale: {nome_cat} (tag: {cat.tag})")
            else:
                print("  ❌ Nessuna categoria ufficiale")

            importate = prodotto.imported_categories.all()
            if importate.exists():
                for cat in importate:
                    nome_cat = cat.translations.get("it", {}).get("name", cat.name)
                    print(f"  🛈 Categoria importata: {nome_cat} (tag: {cat.tag})")
