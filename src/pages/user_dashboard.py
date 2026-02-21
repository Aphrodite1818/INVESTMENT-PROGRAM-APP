import streamlit as st
import pandas as pd
import plotly.express as px

from src.Database.GOOGLE_SHEETS import get_transaction_data
from src.Tools.data_clean import clean_transaction_data


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="User Dashboard", layout="wide")
st.markdown("<h1 style='text-align: center; color: green;'>My Dashboard</h1>", unsafe_allow_html=True)


# -----------------------------
# Guard (uncomment when auth is ready)
# -----------------------------
# if not st.session_state.get("authenticated"):
#     st.error("Please log in to view this page.")
#     st.stop()


# -----------------------------
# Demo user (REMOVE in production)
# -----------------------------
if "username" not in st.session_state:
    st.session_state["username"] = "Naomi"

username = st.session_state.get("username")
st.write(f"WELCOME: {username}")


# -----------------------------
# Load + clean data
# -----------------------------
raw_df = get_transaction_data()
df_all = clean_transaction_data(raw_df).copy()

# Basic validation
required_cols = {"NAME", "AMOUNT PAID", "DATE"}
missing = required_cols - set(df_all.columns)
if missing:
    st.error(f"Missing required columns in sheet: {', '.join(sorted(missing))}")
    st.stop()

# Ensure types are sane (cleaner should do this, but we keep it safe)
df_all["NAME"] = df_all["NAME"].astype(str).str.strip().str.title()
df_all["AMOUNT PAID"] = pd.to_numeric(df_all["AMOUNT PAID"], errors="coerce")
df_all["DATE"] = pd.to_datetime(df_all["DATE"], errors="coerce")

# Keep a full copy for fund-wide calculations
main_df = df_all.copy()

# Filter to current user
user_key = str(username).strip().lower()
user_df = df_all[df_all["NAME"].astype(str).str.strip().str.lower() == user_key].copy()


# -----------------------------
# KPI values
# -----------------------------
user_total = float(user_df["AMOUNT PAID"].sum()) if not user_df.empty else 0.0
fund_total = float(main_df["AMOUNT PAID"].sum()) if not main_df.empty else 0.0
equity_pct = (user_total / fund_total * 100) if fund_total > 0 else 0.0


# -----------------------------
# KPIs (cards)
# -----------------------------
col1, col2, col3 = st.columns([3, 3, 3])

with col1:
    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>TOTAL (YOU)</h2>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align:center; color: green;'>₦{:,.2f}</h2>".format(user_total),
            unsafe_allow_html=True
        )

with col2:
    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>EQUITY %</h2>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align:center; color: green;'>{:.2f}%</h2>".format(equity_pct),
            unsafe_allow_html=True
        )

with col3:
    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>TOTAL FUND</h2>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align:center; color: green;'>₦{:,.2f}</h2>".format(fund_total),
            unsafe_allow_html=True
        )


# -----------------------------
# Prep time-series for charts
# -----------------------------
# Drop bad dates for time charts
user_time = user_df.dropna(subset=["DATE"]).copy()
fund_time = main_df.dropna(subset=["DATE"]).copy()

# Month bucket as real timestamps (keeps correct order)
user_time["MONTH"] = user_time["DATE"].dt.to_period("M").dt.to_timestamp()
fund_time["MONTH"] = fund_time["DATE"].dt.to_period("M").dt.to_timestamp()

user_monthly = user_time.groupby("MONTH", as_index=False)["AMOUNT PAID"].sum()
fund_monthly = fund_time.groupby("MONTH", as_index=False)["AMOUNT PAID"].sum()

# Equity breakdown
others_total = max(fund_total - user_total, 0.0)
equity_df = pd.DataFrame({"Share": ["You", "Others"], "Amount": [user_total, others_total]})

# Top contributors
top = (
    main_df.groupby("NAME", as_index=False)["AMOUNT PAID"].sum()
    .sort_values("AMOUNT PAID", ascending=False)
    .head(8)
)


def compact(fig, height=260):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=None, showgrid=True, tickprefix="₦", separatethousands=True)
    return fig


st.markdown("")


# -----------------------------
# Charts (compact cards)
# -----------------------------
c1, c2 = st.columns([3, 3])

with c1:
    with st.container(border=True):
        if user_monthly.empty:
            st.info("No valid dated transactions for you yet.")
        else:
            fig = px.line(
                user_monthly, x="MONTH", y="AMOUNT PAID",
                markers=True, title="Your Contributions Per Month"
            )
            fig.update_traces(line_width=3)
            compact(fig)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    with st.container(border=True):
        if fund_monthly.empty:
            st.info("No valid dated transactions in the fund yet.")
        else:
            fig = px.line(
                fund_monthly, x="MONTH", y="AMOUNT PAID",
                markers=True, title="Total Fund Inflow Per Month"
            )
            fig.update_traces(line_width=3)
            compact(fig)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


c3, c4 = st.columns([3, 3])

with c3:
    with st.container(border=True):
        fig = px.pie(equity_df, names="Share", values="Amount", title="Equity Breakdown (You vs Others)")
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c4:
    with st.container(border=True):
        if top.empty:
            st.info("No contributors yet.")
        else:
            fig = px.bar(top, x="NAME", y="AMOUNT PAID", title="Top Contributors", text="AMOUNT PAID")
            fig.update_traces(texttemplate="₦%{text:,.0f}", textposition="outside")
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10))
            fig.update_yaxes(title=None, tickprefix="₦", separatethousands=True)
            fig.update_xaxes(title=None)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# -----------------------------
# Optional: show user transactions table
# -----------------------------
with st.expander("View My Transactions"):
    st.dataframe(
        user_df.sort_values("DATE", ascending=False),
        use_container_width=True
    )



with st.sidebar:
    st.markdown("<h1 style='color: green;'>Logout</h1>", unsafe_allow_html=True)
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.switch_page("pages/login.py")



if st.button("CLICK HERE TO SUBMIT RECEIPT"):
    st.switch_page("pages/submit_receipt.py")