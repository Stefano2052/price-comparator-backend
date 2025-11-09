import csv
from django.core.management.base import BaseCommand
from api.services.openfacts_importer import import_product_by_ean

class Command(BaseCommand):
    help = "Riprova ad importare i prodotti che avevano fallito nel log precedente"

    def handle(self, *args, **kwargs):
        input_path = "import_log.csv"
        output_path = "import_retry_log.csv"

        with open(input_path, newline="", encoding="utf-8") as infile, \
             open(output_path, "w", newline="", encoding="utf-8") as outfile:

            reader = csv.DictReader(infile)
            writer = csv.writer(outfile)
            writer.writerow(["ean", "status", "message"])

            for row in reader:
                ean = row["ean"]
                status = row["status"]

                if status != "ERROR" or not ean or ean == "-":
                    continue

                try:
                    self.stdout.write(f"🔁 Tentativo nuovo import per {ean}")
                    import_product_by_ean(ean, verbose=False)
                    writer.writerow([ean, "OK", "Importazione riuscita al retry"])
                    self.stdout.write(f"✅ Importazione riuscita per {ean}")
                except Exception as e:
                    msg = f"{type(e).__name__} – {e}"
                    writer.writerow([ean, "ERROR", msg])
                    self.stderr.write(f"❌ Errore su {ean}: {msg}")

        self.stdout.write(f"📄 Log aggiornato salvato in {output_path}")
