
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from oui_loader import oui_lookup

st.set_page_config("MAC Analyzer", layout="wide")
st.title("📊 MAC Analyzer (OUI local via .gz)")

file = st.file_uploader("CSV com colunas de MAC", type=["csv"])
if not file:
    st.stop()

df = pd.read_csv(file)
mac_col = st.selectbox("Coluna com MAC", [c for c in df.columns if "mac" in c.lower()])
df["mac"] = df[mac_col].astype(str)
df["vendor"] = df["mac"].apply(oui_lookup)

def classificar(v: str) -> str:
    v = v.upper()
    if "APPLE" in v: return "Smartphone"
    if "SAMSUNG" in v or "XIAOMI" in v: return "Smartphone"
    if "HUAWEI" in v: return "Smartphone"
    if "PAD" in v or "TABLET" in v: return "Tablet"
    if "MAC" in v: return "Computador"
    if "GARMIN" in v or "WATCH" in v: return "Relógio"
    if "BUDS" in v or "AIRPODS" in v: return "Fones"
    return "Desconhecido"

df["tipo"] = df["vendor"].apply(classificar)

st.dataframe(df[["mac", "vendor", "tipo"]])

st.markdown("### 📊 Por Tipo")
fig1, ax1 = plt.subplots()
sns.countplot(y="tipo", data=df, order=df["tipo"].value_counts().index, ax=ax1, color="orange")
st.pyplot(fig1)

st.markdown("### 🥧 Pizza por Tipo")
fig2, ax2 = plt.subplots()
df["tipo"].value_counts().plot.pie(autopct="%.1f%%", ax=ax2)
ax2.set_ylabel("")
st.pyplot(fig2)

st.markdown("### 🏷️ Top Marcas")
top = df["vendor"].value_counts().nlargest(10).index
df_top = df[df["vendor"].isin(top)]
fig3, ax3 = plt.subplots(figsize=(10,4))
sns.countplot(x="vendor", hue="tipo", data=df_top, ax=ax3)
plt.xticks(rotation=45, ha="right")
st.pyplot(fig3)

csv_out = df.to_csv(index=False).encode()
st.download_button("⬇️ Baixar CSV enriquecido", csv_out, "resultado.csv", "text/csv")
