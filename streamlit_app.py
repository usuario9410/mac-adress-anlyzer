
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config("MAC Analyzer Avançado", layout="wide")
st.title("🔍 MAC Analyzer – Heurística Refinada")

file = st.file_uploader("📤 Envie planilha com MACs e colunas complementares", type=["xlsx", "csv"])
if not file:
    st.stop()

if file.name.endswith(".xlsx"):
    df = pd.read_excel(file, engine="openpyxl")
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
    raw = " ".join(str(v).lower() if isinstance(v, str) else str(v).lower() for v in row.values())
    if any(k in raw for k in ["airpods", "buds", "earbuds", "beats"]): return "Fones"
    if any(k in raw for k in ["watch", "galaxy watch", "mi watch", "wearable"]): return "Relógio"
    if any(k in raw for k in ["phone", "smartphone", "iphone", "galaxy s"]): return "Smartphone"
    if any(k in raw for k in ["ipad", "tablet"]): return "Tablet"
    if any(k in raw for k in ["macbook", "notebook", "computer", "pc"]): return "Computador"
    if "sensor" in raw: return "Sensor"
    if "ble" in raw or "bluetooth" in raw: return "Dispositivo BLE"
    return "Outro"

df["marca"] = df.apply(detectar_marca, axis=1)
df["tipo"] = df.apply(detectar_tipo, axis=1)

st.markdown("### 📋 Dispositivos identificados")
st.dataframe(df[["mac", "marca", "tipo"]])

st.markdown("### 📊 Gráfico de Tipos")
fig1, ax1 = plt.subplots()
sns.countplot(y="tipo", data=df, order=df["tipo"].value_counts().index, ax=ax1, color="#e2950f")
st.pyplot(fig1)

st.markdown("### 🥧 Distribuição por Tipo")
fig2, ax2 = plt.subplots()
df["tipo"].value_counts().plot.pie(autopct="%.1f%%", ax=ax2, colors=sns.color_palette("pastel"))
ax2.set_ylabel("")
st.pyplot(fig2)

st.markdown("### 🏷️ Top Marcas por Tipo")
fig3, ax3 = plt.subplots(figsize=(10,5))
top = df["marca"].value_counts().nlargest(10).index
sns.countplot(x="marca", hue="tipo", data=df[df["marca"].isin(top)], ax=ax3)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
st.pyplot(fig3)

csv_out = df.to_csv(index=False).encode()
st.download_button("⬇️ Baixar CSV enriquecido", csv_out, "resultado_enriquecido.csv", "text/csv")
