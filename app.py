import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Sistema de Gestão de Materiais")

# =========================
# 📂 SIDEBAR - UPLOAD (NOVO FLUXO)
# =========================
st.sidebar.title("📁 Controle")

arquivo = st.sidebar.file_uploader(
    "Upload do Excel",
    type=["xlsx"]
)

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
# 🚨 SEM ARQUIVO
# =========================
if not arquivo:
    st.info("📤 Faça upload de um arquivo na barra lateral para começar")
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
col_deposito = find(df.columns, ["deposito"])
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
# 🎯 FILTROS (CORPO)
# =========================
st.markdown("### 🎯 Filtros")

def filtro(col, label):
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

mask = (
    filtro("material", "Material") &
    filtro("centro", "Centro") &
    filtro("deposito", "Depósito") &
    filtro("movimento", "Tipo de movimento")
)

df = df[mask]

# =========================
# 📊 PERÍODOS
# =========================
hoje = datetime.today()
ano_atual = hoje.year
mes_atual = hoje.month

if mes_atual == 1:
    mes_ult = 12
    ano_ult = ano_atual - 1
else:
    mes_ult = mes_atual - 1
    ano_ult = ano_atual

# =========================
# 📊 MÉTRICAS
# =========================
anos = sorted(df["ano"].unique())
medias_anos = {}

for a in anos:
    medias_anos[a] = df[df["ano"] == a]["quantidade"].sum() / 12

df_sem = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=6)]
media_sem = df_sem["quantidade"].sum() / 6

df_tri = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=3)]
media_tri = df_tri["quantidade"].sum() / 3

df_ult = df[(df["ano"] == ano_ult) & (df["mes"] == mes_ult)]
media_ult = df_ult["quantidade"].sum() / 31

df_mes = df[(df["ano"] == ano_atual) & (df["mes"] == mes_atual)]
dias = df_mes["dia"].nunique()
media_mes = df_mes["quantidade"].sum() / dias if dias > 0 else 0

# =========================
# 📊 UI
# =========================
st.markdown("### 📊 Consumo Médio")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Ano", fmt(medias_anos.get(ano_atual, 0)))
c2.metric("Semestre", fmt(media_sem))
c3.metric("Trimestre", fmt(media_tri))
c4.metric("Último mês", fmt(media_ult))
c5.metric("Mês atual", fmt(media_mes))

# =========================
# 📅 TABELA ANOS
# =========================
st.markdown("### 📅 Médias por Ano")

df_anos = pd.DataFrame({
    "Ano": list(medias_anos.keys()),
    "Consumo médio": list(medias_anos.values())
}).sort_values("Ano")

df_anos["Consumo médio"] = df_anos["Consumo médio"].apply(fmt)

st.dataframe(df_anos, use_container_width=True)
