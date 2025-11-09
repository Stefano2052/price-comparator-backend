# api/utils/unit_normalization.py

UNIT_NORMALIZATION_MAP = {
    # Peso
    "g": "g",
    "gr": "g",
    "gm": "g",
    "gram": "g",
    "grammes": "g",
    "kg": "kg",
    "kilogram": "kg",
    "klg": "kg",
    "kilograms": "kg",
    "kilogrammes": "kg",
    "milligram": "mg",
    "milligrams": "mg",
    "mg": "mg",

    # Volume
    "mililitres": "ml",
    "cl": "cl",
    "ml": "ml",
    "L": "l",
    "l": "l",
    "centilitres": "cl",
    "centilitre": "cl",
    "centiliters": "cl",
    "litre": "l",
    "litres": "l",
    "lt": "l",
    "litres": "l",
    "millilitres": "ml",

    # Qualtità
    "pz": "pz",
    "pcs": "pz",
    "pi": "pz",
    "unit": "pz",
    "units": "pz",
    "p": "pz",
    "piece": "pz",
    "pieces": "pz",

    # sconosciute o non utili
    "rice": "unknown",
    "crackers": "unknown",
    "oz": "unknown",
    "unknown": "unknown",
    "pack": "unknown",
    "portion": "unknown",
    "pouches": "unknown",
    "x": "unknown",
    "slices": "unknown",
    "sausages": "unknown",
    "lonchas": "unknown",
    "latas": "unknown",
    "pints": "unknown",
    "sachets": "unknown",
}
