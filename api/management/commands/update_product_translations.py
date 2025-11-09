from django.core.management.base import BaseCommand
from api.models import Product
from django.db.models import Q

class Command(BaseCommand):
    help = "Popola il campo translations per i prodotti esistenti usando i dati da raw_data"

    SUPPORTED_LANGUAGES = ["it", "en", "fr"]
    TRANSLATABLE_FIELDS = [
        "product_name",
        "generic_name",
        "ingredients_text",
        "ingredients_text_with_allergens",
        "packaging_text",
        "conservation_conditions"
    ]

    def handle(self, *args, **options):
        prodotti = Product.objects.exclude(raw_data=None)
        aggiornati = 0
        già_ok = 0

        for p in prodotti:
            updated = False
            translations = p.translations or {}

            for lang in self.SUPPORTED_LANGUAGES:
                lang_data = translations.get(lang, {})
                for field in self.TRANSLATABLE_FIELDS:
                    key = f"{field}_{lang}"
                    valore = p.raw_data.get(key)
                    if valore and not lang_data.get(field):
                        lang_data[field] = valore
                        updated = True
                if lang_data:
                    translations[lang] = lang_data

            if updated:
                p.translations = translations
                p.save()
                aggiornati += 1
            else:
                già_ok += 1

        self.stdout.write(f"\n✅ Traduzioni aggiornate per {aggiornati} prodotti.")
        self.stdout.write(f"➖ Prodotti già completi: {già_ok}")
