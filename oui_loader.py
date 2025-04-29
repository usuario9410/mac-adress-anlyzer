import gzip, csv
from pathlib import Path

def oui_lookup(mac: str) -> str:
    try:
        mac = mac.replace("-", "").replace(":", "").upper()
        prefix = mac[:6]

        path = Path(__file__).with_name("oui.csv.gz")
        with gzip.open(path, "rt", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Assignment", "").upper() == prefix:
                    return row.get("Organization Name", "Unknown")
    except Exception as e:
        print("Erro no OUI lookup:", e)
    return "Unknown"
