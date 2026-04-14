import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Análise de Movimentações de Estoque")

# =========================
# 📂 MENU LATERAL (GUIAS)
# =========================
st.sidebar.title("📁 Categorias")

abas = [
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

aba_selecionada = st.sidebar.radio("Selecione a área:", abas)

st.subheader(f"📌 Área selecionada: {aba_selecionada}")

# =========================
# 📥 UPLOAD
# =========================
arquivo = st.file_uploader("Upload do Excel", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo, engine='openpyxl')

    # =========================
    # 🔧 AJUSTE DE COLUNAS
    # =========================
    df = df.rename(columns={
        'Material': 'material',
        'Quantidade': 'quantidade',
        'Data': 'data'
    })

    # =========================
    # 📅 TRATAR DATA
    # =========================
    df['data'] = pd.to_datetime(df['data'])

    # =========================
    # 🔢 VALORES POSITIVOS
    # =========================
    df['quantidade'] = df['quantidade'].abs()

    # =========================
    # 📆 COLUNAS AUXILIARES
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
    # 📊 MÉDIA ÚLTIMO MÊS COMPLETO
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
    # 📊 VISÃO GERAL
    # =========================
    st.markdown("### 📊 Indicadores")

    col1, col2 = st.columns(2)

    col1.metric("📅 Média mês corrente", f"{media_mes_corrente:,.2f}")
    col2.metric("📆 Média último mês completo", f"{media_ultimo_mes:,.2f}")

    # =========================
    # 📊 AGRUPAMENTO MENSAL
    # =========================
    df_group = df.groupby(['ano', 'mes'])['quantidade'].mean().reset_index()

    df_group = df_group.sort_values(['ano', 'mes'])

    # =========================
    # ➕ ADICIONAR COLUNAS FIXAS
    # =========================
    df_group['media_mes_corrente'] = media_mes_corrente
    df_group['media_ultimo_mes'] = media_ultimo_mes

    st.markdown("### 📋 Tabela de Médias")
    st.dataframe(df_group, use_container_width=True)
