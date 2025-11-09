from django.core.management.base import BaseCommand
import requests
from collections import defaultdict
from time import sleep

DATASETS = [
    "https://world.openfoodfacts.org",
    "https://world.openbeautyfacts.org",
    "https://world.openpetfoodfacts.org",
]

def split_and_clean(val):
    if not val:
        return []
    return [v.strip() for v in val.split(",") if v.strip()]

def fetch_all_products(base_url, max_pages=10):
    all_products = []
    print(f"\n🔎 Analisi da: {base_url}")
    page = 1
    while page <= max_pages:
        url = f"{base_url}/cgi/search.pl?search_simple=1&action=process&json=1&page_size=1000&page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Errore nella richiesta a {url}")
            break

        data = response.json()
        products = data.get("products", [])
        if not products:
            break

        all_products.extend(products)
        print(f"✅ Pagina {page}: {len(products)} prodotti")
        page += 1
        sleep(0.5)

    print(f"📦 Totale prodotti scaricati: {len(all_products)}")
    return all_products

def analyze(products):
    counters = {
        "countries_tags": defaultdict(int),
        "origins_tags": defaultdict(int),
        "manufacturing_places": defaultdict(int),
        "purchase_places": defaultdict(int),
    }

    for p in products:
        for c in p.get("countries_tags", []):
            counters["countries_tags"][c] += 1

        for o in p.get("origins_tags", []):
            counters["origins_tags"][o] += 1

        for m in split_and_clean(p.get("manufacturing_places", "")):
            counters["manufacturing_places"][m] += 1

        for pp in split_and_clean(p.get("purchase_places", "")):
            counters["purchase_places"][pp] += 1

    return counters

def print_results(counters, title):
    print(f"\n📊 {title}")
    for key, counter in counters.items():
        print(f"\n➡️ {key}")
        for value in sorted(counter, key=counter.get, reverse=True)[:50]:
            print(f"{value}: {counter[value]}")

class Command(BaseCommand):
    help = "Estrae e analizza dati geografici dai dataset OpenFacts"

    def handle(self, *args, **options):
        global_counters = {
            "countries_tags": defaultdict(int),
            "origins_tags": defaultdict(int),
            "manufacturing_places": defaultdict(int),
            "purchase_places": defaultdict(int),
        }

        for base_url in DATASETS:
            products = fetch_all_products(base_url, max_pages=10)
            counters = analyze(products)

            for key in global_counters:
                for val, count in counters[key].items():
                    global_counters[key][val] += count

        print_results(global_counters, "TOTALE (tutti i dataset)")
