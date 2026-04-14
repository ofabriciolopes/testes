import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Sistema de Análise de Estoque")

# =========================
# 📂 CATEGORIA
# =========================
st.sidebar.title("📁 Navegação")

categoria = st.sidebar.selectbox(
    "Categoria",
    [
        "Matex",
        "Ingrediente",
        "Negro de Fumo",
        "Borracha",
        "Tecido",
        "Cordinha",
        "Importação",
        "Exportação",
        "Feira de Santana",
        "Barueri"
    ]
)

# =========================
# 📂 SUBCATEGORIA DINÂMICA
# =========================
subcategorias = {
    "Matex": ["Médias", "Consumo", "Estoque"],
    "Ingrediente": ["Em breve"],
    "Negro de Fumo": ["Em breve"],
    "Borracha": ["Em breve"],
    "Tecido": ["Em breve"],
    "Cordinha": ["Em breve"],
    "Importação": ["Em breve"],
    "Exportação": ["Em breve"],
    "Feira de Santana": ["Em breve"],
    "Barueri": ["Em breve"]
}

subcategoria = st.sidebar.selectbox(
    "Subcategoria",
    subcategorias[categoria]
)

st.subheader(f"📌 {categoria} → {subcategoria}")

# =========================
# 📌 REGRA: SÓ EXECUTA SE FOR MATEX + MÉDIAS
# =========================
if categoria == "Matex" and subcategoria == "Médias":

    arquivo = st.file_uploader("Upload do Excel", type=["xlsx"])

    if arquivo:
        df = pd.read_excel(arquivo, engine='openpyxl')

        # =========================
        # 🔧 PADRONIZAR COLUNAS
        # =========================
        df.columns = df.columns.str.strip().str.lower()

        # Detectar colunas
        coluna_data = None
        coluna_qtd = None

        for col in df.columns:
            if 'data' in col:
                coluna_data = col
            if 'quant' in col or 'qtd' in col:
                coluna_qtd = col

        if coluna_data is None or coluna_qtd is None:
            st.error("❌ Não encontrei colunas de data ou quantidade")
            st.stop()

        df = df.rename(columns={
            coluna_data: 'data',
            coluna_qtd: 'quantidade'
        })

        # =========================
        # 📅 TRATAR DADOS
        # =========================
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df = df.dropna(subset=['data'])

        df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce')
        df = df.dropna(subset=['quantidade'])

        # 🔢 POSITIVO
        df['quantidade'] = df['quantidade'].abs()

        # =========================
        # 📆 COLUNAS
        # =========================
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month

        hoje = datetime.today()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # =========================
        # 📊 MÉDIA MÊS CORRENTE
        # =========================
        df_mes_corrente = df[
            (df['ano'] == ano_atual) &
            (df['mes'] == mes_atual)
        ]

        media_mes_corrente = df_mes_corrente['quantidade'].mean()

        # =========================
        # 📊 ÚLTIMO MÊS COMPLETO
        # =========================
        if mes_atual == 1:
            ultimo_mes = 12
            ano_ultimo_mes = ano_atual - 1
        else:
            ultimo_mes = mes_atual - 1
            ano_ultimo_mes = ano_atual

        df_ultimo_mes = df[
            (df['ano'] == ano_ultimo_mes) &
            (df['mes'] == ultimo_mes)
        ]

        media_ultimo_mes = df_ultimo_mes['quantidade'].mean()

        # =========================
        # 📊 UI
        # =========================
        col1, col2 = st.columns(2)

        col1.metric("Média mês corrente", f"{media_mes_corrente:,.2f}")
        col2.metric("Último mês completo", f"{media_ultimo_mes:,.2f}")

        # =========================
        # 📋 TABELA
        # =========================
        df_group = df.groupby(['ano', 'mes'])['quantidade'].mean().reset_index()

        st.dataframe(df_group, use_container_width=True)

# =========================
# 📌 OUTRAS TELAS (FUTURO)
# =========================
elif categoria == "Matex":
    st.info("🚧 Essa subcategoria ainda será desenvolvida.")

else:
    st.info("🚧 Categoria ainda não implementada.")
