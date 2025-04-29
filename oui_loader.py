
"""Offline OUI lookup helper.

If the compressed file ``oui.csv.gz`` is present in the same directory this
module will load the full IEEE OUI list from it.  Otherwise it falls back to
a _very_ small built‑in dictionary that is enough to keep the application
running, but unknown vendors will be reported as ``Unknown``.

You can download the official list from:
    https://standards-oui.ieee.org/oui/oui.csv
and compress it with:

    gzip -9c oui.csv > oui.csv.gz

Then simply place the resulting file alongside this module.

The public API intentionally mirrors the ``ieee_oui.oui_lookup`` helper used
before so the rest of the code base does **not** need to change.

Example
-------
>>> from oui_loader import oui_lookup
>>> oui_lookup('B0:D5:9D:12:34:56')
'Apple, Inc.'
"""

from __future__ import annotations

import csv
import gzip
from importlib.resources import files
from pathlib import Path
from typing import Dict

# --------------------------------------------------------------------------- #
# 1. Built‑in minimal fallback database (prefix -> vendor string)
# --------------------------------------------------------------------------- #
_FALLBACK: Dict[str, str] = {
    '00:00:00': 'Xerox Corporation',
    '28:CF:E9': 'Apple, Inc.',
    'B8:27:EB': 'Raspberry Pi Foundation',
}


def _load_official() -> Dict[str, str] | None:
    """Try to load an on‑disk ``oui.csv.gz`` that sits next to this file."""
    path = Path(__file__).with_name('oui.csv.gz')
    if not path.is_file():
        return None

    vendors: Dict[str, str] = {}
    try:
        with gzip.open(path, 'rt', newline='') as gz:
            reader = csv.DictReader(gz)
            for row in reader:
                # The IEEE CSV contains prefixes without separators ― we store
                # them colon‑separated and **uppercase** for fast lookup.
                prefix = ':'.join(row['Assignment'][i : i + 2] for i in range(0, 6, 2))
                vendors[prefix.upper()] = row['Organization Name']
    except Exception as exc:  # pragma: no cover
        # Corrupted file?  Fall back silently and let the app continue.
        print(f'[OUI] Unable to load official list: {exc}')

    return vendors or None


# --------------------------------------------------------------------------- #
# 2. Public lookup helpers
# --------------------------------------------------------------------------- #
_VENDOR_DB = _load_official() or _FALLBACK


def oui_lookup(mac: str) -> str:
    """Return the vendor string for *mac* (case‑insensitive)."""
    # Normalise MAC into ``XX:XX:XX``
    mac = mac.replace('-', ':').upper()
    prefix = ':'.join(mac.split(':')[0:3])
    return _VENDOR_DB.get(prefix, 'Unknown')
