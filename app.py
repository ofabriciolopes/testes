import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Sistema de Gestão de Materiais")

# =========================
# 📂 SIDEBAR - HIERARQUIA
# =========================
st.sidebar.title("📁 Navegação")

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
# 📌 MATEX → MÉDIAS
# =========================
if familia == "Matex" and subcategoria == "Médias":

    arquivo = st.file_uploader("Upload do Excel", type=["xlsx"])

    if arquivo:

        df = pd.read_excel(arquivo, engine="openpyxl")

        # =========================
        # 🔧 PADRONIZAÇÃO
        # =========================
        df.columns = df.columns.str.strip().str.lower()

        def find(col, keys):
            for c in col:
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
            st.error("❌ Data e Quantidade são obrigatórias")
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
        # 🎯 FILTROS (LIMPOS)
        # =========================
        st.markdown("### 🎯 Filtros")

        col1, col2, col3, col4 = st.columns(4)

        def mult(col, label, container):
            if col and col in df.columns:
                vals = sorted(df[col].astype(str).dropna().unique())
                sel = container.multiselect(label, vals, default=vals)
                return df[col].astype(str).isin(sel)
            return pd.Series([True] * len(df))

        mask = (
            mult("material", "Material", col1) &
            mult("centro", "Centro", col2) &
            mult("deposito", "Depósito", col3) &
            mult("movimento", "Movimento", col4)
        )

        df = df[mask]

        # =========================
        # 📅 BASE
        # =========================
        hoje = datetime.today()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # último mês completo
        if mes_atual == 1:
            mes_ult = 12
            ano_ult = ano_atual - 1
        else:
            mes_ult = mes_atual - 1
            ano_ult = ano_atual

        # =========================
        # 📊 FUNÇÃO PADRÃO
        # =========================
        def consumo_diario(total, divisor_meses):
            return (total / divisor_meses) / 31 if divisor_meses > 0 else 0

        # =========================
        # 📊 ANO (todos disponíveis)
        # =========================
        anos = sorted(df["ano"].unique())
        medias_anos = {}

        for a in anos:
            total = df[df["ano"] == a]["quantidade"].sum()
            medias_anos[a] = consumo_diario(total, 12)

        # =========================
        # 📊 SEMESTRE
        # =========================
        df_sem = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=6)]
        media_sem = consumo_diario(df_sem["quantidade"].sum(), 6)

        # =========================
        # 📊 TRIMESTRE
        # =========================
        df_tri = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=3)]
        media_tri = consumo_diario(df_tri["quantidade"].sum(), 3)

        # =========================
        # 📊 ÚLTIMO MÊS COMPLETO
        # =========================
        df_ult = df[(df["ano"] == ano_ult) & (df["mes"] == mes_ult)]
        media_ult_mes = df_ult["quantidade"].sum() / 31 if len(df_ult) > 0 else 0

        # =========================
        # 📊 MÊS ATUAL
        # =========================
        df_mes = df[(df["ano"] == ano_atual) & (df["mes"] == mes_atual)]

        dias = df_mes["dia"].nunique()
        media_mes_atual = df_mes["quantidade"].sum() / dias if dias > 0 else 0

        # =========================
        # 📊 UI - RESUMO
        # =========================
        st.markdown("### 📊 Consumo Médio (padronizado)")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Ano atual", f"{medias_anos.get(ano_atual, 0):.3f}")
        col2.metric("Semestre", f"{media_sem:.3f}")
        col3.metric("Trimestre", f"{media_tri:.3f}")
        col4.metric("Último mês", f"{media_ult_mes:.3f}")
        col5.metric("Mês atual", f"{media_mes_atual:.3f}")

        # =========================
        # 📊 ANOS (TABELA)
        # =========================
        st.markdown("### 📅 Médias por Ano")

        df_anos = pd.DataFrame({
            "Ano": list(medias_anos.keys()),
            "Consumo mensal médio (÷12)": list(medias_anos.values())
        }).sort_values("Ano")

        st.dataframe(df_anos, use_container_width=True)

else:
    st.info("Selecione Matex → Médias")
