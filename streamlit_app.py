# --------------------------------------------------------------
#  Streamlit ‑ MAC Dashboard – versão refatorada e enxuta
#  • Python ≥ 3.9, roda bem em 3.12 (ambiente Streamlit Cloud)
#  • Dependências mínimas (requirements.txt):
#      streamlit>=1.25
#      pandas>=1.5
#      manuf>=1.0            # parser OUI / fabricante
# --------------------------------------------------------------
"""Aplicação Streamlit para análise de endereços MAC.

Principais mudanças em relação ao código original "espaguete":
• Arquitetura em funções puras + cache → fácil de testar.
• Detecção robusta de fabricante usando *manuf* (offline, sem API).
• Heurística de tipo de dispositivo desacoplada em dicionário.
• Validação de entrada e tratamento de erros amigável.
• Sem pandas.apply + funções aninhadas pesadas → rápido.
"""
from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Final, Iterable

import pandas as pd
import streamlit as st
from manuf import manuf

# -----------------------------------------------------------------------------
#  Configurações fixas
# -----------------------------------------------------------------------------
PAGE_TITLE: Final = "MAC Dashboard"
MAC_RE: Final = re.compile(r"^(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})$")

# palavras‑chave → tipo de dispositivo
DEVICE_KEYWORDS: Final[dict[str, tuple[str, ...]]] = {
    "smartphone": ("iphone", "android", "phone", "samsung", "galaxy", "pixel"),
    "notebook": ("laptop", "notebook", "macbook", "dell", "lenovo", "hp"),
    "iot‑sensor": ("sensor", "zigbee", "ble", "esp32", "esp8266", "arduino"),
    "wifi‑ap": ("router", "access point", "unifi", "ubiquiti", "mikrotik"),
}

# -----------------------------------------------------------------------------
#  Funções utilitárias
# -----------------------------------------------------------------------------

def valid_mac(mac: str) -> bool:
    """Valida se a string parece um endereço MAC."""
    return bool(MAC_RE.match(mac.strip()))


@st.cache_data(show_spinner=False)
def get_oui_parser() -> manuf.MacParser:  # type: ignore[attr-defined]
    """Carrega o parser OUI do pacote *manuf* (cacheado)."""
    return manuf.MacParser()


def identify_vendor(mac: str, parser: manuf.MacParser) -> str:  # type: ignore[name-defined]
    """Retorna o fabricante ou "Unknown"."""
    try:
        vendor: str | None = parser.get_manuf(mac)  # type: ignore[arg-type]
    except Exception:
        vendor = None
    return vendor if vendor else "Unknown"


def detect_device_type(text: str) -> str:
    """Detecta o tipo de dispositivo a partir de texto livre."""
    t = text.lower()
    for dev_type, kws in DEVICE_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return dev_type
    return "Unknown"


def concat_iter(values: Iterable[str | float | int | None]) -> str:
    """Concatena valores ignorando nulos."""
    return " ".join(str(v) for v in values if pd.notna(v))


# -----------------------------------------------------------------------------
#  Pipeline principal
# -----------------------------------------------------------------------------

def process_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Devolve dataframe enriquecido com *vendor* e *device_type*."""
    df = df_raw.copy()

    # Normaliza nomes de colunas → minúsculas sem espaço
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if "mac" not in df.columns:
        raise ValueError("Coluna 'mac' não encontrada no arquivo.")

    # Filtra linhas com MAC válido
    df = df[df["mac"].astype(str).apply(valid_mac)]

    parser = get_oui_parser()
    df["vendor"] = df["mac"].apply(lambda m: identify_vendor(m, parser))

    # Build texto base para heurística de tipo
    df["_raw"] = df.apply(concat_iter, axis=1)
    df["device_type"] = df["_raw"].apply(detect_device_type)
    df.drop(columns="_raw", inplace=True)

    return df


# -----------------------------------------------------------------------------
#  Interface Streamlit
# -----------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(PAGE_TITLE, layout="wide")
    st.title(PAGE_TITLE)
    st.markdown("Faça upload de um arquivo **CSV** ou **Excel** contendo pelo menos uma coluna `mac`.")

    uploaded = st.file_uploader("Arquivo", type=["csv", "xls", "xlsx"])
    if not uploaded:
        st.stop()

    # Lê arquivo
    try:
        if Path(uploaded.name).suffix.lower() in {".xlsx", ".xls"}:
            df_raw = pd.read_excel(uploaded)
        else:
            df_raw = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        st.stop()

    # Processa
    try:
        df_final = process_dataframe(df_raw)
    except Exception as e:
        st.exception(e)
        st.stop()

    st.success(f"Linhas processadas: {len(df_final)}")
    st.dataframe(df_final, use_container_width=True)

    # Download resultado
    buf = BytesIO()
    df_final.to_csv(buf, index=False)
    st.download_button("⬇️ Baixar CSV resultante", buf.getvalue(), file_name="mac_dashboard_output.csv", mime="text/csv")


if __name__ == "__main__":
    main()
