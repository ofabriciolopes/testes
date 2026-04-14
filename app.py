# =========================
# 📊 MÉDIAS CORRIGIDAS (PADRÃO FIXO LOGÍSTICO)
# =========================

hoje = datetime.today()

# =========================
# 📊 SEMESTRE (6 meses fixos)
# =========================
df_sem = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=6)]
media_sem = df_sem["quantidade"].sum() / 6


# =========================
# 📊 TRIMESTRE (3 meses fixos)
# =========================
df_tri = df[df["data"] >= pd.Timestamp(hoje) - pd.DateOffset(months=3)]
media_tri = df_tri["quantidade"].sum() / 3


# =========================
# 📊 ÚLTIMO MÊS COMPLETO (FIXO 31 DIAS)
# =========================
ano_ult = hoje.year if hoje.month > 1 else hoje.year - 1
mes_ult = hoje.month - 1 if hoje.month > 1 else 12

df_ult = df[(df["ano"] == ano_ult) & (df["mes"] == mes_ult)]

media_ult = df_ult["quantidade"].sum() / 31


# =========================
# 📊 MÊS ATUAL (TAMBÉM FIXO 31 DIAS)
# =========================
df_mes = df[(df["ano"] == hoje.year) & (df["mes"] == hoje.month)]

media_mes = df_mes["quantidade"].sum() / 31


# =========================
# 📊 MÉDIA ANUAL (FIXO 12 MESES)
# =========================
anos = sorted(df["ano"].unique())
medias_anos = {}

for a in anos:
    df_a = df[df["ano"] == a]
    medias_anos[a] = df_a["quantidade"].sum() / 12
