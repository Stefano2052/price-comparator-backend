import json
import logging
import os
import sys
from collections import defaultdict
from django.core.management.base import BaseCommand
from api.models import Product, Category
from api.services.openfacts_importer import fetch_product_data_from_apis
from transformers import pipeline

logger = logging.getLogger(__name__)

# Forza output a terminale
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def load_leaf_categories(path="backend/categories_full.json"):
    full_path = os.path.abspath(path)
    with open(full_path, "r", encoding="utf-8") as f:
        all_categories = json.load(f)
    parent_tags = {cat["parent_tag"] for cat in all_categories if cat["parent_tag"]}
    leaf_categories = [cat for cat in all_categories if cat["tag"] not in parent_tags]
    return leaf_categories


def build_product_description(p):
    parts = []
    if p.name:
        parts.append(f"Nome: {p.name}")
    if p.brand:
        parts.append(f"Marca: {p.brand}")
    if p.ingredients_text:
        parts.append(f"Ingredienti: {p.ingredients_text}")
    if p.ingredients:
        names = [ing.get('text', '') for ing in p.ingredients if isinstance(ing, dict)]
        if names:
            parts.append('Contiene: ' + ', '.join(names))
    if p.labels_tags:
        parts.append('Tags: ' + ', '.join(p.labels_tags))
    return "\n".join(parts)


def build_description_from_external(data):
    parts = []
    for field in ['product_name', 'generic_name', 'categories', 'ingredients_text']:
        val = data.get(field)
        if val:
            parts.append(val)
    return "\n".join(parts)


class Command(BaseCommand):
    help = "Assegna la foglia più adatta a ciascun prodotto utilizzando l'AI"

    def add_arguments(self, parser):
        parser.add_argument('--threshold', type=float, default=0.7, help='Soglia minima di confidenza')
        parser.add_argument('--categories-path', type=str, default='backend/categories_full.json', help='Path file JSON categorie')
        parser.add_argument('--dry-run', action='store_true', help='Mostra le categorie assegnate senza salvare nel database')

    def handle(self, *args, **options):
        threshold = options['threshold']
        path = options['categories_path']
        dry_run = options['dry_run']

        logger.info("\U0001F50D Avvio classificazione prodotti per categorie foglia")

        leaf_cats = load_leaf_categories(path)
        candidate_labels = [cat["translations"]["it"]["name"] for cat in leaf_cats]
        label_to_tag = {cat["translations"]["it"]["name"]: cat["tag"] for cat in leaf_cats}
        tag_to_label = {cat["tag"]: cat["translations"]["it"]["name"] for cat in leaf_cats}

        fallback = Category.objects.filter(translations__it__name="Prodotti non classificati").first()
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

        prodotti = list(Product.objects.all())
        totale = len(prodotti)
        logger.info(f"Prodotti da analizzare: {totale}")

        categoria_count = defaultdict(int)
        assegnazioni = []
        classificati = 0
        fallback_count = 0

        for idx, prodotto in enumerate(prodotti, start=1):
            descrizione = build_product_description(prodotto)
            if not descrizione.strip():
                extra, _ = fetch_product_data_from_apis(prodotto.ean)
                descrizione = build_description_from_external(extra) if extra else (prodotto.name or prodotto.ean)

            try:
                result = classifier(descrizione, candidate_labels, hypothesis_template="Appartiene alla categoria: {}")
                best_label = result['labels'][0]
                best_score = result['scores'][0]
                best_tag = label_to_tag.get(best_label)

                # log top 3 label-score
                top3 = list(zip(result['labels'][:3], result['scores'][:3]))
                logger.info(f"{prodotto.ean} - Top 3 categorie:")
                for lbl, score in top3:
                    logger.info(f"  - {lbl}: {score:.2f}")

                if best_score >= threshold:
                    category = Category.objects.filter(tag=best_tag).first()
                else:
                    logger.info(f"{prodotto.ean}: confidenza troppo bassa ({best_score:.2f}) → fallback")
                    category = fallback
                    fallback_count += 1

                if category:
                    assegnazioni.append((prodotto, category, descrizione, best_score))
                    categoria_count[category.tag] += 1
                    logger.info("\n===\nDescrizione:\n%s\n--> Categoria assegnata: %s\n===", descrizione, tag_to_label.get(category.tag, category.tag))
                    classificati += 1

                progress = (idx / totale) * 100
                logger.info(f"Analizzati {idx} di {totale} ({progress:.1f}%) – Assegnati: {classificati - fallback_count}, Fallback: {fallback_count}")

            except Exception as e:
                logger.error(f"Errore su {prodotto.ean}: {e}")
                if fallback:
                    assegnazioni.append((prodotto, fallback, descrizione, 0))
                    categoria_count[fallback.tag] += 1
                    fallback_count += 1
                    classificati += 1
                logger.info(f"Analizzati {idx} di {totale} – Assegnati: {classificati - fallback_count}, Fallback: {fallback_count}")

        if dry_run:
            logger.info("\n⚠️ Modalità dry-run: nessuna modifica salvata. Puoi rieseguire il comando senza --dry-run per confermare.")
        else:
            logger.info("\n✅ Salvataggio categorie assegnate nel database...")
            for prodotto, category, _, _ in assegnazioni:
                prodotto.categories.set([category])

        logger.info("\n✅ Classificazione completata. Riepilogo per categoria:\n")
        for tag, count in sorted(categoria_count.items(), key=lambda x: -x[1]):
            label = tag_to_label.get(tag, tag)
            logger.info(f"{label} ({tag}): {count} prodotti")
