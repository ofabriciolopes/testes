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
# 📌 FORMATAÇÃO BR
# =========================
def fmt(v):
    if pd.isna(v):
        return "0,000"
    return f"{v:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# 🚨 FILTRO DE TELA
# =========================
if familia != "Matex" or subcategoria != "Médias":
    st.info("Selecione: Famílias → Matex → Médias")
    st.stop()

# =========================
# 📤 UPLOAD
# =========================
arquivo = st.sidebar.file_uploader(
    "Upload do arquivo Excel",
    type=["xlsx"]
)

if not arquivo:
    st.warning("Envie o arquivo na barra lateral para continuar")
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

# 🔥 DEPÓSITO MAIS FLEXÍVEL (CORREÇÃO)
col_deposito = find(df.columns, ["deposito", "dep", "armazen", "storage"])

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
df["dia"] = df["data"].dt.date

# =========================
# 🎯 FILTROS RESPONSIVOS
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

linha1 = st.columns(4)

with linha1[0]:
    f_material = mult("material", "Material")

with linha1[1]:
    f_centro = mult("centro", "Centro")

with linha1[2]:
    f_deposito = mult("deposito", "Depósito")  # 🔥 AGORA GARANTIDO

with linha1[3]:
    f_movimento = mult("movimento", "Tipo de movimento")

mask = f_material & f_centro & f_deposito & f_movimento
df = df[mask]

# =========================
# 📊 KPIs (mantido simples)
# =========================
st.write("Dados carregados:", len(df))
