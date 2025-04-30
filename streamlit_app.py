
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config("MAC Heurístico", layout="wide")
st.title("🔍 MAC Analyzer com Heurística Avançada")

file = st.file_uploader("📤 Envie planilha com MACs e colunas complementares", type=["xlsx", "csv"])
if not file:
    st.stop()

if file.name.endswith(".xlsx"):
    df = pd.read_excel(file)
else:
    df = pd.read_csv(file)

df.columns = [c.strip().lower() for c in df.columns]
df["mac"] = df["mac"].astype(str).str.upper()

def detectar_marca(row):
    nome = str(row.get("company name", "")).upper()
    if "APPLE" in nome: return "Apple"
    if "SAMSUNG" in nome: return "Samsung"
    if "XIAOMI" in nome: return "Xiaomi"
    if "HUAWEI" in nome: return "Huawei"
    if "SONY" in nome: return "Sony"
    return "Desconhecido"

def detectar_tipo(row):
    ap = str(row.get("appearance name", "")).lower()
    uuid = str(row.get("uuid service name ad03", "")).lower()
    nome = str(row.get("company name", "")).lower()

    if "headphone" in ap or "earbuds" in ap or "buds" in uuid: return "Fones"
    if "watch" in ap or "wearable" in ap: return "Relógio"
    if "phone" in ap or "smartphone" in ap: return "Smartphone"
    if "tablet" in ap or "ipad" in ap: return "Tablet"
    if "computer" in ap or "macbook" in ap: return "Computador"
    if "sensor" in ap: return "Sensor"
    if "light" in ap: return "IoT / Smartlight"
    if "ble" in uuid: return "Bluetooth Device"
    if "airpods" in uuid: return "Fones"
    return "Outro"

df["marca"] = df.apply(detectar_marca, axis=1)
df["tipo"] = df.apply(detectar_tipo, axis=1)

st.markdown("### 📋 Dispositivos identificados")
st.dataframe(df[["mac", "marca", "tipo"]])

st.markdown("### 📊 Gráfico de Tipos")
fig1, ax1 = plt.subplots()
sns.countplot(y="tipo", data=df, order=df["tipo"].value_counts().index, ax=ax1, color="orange")
st.pyplot(fig1)

st.markdown("### 🥧 Distribuição por Tipo")
fig2, ax2 = plt.subplots()
df["tipo"].value_counts().plot.pie(autopct="%.1f%%", ax=ax2)
ax2.set_ylabel("")
st.pyplot(fig2)

st.markdown("### 🏷️ Top Marcas")
fig3, ax3 = plt.subplots(figsize=(10,4))
top = df["marca"].value_counts().nlargest(10).index
sns.countplot(x="marca", hue="tipo", data=df[df["marca"].isin(top)], ax=ax3)
plt.xticks(rotation=45)
st.pyplot(fig3)

csv_out = df.to_csv(index=False).encode()
st.download_button("⬇️ Baixar CSV enriquecido", csv_out, "resultado_enriquecido.csv", "text/csv")
