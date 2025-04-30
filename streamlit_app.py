
import streamlit as st
import pandas as pd
from utils.preprocess import load_data
from utils.enrichment import enrich
from utils.viz import top_brands, hourly_heatmap
import matplotlib.pyplot as plt

st.set_page_config(page_title="MAC Dashboard", layout="wide")

st.title("📊 MAC Address Dashboard")

uploaded = st.sidebar.file_uploader("📤 Envie sua planilha (CSV ou XLSX)", type=['csv', 'xlsx'])
if not uploaded:
    st.info("Faça upload de um arquivo para começar.")
    st.stop()

with st.spinner("Carregando dados..."):
    df = load_data(uploaded)
    df = enrich(df)

# Sidebar filters
with st.sidebar:
    st.markdown("### Filtros")
    min_date, max_date = df['timestamp'].min().date(), df['timestamp'].max().date()
    date_range = st.date_input("Intervalo de datas", (min_date, max_date))
    if date_range and len(date_range) == 2:
        df = df[(df['timestamp'].dt.date >= date_range[0]) & (df['timestamp'].dt.date <= date_range[1])]
    brands_selected = st.multiselect("Marcas", sorted(df['brand'].unique()))
    if brands_selected:
        df = df[df['brand'].isin(brands_selected)]
    types_selected = st.multiselect("Tipos de dispositivo", sorted(df['device_type'].unique()))
    if types_selected:
        df = df[df['device_type'].isin(types_selected)]

# KPIs
unique_devices = df['mac'].nunique()
col1, col2, col3 = st.columns(3)
col1.metric("Dispositivos únicos", unique_devices)
col2.metric("Data inicial", df['timestamp'].min().date())
col3.metric("Data final", df['timestamp'].max().date())

# Top marcas
st.subheader("Top 10 marcas")
st.bar_chart(top_brands(df))

# Heatmap
st.subheader("Heatmap dia × hora")
fig = hourly_heatmap(df)
st.pyplot(fig)

# Download
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Baixar CSV filtrado", data=csv, file_name="mac_filtrado.csv", mime='text/csv')
