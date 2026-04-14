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
# 📌 FORMATAÇÃO ERP
# =========================
def fmt_br(valor):
    if pd.isna(valor):
        return "0,000"
    return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
# 📊 BASE
# =========================
hoje = datetime.today()

df_consumo = df[df["quantidade"] < 0].copy()
df_consumo["quantidade"] = df_consumo["quantidade"].abs()

# =========================
# 📊 KPIs
# =========================
st.markdown("### 📊 Consumo Médio")

df_ano_base = df_consumo.copy()

media_ult = df_ano_base["quantidade"].sum() / 31
media_tri = df_ano_base["quantidade"].sum() / 3 / 31
media_sem = df_ano_base["quantidade"].sum() / 6 / 31
media_ano = df_ano_base["quantidade"].sum() / 12 / 31

k1, k2, k3, k4 = st.columns(4)

k1.metric("Ano", fmt_br(media_ano))
k2.metric("Semestre", fmt_br(media_sem))
k3.metric("Trimestre", fmt_br(media_tri))
k4.metric("Último mês", fmt_br(media_ult))

# =========================
# 📊 ANOS FECHADOS (REGRA FINAL)
# =========================
st.markdown("### 📊 Consumo Médio por Ano (Regra Final)")

ano_atual = datetime.today().year

df_anos = df.copy()
df_anos = df_anos[df_anos["ano"] < ano_atual]

df_anos = df_anos.groupby("ano")["quantidade"].sum().reset_index()
df_anos = df_anos.sort_values("ano", ascending=False)

if df_anos.empty:
    st.info("Sem anos fechados para exibir")
    st.stop()

for _, row in df_anos.iterrows():
    ano = int(row["ano"])
    total = row["quantidade"]

    media_mensal = total / 12
    media_diaria = media_mensal / 31

    # ABS somente no final (visual)
    total = abs(total)
    media_diaria = abs(media_diaria)

    c1, c2, c3 = st.columns(3)

    c1.metric("Ano", ano)
    c2.metric("Total", fmt_br(total))
    c3.metric("Média diária (12 → 31)", fmt_br(media_diaria))
