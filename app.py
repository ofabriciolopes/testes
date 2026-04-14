import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Sistema de Gestão de Materiais")

# =========================
# 📂 SIDEBAR - HIERARQUIA
# =========================
familias = sorted([
    "Borracha",
    "Cordinha",
    "Ingrediente",
    "Matex",
    "Negro de Fumo",
    "Tecido"
])

familia = st.sidebar.selectbox("Famílias", familias)

subcategorias = {
    "Matex": sorted(["Manuais", "Médias", "Tarefas"])
}

subcategoria = st.sidebar.selectbox(
    "Opções",
    subcategorias.get(familia, ["Em breve"])
)

st.subheader(f"📌 {familia} → {subcategoria}")

# =========================
# 📌 FORMATAÇÃO
# =========================
def fmt(v):
    if pd.isna(v):
        return "0,000"
    return f"{v:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# 🚨 TELA CERTA
# =========================
if familia != "Matex" or subcategoria != "Médias":
    st.info("Selecione: Famílias → Matex → Médias")
    st.stop()

# =========================
# 📤 UPLOAD
# =========================
arquivo = st.sidebar.file_uploader("Upload do Excel", type=["xlsx"])

if not arquivo:
    st.warning("Envie o arquivo na barra lateral")
    st.stop()

# =========================
# 📥 LEITURA
# =========================
df = pd.read_excel(arquivo, engine="openpyxl")
df.columns = df.columns.str.strip().str.lower()

def find(cols, keys):
    for c in cols:
        if any(k in c for k in keys):
            return c
    return None

col_data = find(df.columns, ["data"])
col_qtd = find(df.columns, ["quant", "qtd"])
col_material = find(df.columns, ["material", "codigo"])
col_centro = find(df.columns, ["centro"])
col_deposito = find(df.columns, ["deposito", "dep", "armazen"])
col_mov = find(df.columns, ["mov", "tipo"])

if not col_data or not col_qtd:
    st.error("❌ Colunas obrigatórias não encontradas")
    st.stop()

df = df.rename(columns={
    col_data: "data",
    col_qtd: "quantidade"
})

if col_material:
    df = df.rename(columns={col_material: "material"})
if col_centro:
    df = df.rename(columns={col_centro: "centro"})
if col_deposito:
    df = df.rename(columns={col_deposito: "deposito"})
if col_mov:
    df = df.rename(columns={col_mov: "movimento"})

# =========================
# 🧹 TRATAMENTO
# =========================
df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data"])

df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
df = df.dropna(subset=["quantidade"])
df["quantidade"] = df["quantidade"].abs()

df["ano"] = df["data"].dt.year
df["mes"] = df["data"].dt.month

# =========================
# 🎯 FILTROS
# =========================
st.markdown("### 🎯 Filtros")

def mult(col, label):
    if col and col in df.columns:
        valores = sorted(df[col].astype(str).dropna().unique())

        selecionados = st.multiselect(
            label,
            options=valores,
            default=None,
            placeholder=f"Selecionar {label}"
        )

        if len(selecionados) == 0:
            return pd.Series([True] * len(df))

        return df[col].astype(str).isin(selecionados)

    return pd.Series([True] * len(df))

c1, c2, c3, c4 = st.columns(4)

with c1:
    f_material = mult("material", "Material")

with c2:
    f_centro = mult("centro", "Centro")

with c3:
    f_deposito = mult("deposito", "Depósito")

with c4:
    f_movimento = mult("movimento", "Tipo de movimento")

df = df[f_material & f_centro & f_deposito & f_movimento]

# =========================
# 📊 BASE DE TEMPO
# =========================
hoje = datetime.today()

# =========================
# 📊 ÚLTIMO MÊS REAL DO DATASET
# =========================
df_sorted = df.sort_values("data")

ultimo_mes = df_sorted["data"].dt.to_period("M").max()
df_ult = df_sorted[df_sorted["data"].dt.to_period("M") == ultimo_mes]

media_ult = df_ult["quantidade"].sum() / 31

# =========================
# 📊 MÊS ATUAL
# =========================
df_mes = df_sorted[df_sorted["data"].dt.to_period("M") == hoje.strftime("%Y-%m")]

media_mes = df_mes["quantidade"].sum() / 31

# =========================
# 📊 TRIMESTRE E SEMESTRE
# =========================
df_tri = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=3)]
media_tri = df_tri["quantidade"].sum() / 3

df_sem = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=6)]
media_sem = df_sem["quantidade"].sum() / 6

# =========================
# 📊 ANUAL
# =========================
anos = sorted(df["ano"].unique())
medias_anos = {}

for a in anos:
    df_a = df[df["ano"] == a]
    medias_anos[a] = df_a["quantidade"].sum() / 12

# =========================
# 📊 KPIs
# =========================
st.markdown("### 📊 Consumo Médio")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Ano", fmt(medias_anos.get(hoje.year, 0)))
k2.metric("Semestre", fmt(media_sem))
k3.metric("Trimestre", fmt(media_tri))
k4.metric("Último mês", fmt(media_ult))
k5.metric("Mês atual", fmt(media_mes))

# =========================
# 📅 TABELA ANUAL
# =========================
st.markdown("### 📅 Médias por Ano")

df_anos = pd.DataFrame({
    "Ano": list(medias_anos.keys()),
    "Consumo médio": list(medias_anos.values())
}).sort_values("Ano")

st.dataframe(
    df_anos.style.format({"Consumo médio": "{:,.3f}"}),
    use_container_width=True
)

# =========================
# 🔍 DEBUG (opcional)
# =========================
st.write("Último mês detectado:", ultimo_mes)
st.write("Total último mês:", df_ult["quantidade"].sum())
