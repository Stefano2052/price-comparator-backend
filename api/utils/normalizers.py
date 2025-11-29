"""
Utility functions to normalize OpenFoodFacts product data before import.
"""
import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from api.models import Product


_BRAND_CACHE: Optional[List[str]] = None


def is_valid_ean(ean: str) -> bool:
    """Validate EAN using allowed patterns (8 or 12/13 digits)."""
    if not ean:
        return False
    return bool(re.fullmatch(r"(\d{8}|\d{12,13})", str(ean).strip()))


def _normalize_decimal_string(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        normalized = normalized.quantize(Decimal("1"))
    return format(normalized, "f")


def _map_unit(unit_raw: str) -> Optional[str]:
    unit_map = {
        # weight
        "g": "g",
        "gr": "g",
        "gram": "g",
        "grams": "g",
        "grammes": "g",
        "kg": "kg",
        "kilo": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "kilogrammes": "kg",
        "mg": "g",  # converted later
        # volume
        "l": "l",
        "lt": "l",
        "liter": "l",
        "litre": "l",
        "liters": "l",
        "litres": "l",
        "ml": "ml",
        "milliliter": "ml",
        "millilitre": "ml",
        "milliliters": "ml",
        "millilitres": "ml",
        "cl": "cl",
        "centiliter": "cl",
        "centilitre": "cl",
        "centiliters": "cl",
        "centilitres": "cl",
        # pieces
        "pz": "pz",
        "pc": "pz",
        "pcs": "pz",
        "piece": "pz",
        "pieces": "pz",
        "unit": "pz",
        "units": "pz",
    }
    if not unit_raw:
        return None
    return unit_map.get(unit_raw.strip().lower())


def parse_quantity_unit(qty_raw: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Parse quantity/unit strings like "500 g", "1,5 L", "6 x 33 cl".
    Returns (Decimal quantity, base unit) or (None, None) when unrecognized.
    """
    if not qty_raw:
        return None, None

    text = str(qty_raw).strip().lower().replace(",", ".")
    if not text:
        return None, None

    multipack_match = re.match(
        r"(?P<count>\d+(?:\.\d+)?)\s*[xX]\s*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)",
        text,
    )
    if multipack_match:
        unit = _map_unit(multipack_match.group("unit"))
        if not unit:
            return None, None
        try:
            count = Decimal(multipack_match.group("count"))
            single_qty = Decimal(multipack_match.group("qty"))
            quantity = count * single_qty
            if unit == "g" and "mg" in text:
                quantity = quantity / Decimal("1000")
            return quantity, unit
        except (InvalidOperation, ValueError):
            return None, None

    single_match = re.match(
        r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)", text
    )
    if single_match:
        unit_raw = single_match.group("unit")
        unit = _map_unit(unit_raw)
        if not unit:
            return None, None
        try:
            quantity = Decimal(single_match.group("qty"))
            if unit == "g" and unit_raw.lower() == "mg":
                quantity = quantity / Decimal("1000")
            return quantity, unit
        except (InvalidOperation, ValueError):
            return None, None

    return None, None


def clean_name(raw_name: str) -> str:
    """Remove noise words and normalize spacing in product names."""
    if not raw_name:
        return ""
    name = str(raw_name)
    name = re.sub(r"\b(cassa|confezione|bottiglia|bott\.?|pezzi)\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def canonicalize_brand(raw_brand: Optional[str]) -> Optional[str]:
    """Keep the first brand, strip company suffixes, apply title case and length cap."""
    if not raw_brand:
        return None
    brand = str(raw_brand).split(",")[0]
    brand = re.sub(
        r"\b(s\.p\.a\.?|spa|srl|s\.r\.l\.?)\b",
        "",
        brand,
        flags=re.IGNORECASE,
    )
    brand = re.sub(r"[\.,]", " ", brand)
    brand = re.sub(r"\s+", " ", brand).strip()
    if not brand:
        return None
    brand = brand.title()
    return brand[:20]


def _find_similar_brand(brand: str) -> str:
    global _BRAND_CACHE

    if _BRAND_CACHE is None:
        _BRAND_CACHE = list(
            Product.objects.exclude(brand=None).values_list("brand", flat=True)
        )

    best_match = brand
    best_score = 0.0
    for existing in _BRAND_CACHE:
        score = SequenceMatcher(None, brand.lower(), existing.lower()).ratio()
        if score > 0.8 and score > best_score:
            best_match = existing
            best_score = score

    if best_match == brand:
        _BRAND_CACHE.append(brand)
    return best_match


def normalize_name(
    raw_name: str,
    brand: Optional[str],
    quantity: Optional[Decimal],
    unit: Optional[str],
) -> str:
    """Build a standardized product name: description + brand + quantity/unit."""
    base_name = clean_name(raw_name)
    brand_part = brand or ""

    if brand_part:
        base_name = re.sub(re.escape(brand_part), "", base_name, flags=re.IGNORECASE)

    base_name = re.sub(r"\s+", " ", base_name).strip()

    qty_part = ""
    if quantity is not None and unit:
        qty_str = _normalize_decimal_string(quantity)
        qty_part = f"{qty_str}{unit.upper()}"

    parts = [p for p in [base_name, brand_part] if p]
    name = " ".join(parts).strip()

    if qty_part and qty_part.lower() not in name.lower():
        name = f"{name} {qty_part}".strip()

    return name[:255]


def safe_list(value) -> Optional[List]:
    """Return the list or an empty list when the value is not a list."""
    if isinstance(value, list):
        return value
    return []


def safe_dict(value) -> Optional[Dict]:
    """Return the dict or None when not a mapping."""
    if isinstance(value, dict):
        return value
    return None


def normalize_off_product(doc: dict) -> Optional[dict]:
    """
    Normalize an OFF product document into defaults for update_or_create.
    Returns None when required checks fail.
    """
    ean = doc.get("code")
    if not is_valid_ean(ean):
        return None

    name_raw = next(
        (
            doc.get(field)
            for field in [
                "product_name_it",
                "product_name",
                "generic_name_it",
                "generic_name",
            ]
            if doc.get(field)
        ),
        None,
    )
    if not name_raw:
        return None

    brand_clean = canonicalize_brand(doc.get("brands"))
    if brand_clean:
        brand_clean = _find_similar_brand(brand_clean)
        brand_clean = brand_clean[:20]

    quantity, unit = parse_quantity_unit(doc.get("quantity"))
    normalized_name = normalize_name(name_raw, brand_clean, quantity, unit)
    if not normalized_name:
        return None

    image_url = doc.get("image_front_url") or doc.get("image_url")
    if image_url and str(image_url).startswith("//"):
        image_url = f"https:{image_url}"

    try:
        nova_group = int(doc.get("nova_group")) if doc.get("nova_group") is not None else None
    except (TypeError, ValueError):
        nova_group = None

    ingredients = doc.get("ingredients") if isinstance(doc.get("ingredients"), list) else None
    nutrients = doc.get("nutriments") if isinstance(doc.get("nutriments"), dict) else None

    translations = {}
    for lang in ["it", "en", "fr"]:
        lang_data = {}
        for field in ["product_name", "generic_name", "ingredients_text"]:
            key = f"{field}_{lang}"
            value = doc.get(key)
            if value:
                lang_data[field] = value
        if lang_data:
            translations[lang] = lang_data

    defaults = {
        "ean": str(ean),
        "name": normalized_name,
        "brand": brand_clean,
        "quantity": quantity,
        "unit": unit,
        "image_url": image_url,
        "ecoscore_grade": doc.get("ecoscore_grade"),
        "nova_group": nova_group,
        "nutrition_grade": doc.get("nutrition_grade"),
        "packaging_tags": safe_list(doc.get("packaging_tags")),
        "labels_tags": safe_list(doc.get("labels_tags")),
        "allergens_tags": safe_list(doc.get("allergens_tags")),
        "additives_tags": safe_list(doc.get("additives_tags")),
        "origins_tags": safe_list(doc.get("origins_tags")),
        "ingredients_text": doc.get("ingredients_text"),
        "ingredients": ingredients,
        "nutrients": nutrients,
        "translations": translations or None,
        "raw_data": doc,
    }

    return defaults
