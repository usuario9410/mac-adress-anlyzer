
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
                if row["Assignment"].replace("-", "").upper() == prefix:
                    return row["Organization Name"]
    except Exception:
        pass
    return "Unknown"
