# =====================================================
# DASHBOARD -- BOT TELEGRAM + GROQ
# Taller Ciencia de Datos -- EAFIT 2026
# =====================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import os, asyncio, libsql_client
from dotenv import load_dotenv

load_dotenv()
TURSO_URL   = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

st.set_page_config(page_title="Dashboard Bot IA", layout="wide")
st.title("Dashboard — Asistente de Ciencia de Datos")
st.caption("Análisis de conversaciones del bot de Telegram")

@st.cache_data(ttl=30)
def cargar_datos():
    async def _fetch():
        async with libsql_client.create_client(
            url=TURSO_URL, auth_token=TURSO_TOKEN) as db:
            r = await db.execute(
                "SELECT * FROM mensajes ORDER BY fecha DESC LIMIT 1000")
            return r.rows, r.columns
    rows, cols = asyncio.run(_fetch())
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=cols)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["hora"]  = df["fecha"].dt.hour
    df["dia"]   = df["fecha"].dt.date
    return df

df = cargar_datos()
if df.empty:
    st.warning("Aún no hay conversaciones.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total mensajes",   len(df))
c2.metric("Usuarios únicos",  df["user_id"].nunique())
c3.metric("Tokens usados",    int(df["tokens"].sum()))
c4.metric("Días activos",     df["dia"].nunique())

st.divider()
ca, cb = st.columns(2)
with ca:
    st.subheader("Mensajes por día")
    d = df.groupby("dia").size().reset_index(name="n")
    st.plotly_chart(px.bar(d, x="dia", y="n",
        color_discrete_sequence=["#1A3A5C"]), use_container_width=True)
with cb:
    st.subheader("Mensajes por hora")
    h = df.groupby("hora").size().reset_index(name="n")
    st.plotly_chart(px.line(h, x="hora", y="n", markers=True,
        color_discrete_sequence=["#E8A020"]), use_container_width=True)

st.subheader("Usuarios más activos")
top = (df.groupby("usuario").size()
       .reset_index(name="n")
       .sort_values("n", ascending=True).tail(10))
st.plotly_chart(px.bar(top, x="n", y="usuario", orientation="h",
    color_discrete_sequence=["#1A3A5C"]), use_container_width=True)

st.subheader("Últimas conversaciones")
st.dataframe(df[["fecha","usuario","pregunta","respuesta","tokens"]].head(20),
             use_container_width=True, hide_index=True)

if st.button("🔄 Actualizar"):
    st.cache_data.clear()
    st.rerun()
