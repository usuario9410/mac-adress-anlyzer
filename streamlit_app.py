"""
MAC Analyzer – Streamlit app (re‑escrito do zero)

✓ Carrega CSV com colunas contendo MACs (ex.: "mac" ou "address").
✓ Baixa lista oficial de fabricantes (IEEE OUI) ou usa fallback interno.
✓ Classifica fabricante & tipo de dispositivo.
✓ Exibe contagens de MACs únicos + gráficos de barras (Altair) para:
   • Tipos de dispositivo  • Marcas (Top 15)  • Dispositivos únicos por marca
"""

from __future__ import annotations

import datetime
import io
import textwrap
from pathlib import Path
from oui_loader import oui_lookup
from typing import Dict, Tuple

import pandas as pd
import requests
import streamlit as st
import altair as alt

# ----------------------------------------------------------------------------
# Config Streamlit
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="MAC Analyzer",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📶 MAC Analyzer – Painel de Dispositivos Detectados")

# ----------------------------------------------------------------------------
# Funções utilitárias
# ----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_official_oui() -> pd.DataFrame:
    """Baixa o CSV oficial da IEEE e devolve DataFrame {'prefix','vendor'}.
    Se falhar, usa fallback interno reduzido.
    """
    url = "https://standards-oui.ieee.org/oui/oui.csv"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df = df.rename(columns={df.columns[0]: "prefix", df.columns[1]: "vendor"})
        df["prefix"] = df["prefix"].str.replace("-", "").str.upper().str[:6]
        return df[["prefix", "vendor"]]
    except Exception as exc:
        st.warning(
            f"⚠️ Não foi possível baixar a base oficial ({exc}). "
            "Será usada uma lista de fallback limitada – fabricantes raros podem aparecer como 'Unknown'."
        )
        fallback = {
            "D8A01D": "Apple",
            "F0D1A9": "Samsung",
            "4C32D9": "Xiaomi",
            "8CBEBE": "Sony",
            "DC3A5E": "LG",
            "0017F2": "HP",
        }
        return pd.DataFrame(list(fallback.items()), columns=["prefix", "vendor"])


OUI_DF = load_official_oui()

# Heurística para tipo de dispositivo (padrões keywords → tipo)
VENDOR_KEYWORDS: Dict[str, str] = {
    "APPLE": "Smartphone / iOS",
    "IPHONE": "Smartphone / iOS",
    "IPAD": "Tablet",
    "MAC": "Computador",
    "SAMSUNG": "Smartphone / Android",
    "XIAOMI": "Smartphone / Android",
    "HUAWEI": "Smartphone / Android",
    "AIRPODS": "Fones de Ouvido",
    "BUDS": "Fones de Ouvido",
    "WATCH": "Relógio / Wearable",
    "GARMIN": "Relógio / Wearable",
    "LENOVO": "Computador",
    "HP": "Computador",
    "DELL": "Computador",
}


def classify_device(vendor: str, name: str | None = "") -> str:
    target = f"{vendor} {name}".upper()
    for kw, d_type in VENDOR_KEYWORDS.items():
        if kw in target:
            return d_type
    return "Outro"


# ----------------------------------------------------------------------------
# Upload de dados
# ----------------------------------------------------------------------------

uploaded = st.file_uploader("📤 Carregue um CSV contendo endereços MAC", type=["csv", "txt"])
if not uploaded:
    st.info("Aguardando upload…")
    st.stop()

with st.spinner("Lendo arquivo…"):
    df_raw = pd.read_csv(uploaded)

# Normaliza nomes de colunas → minúsculas
cols_lower = {c: c.lower() for c in df_raw.columns}
df_raw = df_raw.rename(columns=cols_lower)

# Detecta coluna de MAC
mac_col_candidates = [c for c in df_raw.columns if "mac" in c or "address" in c]
if not mac_col_candidates:
    st.error("⚠️ Nenhuma coluna contendo MAC encontrada! Ex.: 'mac' ou 'address'")
    st.stop()
mac_col = st.sidebar.selectbox("🗂 Selecione a coluna de MAC", mac_col_candidates)

# Seleciona colunas a exibir
optional_cols = [c for c in df_raw.columns if c != mac_col]
default_cols = [mac_col] + optional_cols[:3]
columns_to_show = st.sidebar.multiselect(
    "Colunas extras na tabela:", optional_cols, default=optional_cols[:3]
)

# Processa DataFrame
proc = df_raw.copy()
proc["mac"] = proc[mac_col].str.upper().str.replace("[^0-9A-F]", "", regex=True)
proc["prefix"] = proc["mac"].str[:6]
proc = proc.merge(OUI_DF, how="left", on="prefix")
proc["vendor"].fillna("Unknown", inplace=True)
proc["device_type"] = proc.apply(lambda r: classify_device(r["vendor"], str(r.get("device_name", ""))), axis=1)

# Métricas principais
n_total = len(proc)
n_unique = proc["mac"].nunique()
st.metric("💾 Registros", value=n_total)
st.metric("🔑 MACs únicos", value=n_unique)

# Tabela
st.subheader("📋 Dados enriquecidos")
st.dataframe(proc[[mac_col] + columns_to_show + ["vendor", "device_type"]], use_container_width=True)

# ----------------------------------------------------------------------------
# Gráficos de barras
# ----------------------------------------------------------------------------

def bar_chart(data: pd.DataFrame, x: str, title: str, max_bars: int = 15):
    counts = data.value_counts().nlargest(max_bars).reset_index()
    counts.columns = [x, "count"]
    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            y=alt.Y(f"{x}:N", sort="-x", title=""),
            x=alt.X("count:Q", title="Total"),
            tooltip=[x, "count"],
        )
        .properties(height=400, title=title)
    )
    st.altair_chart(chart, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Tipos de Dispositivo")
    bar_chart(proc["device_type"], "device_type", "Distribuição por Tipo")

with col2:
    st.subheader("🏷️ Marcas (Top 15)")
    bar_chart(proc["vendor"], "vendor", "Top 15 Fabricantes")

# ----------------------------------------------------------------------------
# Download CSV enriquecido
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def to_csv_download(df: pd.DataFrame) -> Tuple[str, str]:
    csv_data = df.to_csv(index=False).encode()
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"mac_enriched_{timestamp}.csv"
    return filename, csv_data

fname, csv_bytes = to_csv_download(proc)
st.download_button(
    label="⬇️ Baixar CSV enriquecido",
    file_name=fname,
    data=csv_bytes,
    mime="text/csv",
)

st.caption("Made with ❤️ using Streamlit + Altair | V1.0")
