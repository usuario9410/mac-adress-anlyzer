import streamlit as st
import pandas as pd
import base64, gzip, io

st.set_page_config("MAC Analyzer", layout="wide")
st.title("🔎 MAC Analyzer (OUI embutido)")

OUI_B64 = """H4sICGcsEWgEAG91aSAoMSkuY3N2ANRdyXLbzBG+pyrvMKVUJXYVyB/7kksKGAASLXH5ScqyfINISE..."""

@st.cache_data
def load_oui():
    raw = gzip.decompress(base64.b64decode(OUI_B64))
    df = pd.read_csv(io.BytesIO(raw))
    df["prefix"] = df["Assignment"].str.replace("-", "").str.upper()
    df = df.rename(columns={"Organization Name": "vendor"})
    return df[["prefix", "vendor"]]

OUI_DF = load_oui()

def get_vendor(mac: str) -> str:
    pfx = mac.replace(":", "").replace("-", "").upper()[:6]
    row = OUI_DF.loc[OUI_DF["prefix"] == pfx]
    return row["vendor"].values[0] if not row.empty else "Unknown"

uploaded = st.file_uploader("📤 Envie CSV com MACs", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    mac_col = st.selectbox("Coluna com MAC", [c for c in df.columns if "mac" in c.lower()])
    df["mac"] = df[mac_col].astype(str)
    df["vendor"] = df["mac"].apply(get_vendor)
    st.dataframe(df)
    st.download_button("⬇️ Baixar CSV", df.to_csv(index=False).encode(), "mac_enriquecido.csv", "text/csv")