import requests
import re
from api.models import Product, Category
from django.utils.timezone import now
from django.db import transaction
from api.utils.unit_normalization import UNIT_NORMALIZATION_MAP


API_DOMAINS = [
    "world.openfoodfacts.org",
    "world.openbeautyfacts.org",
    "world.openpetfoodfacts.org",
    "world.openproductfacts.org",
]


def extract_numeric_quantity(value):
    """
    Estrae la parte numerica da una stringa tipo '375 g' → 375.0
    """
    if not value:
        return None
    try:
        match = re.search(r"[\d.,]+", value)
        if match:
            return float(match.group().replace(',', '.'))
    except:
        pass
    return None


def extract_unit_from_quantity(value):
    """
    Estrae l'unità di misura da stringhe tipo '375 g' → 'g'
    """
    if not value:
        return None
    try:
        match = re.search(r"[\d.,]+\s*([a-zA-Zµ]+)", value)
        if match:
            return match.group(1).lower()
    except:
        pass
    return None


def fetch_product_data_from_apis(ean: str):
    for domain in API_DOMAINS:
        url = f"https://{domain}/api/v0/product/{ean}.json"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    return data.get("product"), domain
        except Exception as e:
            print(f"Errore chiamando {url}: {e}")
    return None, None


def get_or_create_category_hierarchy(hierarchy: list[str]) -> Category | None:
    parent = None
    last_category = None

    for tag in hierarchy:
        name = tag.split(":")[-1].replace("-", " ").capitalize()
        category, _ = Category.objects.get_or_create(
            tag=tag,
            defaults={"name": name, "parent": parent}
        )
        if category.parent is None and parent is not None:
            category.parent = parent
            category.save()
        parent = category
        last_category = category

    return last_category


@transaction.atomic
def import_product_by_ean(ean: str, verbose=False) -> bool:
    product_data, source = fetch_product_data_from_apis(ean)

    if not product_data:
        if verbose:
            print(f"[{ean}] Prodotto non trovato.")
        return False

    # 🔤 Lingue supportate
    SUPPORTED_LANGUAGES = ['it', 'en', 'fr']
    translations = {}

    for lang in SUPPORTED_LANGUAGES:
        lang_data = {
            "product_name": product_data.get(f"product_name_{lang}"),
            "generic_name": product_data.get(f"generic_name_{lang}"),
            "ingredients_text": product_data.get(f"ingredients_text_{lang}"),
            "ingredients_text_with_allergens": product_data.get(f"ingredients_text_with_allergens_{lang}"),
            "packaging_text": product_data.get(f"packaging_text_{lang}"),
            "conservation_conditions": product_data.get(f"conservation_conditions_{lang}"),
        }
        if any(lang_data.values()):
            translations[lang] = lang_data

    defaults = {
        "name": product_data.get("product_name"),
        "brand": product_data.get("brands")[:20] if product_data.get("brands") else None,
        "quantity": extract_numeric_quantity(product_data.get("quantity")),
        "unit": normalize_unit(extract_unit_from_quantity(product_data.get("quantity"))),
        "image_url": product_data.get("image_url"),
        "ecoscore_grade": product_data.get("ecoscore_grade")[:10] if product_data.get("ecoscore_grade") else None,
        "nova_group": product_data.get("nova_group"),
        "nutrition_grade": product_data.get("nutrition_grade_fr")[:10] if product_data.get("nutrition_grade_fr") else None,
        "packaging_tags": product_data.get("packaging_tags"),
        "labels_tags": product_data.get("labels_tags"),
        "allergens_tags": product_data.get("allergens_tags"),
        "additives_tags": product_data.get("additives_tags"),
        "ingredients_text": product_data.get("ingredients_text"),
        "origins_tags": product_data.get("origins_tags"),
        "raw_data": product_data,
        "translations": translations,
        "last_synced_at": now(),
    }

    product, created = Product.objects.update_or_create(
        ean=ean,
        defaults=defaults
    )

    # Gestione categorie
    hierarchy = product_data.get("categories_hierarchy")
    if hierarchy:
        category = get_or_create_category_hierarchy(hierarchy)
        if category and not product.imported_categories.filter(pk=category.pk).exists():
            product.imported_categories.add(category)

    if verbose:
        print(f"[{ean}] {'Creato' if created else 'Aggiornato'} da {source}")
    return True


def normalize_unit(unit: str | None) -> str | None:
    """
    Normalizza l'unità di misura secondo la mappa UNIT_NORMALIZATION_MAP.
    """
    if not unit:
        return None
    return UNIT_NORMALIZATION_MAP.get(unit.strip().lower(), unit.strip().lower())
