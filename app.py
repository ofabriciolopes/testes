# =========================
# 🎯 FILTROS (NO TOPO)
# =========================
st.markdown("### 🎯 Filtros")

col1, col2, col3, col4 = st.columns(4)

def filtro(coluna, nome, container):
    if coluna:
        valores = sorted(df[coluna].astype(str).dropna().unique())
        selecionados = container.multiselect(
            nome,
            valores,
            default=valores
        )
        return df[coluna].astype(str).isin(selecionados)
    return pd.Series([True] * len(df))

mask = (
    filtro(col_material, "Material", col1) &
    filtro(col_centro, "Centro", col2) &
    filtro(col_deposito, "Depósito", col3) &
    filtro(col_mov, "Tipo Mov.", col4)
)

df = df[mask]
