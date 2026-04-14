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

# =========================
# 📊 BASE DE CONSUMO
# =========================
df_consumo = df[df["quantidade"] < 0].copy()
df_consumo["quantidade"] = df_consumo["quantidade"].abs()

# =========================
# 📊 KPIs (mantido simples)
# =========================
st.markdown("### 📊 Consumo Médio")

media_ult = df_consumo["quantidade"].sum() / 31
media_tri = df_consumo["quantidade"].sum() / 3 / 31
media_sem = df_consumo["quantidade"].sum() / 6 / 31
media_ano = df_consumo["quantidade"].sum() / 12 / 31

k1, k2, k3, k4 = st.columns(4)

k1.metric("Ano", fmt_br(media_ano))
k2.metric("Semestre", fmt_br(media_sem))
k3.metric("Trimestre", fmt_br(media_tri))
k4.metric("Último mês", fmt_br(media_ult))

# =========================
# 📊 ANOS FECHADOS (PERÍODO REAL)
# =========================
st.markdown("### 📊 Consumo Médio por Ano (Período Real)")

ano_atual = datetime.today().year

df_anos = df_consumo[df_consumo["data"].dt.year < ano_atual]

anos = sorted(df_anos["data"].dt.year.unique(), reverse=True)

if len(anos) == 0:
    st.info("Sem anos fechados para exibir")
    st.stop()

for ano in anos:
    df_ano = df_anos[df_anos["data"].dt.year == ano]

    inicio = df_ano["data"].min()
    fim = df_ano["data"].max()

    total = df_ano["quantidade"].sum()

    media_mensal = total / 12
    media_diaria = media_mensal / 31

    # ABS só no final (visual)
    total = abs(total)
    media_diaria = abs(media_diaria)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Ano",
        f"{ano}\n{inicio.date()} → {fim.date()}"
    )

    c2.metric("Total", fmt_br(total))

    c3.metric("Média diária (12 → 31)", fmt_br(media_diaria))
