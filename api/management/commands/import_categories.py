import json
import os

from django.core.management.base import BaseCommand
from api.models import Category


class Command(BaseCommand):
    help = "Importa categorie da file JSON, con supporto a parent_tag e traduzioni multilingua"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=r"C:\Users\stefa\price_comparator\backend\categories_full.json",
            help='Percorso del file JSON contenente le categorie'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File non trovato: {file_path}"))
            return

        confirm = input("⚠️ Vuoi cancellare tutte le categorie esistenti prima di importare? (s/N): ").strip().lower()
        if confirm == 's':
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Categorie esistenti eliminate."))

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        tag_to_category = {}

        for entry in data:
            parent = tag_to_category.get(entry.get("parent_tag"))

            category = Category.objects.create(
                name=entry["name"],
                tag=entry["tag"],
                translations=entry.get("translations"),
                parent=parent,
                is_approved=True
            )

            tag_to_category[entry["tag"]] = category
            self.stdout.write(f"✅ Categoria creata: {category.name} (tag: {category.tag})")

        self.stdout.write(self.style.SUCCESS("✔ Importazione categorie completata."))
