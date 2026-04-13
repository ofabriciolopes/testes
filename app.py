import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Análise de Movimentações de Estoque")

arquivo = st.file_uploader("Upload do Excel", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)

    # =========================
    # RENOMEAR COLUNAS
    # =========================
    df = df.rename(columns={
        'Material': 'material',
        'Tipo de movimento': 'tipo_mov',
        'Data de lançamento': 'data',
        'Depósito': 'deposito',
        'Centro': 'planta',
        'Qtd.  UM registro': 'quantidade'
    })

    # =========================
    # TRATAMENTO
    # =========================
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce')

    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month

    # =========================
    # FILTROS
    # =========================
    st.sidebar.header("Filtros")

    material = st.sidebar.text_input("Material")

    deposito = st.sidebar.multiselect("Depósito", sorted(df['deposito'].dropna().unique()))
    planta = st.sidebar.multiselect("Planta", sorted(df['planta'].dropna().unique()))
    tipo_mov = st.sidebar.multiselect("Tipo Mov.", sorted(df['tipo_mov'].dropna().unique()))

    df_filtrado = df.copy()

    if material:
        df_filtrado = df_filtrado[df_filtrado['material'].astype(str).str.contains(material, case=False)]

    if deposito:
        df_filtrado = df_filtrado[df_filtrado['deposito'].isin(deposito)]

    if planta:
        df_filtrado = df_filtrado[df_filtrado['planta'].isin(planta)]

    if tipo_mov:
        df_filtrado = df_filtrado[df_filtrado['tipo_mov'].isin(tipo_mov)]

    # =========================
    # BASE MENSAL
    # =========================
    mensal = df_filtrado.groupby(['material', 'ano', 'mes']).agg(
        total=('quantidade', 'sum'),
        dias=('data', lambda x: x.dt.daysinmonth.iloc[0])
    ).reset_index()

    mensal['media_dia'] = mensal['total'] / mensal['dias']

    # remover mês atual
    hoje = pd.Timestamp.today()
    ultimo_mes = hoje.replace(day=1) - pd.Timedelta(days=1)

    mensal = mensal[
        (mensal['ano'] < ultimo_mes.year) |
        ((mensal['ano'] == ultimo_mes.year) & (mensal['mes'] <= ultimo_mes.month))
    ]

    mensal = mensal.sort_values(['material', 'ano', 'mes'])

    mensal['data_ref'] = pd.to_datetime(
        mensal['ano'].astype(str) + '-' + mensal['mes'].astype(str) + '-01'
    )

    # =========================
    # MÉDIAS
    # =========================

    # anual
    anual = mensal.groupby(['material', 'ano'])['media_dia'].mean().reset_index()
    anual_final = anual.sort_values('ano').groupby('material').tail(1)

    # rolling
    mensal['media_3m'] = mensal.groupby('material')['media_dia'].transform(lambda x: x.rolling(3).mean())
    mensal['media_6m'] = mensal.groupby('material')['media_dia'].transform(lambda x: x.rolling(6).mean())
    mensal['media_12m'] = mensal.groupby('material')['media_dia'].transform(lambda x: x.rolling(12).mean())

    trimestral = mensal.dropna(subset=['media_3m']).groupby('material').tail(1)[['material', 'media_3m']]
    semestral = mensal.dropna(subset=['media_6m']).groupby('material').tail(1)[['material', 'media_6m']]
    mensal_final = mensal.dropna(subset=['media_12m']).groupby('material').tail(1)[['material', 'media_12m']]

    # =========================
    # TABELA FINAL
    # =========================
    df_final = anual_final[['material', 'media_dia']].rename(columns={'media_dia': 'Anual'})

    df_final = df_final.merge(trimestral, on='material', how='left')
    df_final = df_final.merge(semestral, on='material', how='left')
    df_final = df_final.merge(mensal_final, on='material', how='left')

    df_final = df_final.rename(columns={
        'media_3m': '3M',
        'media_6m': '6M',
        'media_12m': '12M'
    })

    # =========================
    # FORMATAÇÃO
    # =========================
    def formatar(valor):
        try:
            return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return ""

    for col in ['Anual', '3M', '6M', '12M']:
        df_final[col] = df_final[col].apply(formatar)

    # =========================
    # KPIs
    # =========================
    st.subheader("📌 Resumo")

    col1, col2, col3 = st.columns(3)

    col1.metric("Materiais", df_final['material'].nunique())

    col2.metric("Média 12M",
        round(pd.to_numeric(df_final['12M'].str.replace('.', '').str.replace(',', '.'), errors='coerce').mean(), 2)
    )

    col3.metric("Média 3M",
        round(pd.to_numeric(df_final['3M'].str.replace('.', '').str.replace(',', '.'), errors='coerce').mean(), 2)
    )

    # =========================
    # TABELA
    # =========================
    st.subheader("📊 Consumo por Material")

    df_final = df_final.sort_values(by='12M', ascending=False)

    st.dataframe(df_final, use_container_width=True)

    # =========================
    # GRÁFICO
    # =========================
    st.subheader("📈 Tendência de Consumo")

    material_select = st.selectbox("Selecione o material", df_final['material'].unique())

    grafico = mensal[mensal['material'] == material_select]

    st.line_chart(grafico.set_index('data_ref')['media_dia'])

    # =========================
    # EXPORTAR
    # =========================
    st.download_button(
        "📥 Baixar dados filtrados",
        df_filtrado.to_csv(index=False).encode('utf-8'),
        "dados_filtrados.csv",
        "text/csv"
    )

else:
    st.info("Faça upload do seu arquivo XLSX")