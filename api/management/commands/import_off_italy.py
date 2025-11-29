import gzip
import json
from typing import List

from django.core.management.base import BaseCommand

from api.models import Category, Product
from api.utils.normalizers import normalize_off_product, safe_list


class Command(BaseCommand):
    """
    Importa prodotti OpenFoodFacts filtrati per l'Italia da un dump JSONL compresso.
    """

    help = "Import massivo da openfoodfacts-products.jsonl.gz con normalizzazione forte."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            required=True,
            help="Percorso del file openfoodfacts-products.jsonl.gz",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Numero massimo di prodotti da importare (solo per test).",
        )

    def handle(self, *args, **options):
        path = options["path"]
        limit = options.get("limit")

        total_read = 0
        italy_considered = 0
        created_count = 0
        updated_count = 0
        discarded_count = 0

        with gzip.open(path, "rt", encoding="utf-8") as file_handle:
            for line in file_handle:
                total_read += 1

                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    discarded_count += 1
                    continue

                if not self._is_italian(doc):
                    continue

                italy_considered += 1
                normalized = normalize_off_product(doc)
                if not normalized:
                    discarded_count += 1
                    continue

                ean = normalized.pop("ean")
                product, created = Product.objects.update_or_create(
                    ean=ean,
                    defaults=normalized,
                )
                self._sync_imported_categories(product, doc.get("categories_tags"))

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                processed = created_count + updated_count
                if processed % 1000 == 0:
                    self.stdout.write(
                        f"Elaborati {processed} prodotti (creati {created_count}, aggiornati {updated_count})."
                    )

                if limit and processed >= limit:
                    break

        self.stdout.write("")
        self.stdout.write(f"Prodotti totali letti: {total_read}")
        self.stdout.write(f"Prodotti Italia considerati: {italy_considered}")
        self.stdout.write(f"Prodotti creati: {created_count}")
        self.stdout.write(f"Prodotti aggiornati: {updated_count}")
        self.stdout.write(f"Prodotti scartati: {discarded_count}")

    def _is_italian(self, doc: dict) -> bool:
        country_tags = doc.get("countries_tags")
        if isinstance(country_tags, list):
            lowered = [str(c).lower() for c in country_tags]
            if "en:italy" in lowered or "it:italia" in lowered:
                return True

        countries = doc.get("countries")
        if isinstance(countries, str):
            countries_lower = countries.lower()
            if "italia" in countries_lower or "italy" in countries_lower:
                return True

        return False

    def _sync_imported_categories(self, product: Product, categories_raw) -> None:
        categories: List[Category] = []
        for tag in safe_list(categories_raw):
            tag_value = str(tag).strip()
            if not tag_value:
                continue

            base_name = tag_value.split(":", 1)[-1] if ":" in tag_value else tag_value
            category, _ = Category.objects.get_or_create(
                tag=tag_value,
                defaults={
                    "name": base_name,
                    "translations": None,
                    "parent": None,
                    "is_approved": False,
                },
            )
            categories.append(category)

        if categories:
            product.imported_categories.set(categories)
        else:
            product.imported_categories.clear()
