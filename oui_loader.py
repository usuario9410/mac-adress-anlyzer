import gzip
import csv
from pathlib import Path

def oui_lookup(mac: str) -> str:
    """
    Retorna o fabricante baseado no prefixo do MAC (via arquivo oui.csv.gz).

    Exemplo:
    >>> oui_lookup("A4:DA:22:00:11:22")  →  "Apple, Inc."
    """
    try:
        # Normaliza MAC: remove separadores e pega prefixo (6 hex dígitos)
        mac = mac.replace(":", "").replace("-", "").upper()
        prefix = mac[:6]

        # Caminho do arquivo .gz
        path = Path(__file__).with_name("oui.csv.gz")
        if not path.exists():
            return "Unknown"

        # Lê o .gz e compara com a coluna Assignment (prefixo sem separador)
        with gzip.open(path, "rt", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Assignment", "").replace("-", "").upper() == prefix:
                    return row.get("Organization Name", "Unknown")

    except Exception as e:
        print("Erro ao carregar OUI:", e)

    return "Unknown"
