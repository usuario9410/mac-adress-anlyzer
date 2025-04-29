
import gzip, csv
from pathlib import Path

_FALLBACK = {
    'B8:27:EB': 'Raspberry Pi Foundation',
    'D8:50:E6': 'Google LLC',
}

def oui_lookup(mac: str) -> str:
    mac = mac.replace('-', ':').upper()
    prefix = ':'.join(mac.split(':')[0:3])
    try:
        path = Path(__file__).with_name("oui.csv.gz")
        with gzip.open(path, "rt", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pfx = ':'.join(row["Assignment"][i:i+2] for i in range(0, 6, 2))
                if pfx == prefix:
                    return row["Organization Name"]
    except Exception:
        pass
    return _FALLBACK.get(prefix, "Unknown")
