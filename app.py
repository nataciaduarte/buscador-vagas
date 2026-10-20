import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Buscador de Vagas", layout="wide")


@st.cache_data(ttl=3600)  # guarda os dados por 1 hora para o site ficar rápido
def carregar_vagas():
    conn = sqlite3.connect("vagas.db")
    df = pd.read_sql("SELECT * FROM vagas ORDER BY data_publicacao DESC", conn)
    conn.close()
    df["data"] = pd.to_datetime(df["data_publicacao"], errors="coerce", utc=True).dt.date
    return df


st.title("Buscador de Vagas e Estágios")
st.caption("Vagas de estágio no Rio de Janeiro, atualizadas todos os dias. Fonte dos dados: Adzuna.")
st.caption("Projeto desenvolvido por **Natacia Duarte** · [GitHub](https://github.com/nataciaduarte) · [LinkedIn](https://www.linkedin.com/in/natácia-duarte-7a4860381)")

df = carregar_vagas()

# ---------- Filtros na barra lateral ----------
with st.sidebar:
    st.header("Filtros")
    termo = st.text_input("Palavra-chave", placeholder="ex.: python, marketing, banco")
    so_estagio = st.checkbox("Mostrar só estágios")
    locais = sorted(df["local"].dropna().unique())
    locais_escolhidos = st.multiselect("Local", locais)
    dias = st.slider("Publicadas nos últimos (dias)", min_value=1, max_value=30, value=30)

filtrado = df.copy()

if termo:
    contem = (
        filtrado["titulo"].str.contains(termo, case=False, na=False, regex=False)
        | filtrado["empresa"].str.contains(termo, case=False, na=False, regex=False)
        | filtrado["descricao"].str.contains(termo, case=False, na=False, regex=False)
    )
    filtrado = filtrado[contem]

e_estagio = filtrado["titulo"].str.contains("estágio|estagi", case=False, na=False)
if so_estagio:
    filtrado = filtrado[e_estagio]

if locais_escolhidos:
    filtrado = filtrado[filtrado["local"].isin(locais_escolhidos)]

limite = date.today() - timedelta(days=dias)
filtrado = filtrado[filtrado["data"] >= limite]

# ---------- Números do topo ----------
col1, col2, col3 = st.columns(3)
col1.metric("Vagas encontradas", len(filtrado))
col2.metric("Empresas diferentes", filtrado["empresa"].nunique())
col3.metric("Estágios", int(filtrado["titulo"].str.contains("estágio|estagi", case=False, na=False).sum()))

# ---------- Lista de vagas ----------
MAXIMO_NA_TELA = 100
if len(filtrado) > MAXIMO_NA_TELA:
    st.info(f"Mostrando as {MAXIMO_NA_TELA} mais recentes. Use os filtros para refinar.")

for _, vaga in filtrado.head(MAXIMO_NA_TELA).iterrows():
    with st.container(border=True):
        st.subheader(vaga["titulo"])
        data_txt = vaga["data"].strftime("%d/%m/%Y") if pd.notna(vaga["data"]) else "sem data"
        st.write(f"{vaga['empresa'] if pd.notna(vaga['empresa']) else 'Empresa não informada'} · {vaga['local']} · publicada em {data_txt}")
        if vaga["descricao"]:
            st.write(vaga["descricao"][:300] + "...")
        st.markdown(f"[Ver vaga completa]({vaga['link']}) · Vaga via [Adzuna](https://www.adzuna.com.br)")