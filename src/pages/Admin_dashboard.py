import streamlit as st
import pandas as pd
import plotly.express as px

from src.Database.GOOGLE_SHEETS import get_transaction_data
from src.Tools.data_clean import clean_transaction_data


# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.title("Admin Dashboard")
st.markdown("")

# -------------------------------------------------
# Load + clean
# -------------------------------------------------
raw_df = get_transaction_data()
df_all = clean_transaction_data(raw_df).copy()

df_all["NAME"] = df_all["NAME"].astype(str).str.strip().str.title()
df_all["AMOUNT PAID"] = pd.to_numeric(df_all["AMOUNT PAID"], errors="coerce")
df_all["DATE"] = pd.to_datetime(df_all["DATE"], errors="coerce")

df_time = df_all.dropna(subset=["DATE"]).copy()
df_time["MONTH"] = df_time["DATE"].dt.to_period("M").dt.to_timestamp()

# -------------------------------------------------
# KPIs
# -------------------------------------------------
total_fund = float(df_all["AMOUNT PAID"].sum())
total_txns = int(df_all["AMOUNT PAID"].count())
unique_members = int(df_all["NAME"].nunique())

recent_30 = 0.0
if not df_time.empty:
    latest = df_time["DATE"].max()
    cutoff = latest - pd.Timedelta(days=30)
    recent_30 = float(df_time[df_time["DATE"] >= cutoff]["AMOUNT PAID"].sum())

k1, k2, k3, k4 = st.columns([1,1,1,1])

with k1:
    with st.container(border=True):
        st.markdown("<h4 style='text-align:center;'>TOTAL FUND</h4>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center;color:green;'>₦{total_fund:,.2f}</h2>", unsafe_allow_html=True)

with k2:
    with st.container(border=True):
        st.markdown("<h4 style='text-align:center;'>TRANSACTIONS</h4>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center;color:green;'>{total_txns}</h2>", unsafe_allow_html=True)

with k3:
    with st.container(border=True):
        st.markdown("<h4 style='text-align:center;'>ACTIVE MEMBERS</h4>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center;color:green;'>{unique_members}</h2>", unsafe_allow_html=True)

with k4:
    with st.container(border=True):
        st.markdown("<h4 style='text-align:center;'>LAST 30 DAYS</h4>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center;color:green;'>₦{recent_30:,.2f}</h2>", unsafe_allow_html=True)

st.markdown("----")
st.markdown("")