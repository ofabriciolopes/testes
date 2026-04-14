import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Sistema de Gestão de Materiais")

# =========================
# 📂 SIDEBAR - HIERARQUIA
# =========================
st.sidebar.title("📁 Navegação")

familias = [
    "Borracha",
    "Cordinha",
    "Ingrediente",
    "Matex",
    "Negro de Fumo",
    "Tecido"
]

familia = st.sidebar.selectbox("Famílias", sorted(familias))

subcategorias = {
    "Matex": ["Manuais", "Médias", "Tarefas"]
}

subcategoria = None

if familia in subcategorias:
    subcategoria = st.sidebar.selectbox(
        "Opções",
        sorted(subcategorias[familia])
    )

# =========================
# 📌 TELA ATUAL
# =========================
if subcategoria:
    st.subheader(f"📌 {familia} → {subcategoria}")
else:
    st.subheader(f"📌 {familia}")

# =========================
# 📊 MATEX → MÉDIAS
# =========================
if familia == "Matex" and subcategoria == "Médias":

    arquivo = st.file_uploader("Upload do Excel", type=["xlsx"])

    if arquivo:
        df = pd.read_excel(arquivo, engine='openpyxl')

        # =========================
        # 🔧 PADRONIZAR COLUNAS
        # =========================
        df.columns = df.columns.str.strip().str.lower()

        # =========================
        # 🔎 DETECTAR COLUNAS
        # =========================
        def detectar(colunas, palavras):
            for col in colunas:
                if any(p in col for p in palavras):
                    return col
            return None

        col_data = detectar(df.columns, ["data"])
        col_qtd = detectar(df.columns, ["quant", "qtd"])
        col_material = detectar(df.columns, ["material", "codigo"])
        col_centro = detectar(df.columns, ["centro"])
        col_deposito = detectar(df.columns, ["deposito", "dep"])
        col_mov = detectar(df.columns, ["mov", "tipo"])

        if not col_data or not col_qtd:
            st.error("❌ Necessário ter colunas de Data e Quantidade")
            st.stop()

        df = df.rename(columns={
            col_data: "data",
            col_qtd: "quantidade"
        })

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
        # 🎯 FILTROS (COM BUSCA)
        # =========================
        st.sidebar.markdown("## 🎯 Filtros")

        def filtro(coluna, nome):
            if coluna:
                valores = sorted(df[coluna].astype(str).dropna().unique())
                selecionados = st.sidebar.multiselect(
                    nome,
                    valores,
                    default=valores
                )
                return df[coluna].astype(str).isin(selecionados)
            return pd.Series([True] * len(df))

        mask = (
            filtro(col_material, "Material") &
            filtro(col_centro, "Centro") &
            filtro(col_deposito, "Depósito") &
            filtro(col_mov, "Tipo Mov.")
        )

        df = df[mask]

        # =========================
        # 📊 PERÍODOS
        # =========================
        hoje = datetime.today()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # Último mês completo
        if mes_atual == 1:
            ultimo_mes = 12
            ano_ultimo_mes = ano_atual - 1
        else:
            ultimo_mes = mes_atual - 1
            ano_ultimo_mes = ano_atual

        # Último trimestre (3 meses completos)
        df_trim = df[
            (df["data"] < datetime(ano_atual, mes_atual, 1)) &
            (df["data"] >= pd.Timestamp(datetime(ano_atual, mes_atual, 1)) - pd.DateOffset(months=3))
        ]

        # Último semestre (6 meses completos)
        df_sem = df[
            (df["data"] < datetime(ano_atual, mes_atual, 1)) &
            (df["data"] >= pd.Timestamp(datetime(ano_atual, mes_atual, 1)) - pd.DateOffset(months=6))
        ]

        # Mês corrente
        df_mes_corrente = df[
            (df["ano"] == ano_atual) &
            (df["mes"] == mes_atual)
        ]

        # Último mês completo
        df_ult_mes = df[
            (df["ano"] == ano_ultimo_mes) &
            (df["mes"] == ultimo_mes)
        ]

        # =========================
        # 📊 MÉDIAS
        # =========================
        media_mes = df_mes_corrente["quantidade"].mean()
        media_ult_mes = df_ult_mes["quantidade"].mean()
        media_trim = df_trim["quantidade"].mean()
        media_sem = df_sem["quantidade"].mean()

        media_ano = df.groupby("ano")["quantidade"].mean().mean()

        # =========================
        # 📊 FORMATADOR
        # =========================
        def fmt(valor):
            if pd.isna(valor):
                return "0"
            return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # =========================
        # 📊 INDICADORES
        # =========================
        st.markdown("### 📊 Médias")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Ano", fmt(media_ano))
        col2.metric("Semestre", fmt(media_sem))
        col3.metric("Trimestre", fmt(media_trim))
        col4.metric("Último mês", fmt(media_ult_mes))
        col5.metric("Mês atual", fmt(media_mes))

        # =========================
        # 📈 TENDÊNCIA
        # =========================
        df_group = df.groupby(["ano", "mes"])["quantidade"].mean().reset_index()

        st.markdown("### 📈 Tendência")
        st.line_chart(df_group["quantidade"])

        # =========================
        # 📋 TABELA
        # =========================
        st.markdown("### 📋 Dados")
        st.dataframe(df_group, use_container_width=True)

# =========================
# 📌 OUTROS
# =========================
else:
    st.info("🚧 Em desenvolvimento")
