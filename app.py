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

subcategoria = None
if familia in subcategorias:
    subcategoria = st.sidebar.selectbox("Opções", subcategorias[familia])

st.subheader(f"📌 {familia} → {subcategoria if subcategoria else ''}")

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

        def detectar(cols, palavras):
            for c in cols:
                if any(p in c for p in palavras):
                    return c
            return None

        col_data = detectar(df.columns, ["data"])
        col_qtd = detectar(df.columns, ["quant", "qtd"])
        col_material = detectar(df.columns, ["material", "codigo"])
        col_centro = detectar(df.columns, ["centro"])
        col_deposito = detectar(df.columns, ["deposito"])
        col_mov = detectar(df.columns, ["mov", "tipo"])

        if not col_data or not col_qtd:
            st.error("❌ Colunas de DATA ou QUANTIDADE não encontradas")
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
        # 🎯 FILTROS (TOPO)
        # =========================
        st.markdown("### 🎯 Filtros")

        col1, col2, col3, col4 = st.columns(4)

        def filtro(coluna, nome, container):
            if coluna and coluna in df.columns:
                valores = sorted(df[coluna].astype(str).dropna().unique())
                selecionados = container.multiselect(nome, valores, default=valores)
                return df[coluna].astype(str).isin(selecionados)
            return pd.Series([True] * len(df))

        mask = (
            filtro("material", "Material", col1) &
            filtro("centro", "Centro", col2) &
            filtro("deposito", "Depósito", col3) &
            filtro("movimento", "Tipo Mov.", col4)
        )

        df = df[mask]

        # =========================
        # 📅 PERÍODOS
        # =========================
        hoje = datetime.today()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # Último mês completo
        if mes_atual == 1:
            mes_ult = 12
            ano_ult = ano_atual - 1
        else:
            mes_ult = mes_atual - 1
            ano_ult = ano_atual

        # =========================
        # 📊 ANO COMPLETO
        # =========================
        df_ano = df[df["ano"] == ano_atual]
        media_ano = df_ano["quantidade"].sum() / 12 if len(df_ano) > 0 else 0

        # =========================
        # 📊 SEMESTRE COMPLETO (6 meses)
        # =========================
        df_semestre = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=6)]
        media_semestre = df_semestre["quantidade"].mean()

        # =========================
        # 📊 TRIMESTRE (3 meses)
        # =========================
        df_trimestre = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=3)]
        media_trimestre = df_trimestre["quantidade"].mean()

        # =========================
        # 📊 ÚLTIMO MÊS COMPLETO
        # =========================
        df_mes_anterior = df[(df["ano"] == ano_ult) & (df["mes"] == mes_ult)]
        media_mes_anterior = df_mes_anterior["quantidade"].mean()

        # =========================
        # 📊 MÊS ATUAL (REFERÊNCIA CONSUMO)
        # =========================
        df_mes_atual = df[(df["ano"] == ano_atual) & (df["mes"] == mes_atual)]

        if len(df_mes_atual) > 0:
            dias = df_mes_atual["dia"].nunique()
            media_mes_atual = df_mes_atual["quantidade"].sum() / dias if dias > 0 else 0
        else:
            media_mes_atual = 0

        # =========================
        # 📊 FORMATADOR BR
        # =========================
        def fmt(v):
            if pd.isna(v):
                return "0"
            return f"{v:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # =========================
        # 📊 KPIs
        # =========================
        st.markdown("### 📊 Médias por Período")

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("Ano", fmt(media_ano))
        c2.metric("Semestre", fmt(media_semestre))
        c3.metric("Trimestre", fmt(media_trimestre))
        c4.metric("Último mês", fmt(media_mes_anterior))
        c5.metric("Mês atual", fmt(media_mes_atual))

        # =========================
        # 📈 TENDÊNCIA
        # =========================
        df_group = df.groupby(["ano", "mes"])["quantidade"].sum().reset_index()

        st.markdown("### 📈 Tendência de Consumo")
        st.line_chart(df_group.set_index(["ano", "mes"]))

        # =========================
        # 📋 DADOS
        # =========================
        st.markdown("### 📋 Dados Filtrados")
        st.dataframe(df_group, use_container_width=True)

else:
    st.info("🚧 Selecione Matex → Médias para visualizar")
