import requests
import csv
import time
from django.core.management.base import BaseCommand
from api.services.openfacts_importer import import_product_by_ean

DATASETS = [
    "https://world.openfoodfacts.org",
    "https://world.openbeautyfacts.org",
    "https://world.openpetfoodfacts.org",
]

MAX_RETRIES = 3
RETRY_DELAY = 2  # secondi

class Command(BaseCommand):
    help = "Importa tutti i prodotti disponibili con EAN da OpenFoodFacts, BeautyFacts, PetFoodFacts"

    def handle(self, *args, **options):
        failed_eans = []
        total_attempted = 0
        total_success = 0
        total_skipped = 0

        log_file = open("import_log.csv", "w", newline="", encoding="utf-8")
        csv_writer = csv.writer(log_file)
        csv_writer.writerow(["ean", "status", "message"])

        for base_url in DATASETS:
            self.stdout.write(f"\n🔍 Inizio importazione da {base_url}")
            page = 1
            while True:
                url = f"{base_url}/cgi/search.pl?search_simple=1&action=process&json=1&page_size=1000&page={page}"
                response = requests.get(url)
                if response.status_code != 200:
                    error_msg = f"Errore nella richiesta a {url}"
                    self.stderr.write(error_msg)
                    csv_writer.writerow(["-", "ERROR", error_msg])
                    break

                data = response.json()
                products = data.get("products", [])
                if not products:
                    break

                for p in products:
                    ean = p.get("code")
                    if not ean or len(ean) < 8:
                        msg = "EAN mancante o troppo corto"
                        self.stderr.write(f"⛔ Skippato: {ean} – {msg}")
                        csv_writer.writerow([ean or "-", "SKIPPED", msg])
                        total_skipped += 1
                        continue

                    total_attempted += 1
                    success = False
                    for attempt in range(1, MAX_RETRIES + 1):
                        try:
                            import_product_by_ean(ean, verbose=False)
                            self.stdout.write(f"✔️ Importato {ean} (tentativo {attempt})")
                            csv_writer.writerow([ean, "OK", f"Importato correttamente (tentativo {attempt})"])
                            total_success += 1
                            success = True
                            break
                        except Exception as e:
                            msg = f"{type(e).__name__} – {e}"
                            self.stderr.write(f"❌ Tentativo {attempt} fallito per {ean}: {msg}")
                            if attempt == MAX_RETRIES:
                                csv_writer.writerow([ean, "ERROR", msg])
                                failed_eans.append((ean, msg))
                            else:
                                time.sleep(RETRY_DELAY)

                page += 1

        log_file.close()

        # 🔁 Retry finale per gli EAN falliti nei 3 tentativi
        retry_success = 0
        retry_fail = 0

        if failed_eans:
            self.stdout.write("\n🔁 Retry finale per EAN falliti nei 3 tentativi iniziali")
            retry_file = open("import_retry_final.csv", "w", newline="", encoding="utf-8")
            retry_writer = csv.writer(retry_file)
            retry_writer.writerow(["ean", "status", "message"])

            for ean, old_msg in failed_eans:
                try:
                    import_product_by_ean(ean, verbose=False)
                    self.stdout.write(f"✅ Recuperato {ean} nel retry finale")
                    retry_writer.writerow([ean, "OK", "Importato correttamente nel retry finale"])
                    retry_success += 1
                except Exception as e:
                    msg = f"{type(e).__name__} – {e}"
                    self.stderr.write(f"❌ Ancora errore su {ean} nel retry finale: {msg}")
                    retry_writer.writerow([ean, "ERROR", msg])
                    retry_fail += 1

            retry_file.close()

        # 📊 Riepilogo finale a schermo
        self.stdout.write("\n📊 RIEPILOGO FINALE:")
        self.stdout.write(f"🔢 Prodotti totali validi processati: {total_attempted}")
        self.stdout.write(f"✅ Importati correttamente al primo giro: {total_success}")
        self.stdout.write(f"🔄 Importati nel retry finale: {retry_success}")
        self.stdout.write(f"❌ Falliti definitivamente: {retry_fail}")
        self.stdout.write(f"⛔ Skippati (EAN assente o invalido): {total_skipped}")
        self.stdout.write("\n📁 Log principale: import_log.csv")
        self.stdout.write("📁 Log retry finale: import_retry_final.csv")
