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
# 📂 SUBCATEGORIA
# =========================
subcategorias = {
    "Matex": ["Médias", "Consumo", "Estoque"],
}

subcategoria = st.sidebar.selectbox(
    "Subcategoria",
    subcategorias.get(categoria, ["Em breve"])
)

st.subheader(f"📌 {categoria} → {subcategoria}")

# =========================
# 📌 MATEX → MÉDIAS
# =========================
if categoria == "Matex" and subcategoria == "Médias":

    arquivo = st.file_uploader("Upload do Excel", type=["xlsx"])

    if arquivo:
        try:
            df = pd.read_excel(arquivo, engine='openpyxl')
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            st.stop()

        # =========================
        # 🔧 PADRONIZAR COLUNAS
        # =========================
        df.columns = df.columns.str.strip().str.lower()

        st.write("🔍 Colunas encontradas:", df.columns)

        # =========================
        # 🔎 DETECTAR COLUNAS
        # =========================
        coluna_data = None
        coluna_qtd = None
        coluna_material = None

        for col in df.columns:
            if 'data' in col:
                coluna_data = col
            if any(p in col for p in ['quant', 'qtd', 'volume']):
                coluna_qtd = col
            if any(p in col for p in ['material', 'codigo', 'produto']):
                coluna_material = col

        if coluna_data is None or coluna_qtd is None:
            st.error("❌ Não encontrei colunas de DATA ou QUANTIDADE")
            st.stop()

        # =========================
        # 🔁 RENOMEAR
        # =========================
        df = df.rename(columns={
            coluna_data: 'data',
            coluna_qtd: 'quantidade'
        })

        if coluna_material:
            df = df.rename(columns={coluna_material: 'material'})

        # =========================
        # 📅 TRATAR DADOS
        # =========================
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df = df.dropna(subset=['data'])

        df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce')
        df = df.dropna(subset=['quantidade'])

        # 🔢 VALORES POSITIVOS
        df['quantidade'] = df['quantidade'].abs()

        # =========================
        # 📆 COLUNAS AUXILIARES
        # =========================
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month

        # =========================
        # 🎯 FILTROS
        # =========================
        st.sidebar.markdown("## 🎯 Filtros")

        # 📦 MATERIAL (SEGURANÇA TOTAL)
        if 'material' in df.columns:

            col_material = df['material']

            # Se vier duplicado ou dataframe
            if isinstance(col_material, pd.DataFrame):
                col_material = col_material.iloc[:, 0]

            col_material = col_material.astype(str)

            materiais = sorted(col_material.dropna().unique())

            material_sel = st.sidebar.multiselect(
                "Material",
                materiais,
                default=materiais
            )

            df = df[col_material.isin(material_sel)]

        # 📅 ANO
        anos = sorted(df['ano'].dropna().unique())
        ano_sel = st.sidebar.multiselect("Ano", anos, default=anos)
        df = df[df['ano'].isin(ano_sel)]

        # 📆 MÊS
        meses = sorted(df['mes'].dropna().unique())
        mes_sel = st.sidebar.multiselect("Mês", meses, default=meses)
        df = df[df['mes'].isin(mes_sel)]

        # =========================
        # 📊 CÁLCULOS
        # =========================
        hoje = datetime.today()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # MÊS CORRENTE
        df_mes_corrente = df[
            (df['ano'] == ano_atual) &
            (df['mes'] == mes_atual)
        ]

        media_mes_corrente = df_mes_corrente['quantidade'].mean()

        # ÚLTIMO MÊS COMPLETO
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
        # 📊 INDICADORES
        # =========================
        col1, col2 = st.columns(2)

        col1.metric(
            "📅 Média mês corrente",
            f"{media_mes_corrente:,.2f}" if pd.notna(media_mes_corrente) else "0"
        )

        col2.metric(
            "📆 Último mês completo",
            f"{media_ultimo_mes:,.2f}" if pd.notna(media_ultimo_mes) else "0"
        )

        # =========================
        # 📋 TABELA
        # =========================
        df_group = df.groupby(['ano', 'mes'])['quantidade'].mean().reset_index()

        st.markdown("### 📋 Média por Mês")
        st.dataframe(df_group, use_container_width=True)

# =========================
# 📌 OUTRAS TELAS
# =========================
elif categoria == "Matex":
    st.info("🚧 Subcategoria ainda não desenvolvida.")

else:
    st.info("🚧 Categoria ainda não implementada.")
