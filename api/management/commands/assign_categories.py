from django.core.management.base import BaseCommand
from api.models import Product, Category
from transformers import pipeline
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Assegna automaticamente la categoria più corretta a ciascun prodotto usando AI zero-shot"

    def handle(self, *args, **options):
        logger.info("🔍 Inizio assegnazione categorie")

        # 1. Costruzione dizionario label → tag
        label_to_tag = {}
        candidate_labels = []
        for category in Category.objects.all():
            label_it = category.translations.get("it", {}).get("name")
            if label_it:
                candidate_labels.append(label_it)
                label_to_tag[label_it] = category.tag

        logger.info(f"🎯 Totale etichette candidate: {len(candidate_labels)}")

        # 2. Pipeline AI
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

        # 3. Prodotti da classificare
        prodotti = Product.objects.all()
        logger.info(f"📦 Prodotti da classificare: {prodotti.count()}")

        for prodotto in prodotti:
            descrizione = build_product_description(prodotto)
            if not descrizione.strip():
                logger.warning(f"⛔ Prodotto {prodotto.ean} senza descrizione utile, saltato")
                continue

            try:
                result = classifier(
                    descrizione,
                    candidate_labels,
                    hypothesis_template="Questo prodotto è {}."
                )
                best_label = result["labels"][0]
                best_tag = label_to_tag.get(best_label)

                if best_tag:
                    categoria = Category.objects.get(tag=best_tag)
                    prodotto.categories.set([categoria])
                    logger.info(f"✅ {prodotto.ean} → {best_label} (tag: {best_tag})")
                else:
                    logger.warning(f"⚠️ Nessun tag trovato per label: {best_label}")

            except Exception as e:
                logger.error(f"❌ Errore su {prodotto.ean}: {e}")

        logger.info("🏁 Assegnazione categorie completata.")


def build_product_description(p):
    parts = []

    # Campo "name"
    if p.name:
        parts.append(f"Nome: {p.name}")

    # Brand
    if p.brand:
        parts.append(f"Marca: {p.brand}")

    # Ingredienti testuali
    if p.ingredients_text:
        parts.append(f"Ingredienti: {p.ingredients_text}")

    # Ingredienti strutturati
    if p.ingredients:
        names = [ing.get("text", "") for ing in p.ingredients if isinstance(ing, dict)]
        if names:
            parts.append(f"Contiene: {', '.join(names)}")

    # Tag
    for tag_list in [p.labels_tags, p.packaging_tags, p.origins_tags]:
        if tag_list:
            parts.append("Tags: " + ", ".join(tag_list))

    # Translations multilingua
    if p.translations:
        for lang, values in p.translations.items():
            for k in ["product_name", "generic_name", "ingredients_text", "packaging_text"]:
                val = values.get(k)
                if val:
                    parts.append(f"{lang.upper()}: {val}")

    return "\n".join(parts)
