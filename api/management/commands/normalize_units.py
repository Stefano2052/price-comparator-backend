from django.core.management.base import BaseCommand
from api.models import Product
from api.utils.unit_normalization import UNIT_NORMALIZATION_MAP


class Command(BaseCommand):
    help = "Normalizza le unità di misura nei prodotti esistenti nel database."

    def handle(self, *args, **options):
        updated = 0
        unchanged = 0
        skipped = 0
        unrecognized_units = set()

        for p in Product.objects.exclude(unit__isnull=True).exclude(unit=''):
            original_unit = p.unit.strip().lower()
            normalized_unit = UNIT_NORMALIZATION_MAP.get(original_unit)

            if normalized_unit:
                if normalized_unit != original_unit:
                    p.unit = normalized_unit
                    p.save(update_fields=['unit'])
                    updated += 1
                else:
                    unchanged += 1
            else:
                skipped += 1
                unrecognized_units.add(original_unit)
                self.stdout.write(f"⚠️ Unità non riconosciuta: '{original_unit}' (EAN: {p.ean})")

        self.stdout.write("\n📊 RIEPILOGO:")
        self.stdout.write(f"✅ Prodotti aggiornati: {updated}")
        self.stdout.write(f"➖ Prodotti già corretti: {unchanged}")
        self.stdout.write(f"❌ Unità non riconosciute: {skipped}")

        if unrecognized_units:
            self.stdout.write("\n🔍 Elenco unità non riconosciute:")
            for u in sorted(unrecognized_units):
                self.stdout.write(f"- '{u}'")
