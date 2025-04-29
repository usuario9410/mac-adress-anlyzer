
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from oui_loader import oui_lookup

st.set_page_config("MAC Dashboard", layout="wide")
st.title("📊 MAC Analyzer - Dashboard de Dispositivos")

file = st.file_uploader("Envie um CSV com colunas de MAC", type=["csv"])
if not file:
    st.stop()

df = pd.read_csv(file)
mac_col = st.selectbox("Coluna com MAC", [c for c in df.columns if "mac" in c.lower()])
df["mac_clean"] = df[mac_col].astype(str).str.upper().str.replace(":", "").str.replace("-", "").str[:12]
df["prefix"] = df["mac_clean"].str[:6]
df["prefix_fmt"] = df["prefix"].str[:2] + ":" + df["prefix"].str[2:4] + ":" + df["prefix"].str[4:6]
df["vendor"] = df["prefix_fmt"].apply(oui_lookup)

st.write("Exemplo:", oui_lookup("A4:DA:22:00:11:22"))

def classificar(v: str) -> str:
    v = v.upper()
    if "APPLE" in v or "IPHONE" in v: return "Smartphone"
    if "SAMSUNG" in v or "XIAOMI" in v: return "Smartphone"
    if "HUAWEI" in v: return "Smartphone"
    if "PAD" in v or "TABLET" in v: return "Tablet"
    if "MAC" in v: return "Computador"
    if "GARMIN" in v or "WATCH" in v: return "Relógio"
    if "BUDS" in v or "AIRPODS" in v or "FONE" in v: return "Fones"
    return "Desconhecido"

df["tipo"] = df["vendor"].apply(classificar)

st.markdown("### 📋 Tabela enriquecida")
st.dataframe(df[["mac_clean", "vendor", "tipo"]])

st.markdown("### 📊 Dispositivos por Tipo")
fig1, ax1 = plt.subplots()
sns.countplot(y="tipo", data=df, order=df["tipo"].value_counts().index, ax=ax1, color="orange")
ax1.set_xlabel("Quantidade")
st.pyplot(fig1)

st.markdown("### 🥧 Distribuição por Tipo (pizza)")
fig2, ax2 = plt.subplots()
df["tipo"].value_counts().plot.pie(autopct="%.1f%%", ax=ax2, colors=sns.color_palette("pastel"))
ax2.set_ylabel("")
st.pyplot(fig2)

st.markdown("### 🏷️ Top 10 Marcas - Distribuição por Tipo")
top = df["vendor"].value_counts().nlargest(10).index
df_top = df[df["vendor"].isin(top)]
fig3, ax3 = plt.subplots(figsize=(10, 4))
sns.countplot(x="vendor", hue="tipo", data=df_top, ax=ax3)
plt.xticks(rotation=45, ha="right")
st.pyplot(fig3)

csv_out = df.to_csv(index=False).encode()
st.download_button("⬇️ Baixar CSV enriquecido", csv_out, "resultado_mac.csv", "text/csv")
