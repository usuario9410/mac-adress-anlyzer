# ───────────────────────────────────────────────────────────────
#  MAC Dashboard  ·  analisador-mac-adress
#  Author: você :)
# ───────────────────────────────────────────────────────────────
import io
from pathlib import Path
from functools import lru_cache

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from manuf import manuf   # ← fornecido pelo pacote pymanuf

st.set_page_config(page_title="MAC Dashboard",
                   layout="wide",
                   page_icon="📡")

# ────────────────────────────
#  📥  Upload
# ────────────────────────────
st.title("📡 Analisador de MAC address")
arquivo = st.file_uploader("Selecione um CSV / XLSX contendo MAC, nome do dispositivo, etc.",
                           type=["csv", "xlsx"])

if arquivo is None:
    st.info("Faça o upload de um arquivo para começar ⬆️")
    st.stop()

# ────────────────────────────
#  📄  Leitura do dataset
# ────────────────────────────
try:
    df = (pd.read_csv(arquivo) if arquivo.name.endswith(".csv")
          else pd.read_excel(arquivo))
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

# Nome uniformizado de colunas essenciais
possiveis = {"mac": "mac", "mac_address": "mac", "endereco_mac": "mac",
             "name": "device_name", "device": "device_name", "device_name": "device_name"}
df.rename(columns={c: possiveis.get(c.lower(), c) for c in df.columns},
          inplace=True)

if "mac" not in df.columns:
    st.error("Coluna de MAC address não encontrada!")
    st.stop()

# ────────────────────────────
#  🏷  Marca & Tipo
# ────────────────────────────
parser = manuf.MacParser()   # cache interno do próprio manuf


@lru_cache
def _categoria_por_palavra(chave: str) -> str | None:
    """Define categoria a partir de palavras-chave encontradas."""
    chave = chave.lower()
    if any(k in chave for k in ("cam", "camera")):
        return "Câmera"
    if any(k in chave for k in ("phone", "smart", "iphone", "android")):
        return "Smartphone"
    if any(k in chave for k in ("tv", "chromecast", "firetv", "roku")):
        return "Smart TV / Media"
    if any(k in chave for k in ("printer", "hp", "epson", "brother", "canon")):
        return "Impressora"
    if any(k in chave for k in ("watch", "wear", "garmin", "fitbit")):
        return "Wearable"
    return None


def detectar_tipo(row: pd.Series) -> tuple[str, str]:
    """
    • manuf → fabricante a partir do OUI
    • heurística → tipo de equipamento
    Retorna (fabricante, tipo)
    """
    mac = str(row.get("mac", ""))[:8]           # “AA:BB:CC”
    fabricante = parser.get_manuf(mac) or "Unknown"

    raw = " ".join(str(v) for v in row.values() if pd.notna(v)).lower()

    tipo = (_categoria_por_palavra(raw)
            or ("Roteador"       if "router" in raw or "gateway" in raw else None)
            or ("Notebook"       if "laptop" in raw or "notebook" in raw else None)
            or ("Tablet"         if "tablet" in raw else None)
            or ("IoT Genérico"))
    return fabricante, tipo


# Aplicar em lote — lightning-fast 👍
df[["fabricante", "tipo"]] = (
    df.apply(detectar_tipo, axis=1, result_type="expand")
)

# ────────────────────────────
#  📊  Interface
# ────────────────────────────
col_filtro, col_plot = st.columns([1, 3])

with col_filtro:
    st.subheader("Filtros")
    fabricante_sel = st.multiselect("Fabricante", sorted(df["fabricante"].unique()))
    tipo_sel       = st.multiselect("Tipo",       sorted(df["tipo"].unique()))

filtro = pd.Series(True, index=df.index)
if fabricante_sel:
    filtro &= df["fabricante"].isin(fabricante_sel)
if tipo_sel:
    filtro &= df["tipo"].isin(tipo_sel)

df_view = df[filtro]

with col_plot:
    st.subheader("Distribuição de dispositivos")

    fig, ax = plt.subplots(figsize=(8, 5))
    (df_view["tipo"]
     .value_counts()
     .sort_values(ascending=True)
     .plot(kind="barh", ax=ax))
    ax.set_xlabel("Quantidade")
    st.pyplot(fig)

st.divider()
st.subheader("📑 Dados brutos filtrados")
st.dataframe(df_view, use_container_width=True)

# Download
buffer = io.BytesIO()
df_view.to_excel(buffer, index=False)
st.download_button("🔽 Baixar resultado (.xlsx)",
                   buffer.getvalue(),
                   file_name="resultado_mac.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
