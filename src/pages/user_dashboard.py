import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from src.Database.GOOGLE_SHEETS import get_transaction_data
    from src.Tools.data_clean import clean_transaction_data
    from src.Tools.session_auth import clear_login, restore_login
except ModuleNotFoundError:
    from Database.GOOGLE_SHEETS import get_transaction_data
    from Tools.data_clean import clean_transaction_data
    from Tools.session_auth import clear_login, restore_login

st.set_page_config(page_title="User Dashboard", layout="wide")

GREEN = "#1b8a3a"
GREEN_LIGHT = "#a5d6a7"
GREEN_FAINT = "#e8f5e9"
DARK = "#0b3d1a"
TARGET_FUND = 312000.0
CURRENCY_PREFIX = "N"


def hide_sidebar() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display:none;}
        [data-testid="collapsedControl"] {display:none;}
        </style>
        """,
        unsafe_allow_html=True,
    )


hide_sidebar()
restore_login()

if not st.session_state.get("authenticated"):
    st.error("Please log in to view this page.")
    st.stop()

if st.session_state.get("role") == "admin":
    st.switch_page("pages/Admin_dashboard.py")

username = str(st.session_state.get("username") or "").strip().title()
if not username:
    st.error("No user found in session. Please log in again.")
    st.stop()

st.markdown(f"<h1 style='text-align: center; color: {GREEN};'>My Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align:left; color: {GREEN};'>WELCOME: {username}</h3>", unsafe_allow_html=True)

raw_df = get_transaction_data()
df_all = clean_transaction_data(raw_df)

if st.session_state.get("submission_success_message"):
    st.success(st.session_state.pop("submission_success_message"))

required_cols = {"NAME", "AMOUNT PAID", "DATE"}
missing = required_cols - set(df_all.columns)
if missing:
    st.error(f"Missing required columns in sheet: {', '.join(sorted(missing))}")
    st.stop()

df_all["NAME"] = df_all["NAME"].astype(str).str.strip().str.title()
df_all["AMOUNT PAID"] = pd.to_numeric(df_all["AMOUNT PAID"], errors="coerce")
df_all = df_all.dropna(subset=["NAME", "AMOUNT PAID"]).copy()

df_all["DATE"] = pd.to_datetime(df_all["DATE"], errors="coerce")

user_key = username.lower()
user_df = df_all[df_all["NAME"].str.lower() == user_key].copy()

user_total = float(user_df["AMOUNT PAID"].sum()) if not user_df.empty else 0.0
fund_total = float(df_all["AMOUNT PAID"].sum()) if not df_all.empty else 0.0
equity_pct = (user_total / fund_total * 100) if fund_total > 0 else 0.0
remaining = max(TARGET_FUND - fund_total, 0.0)
progress_pct = (fund_total / TARGET_FUND * 100) if TARGET_FUND > 0 else 0.0

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>TOTAL (YOU)</h2>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center; color:{GREEN};'>{CURRENCY_PREFIX}{user_total:,.2f}</h2>", unsafe_allow_html=True)

with col2:
    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>EQUITY %</h2>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center; color:{GREEN};'>{equity_pct:.2f}%</h2>", unsafe_allow_html=True)

with col3:
    with st.container(border=True):
        st.markdown("<h2 style='text-align:center;'>TOTAL FUND</h2>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center; color:{GREEN};'>{CURRENCY_PREFIX}{fund_total:,.2f}</h2>", unsafe_allow_html=True)

st.markdown("")

user_time = user_df.dropna(subset=["DATE"]).copy()
fund_time = df_all.dropna(subset=["DATE"]).copy()

if not user_time.empty:
    user_time["MONTH"] = user_time["DATE"].dt.to_period("M").dt.to_timestamp()
else:
    user_time = pd.DataFrame(columns=["MONTH", "AMOUNT PAID"])

if not fund_time.empty:
    fund_time["MONTH"] = fund_time["DATE"].dt.to_period("M").dt.to_timestamp()
else:
    fund_time = pd.DataFrame(columns=["MONTH", "AMOUNT PAID"])

user_monthly = (
    user_time.groupby("MONTH", as_index=False)["AMOUNT PAID"].sum()
    if not user_time.empty
    else pd.DataFrame(columns=["MONTH", "AMOUNT PAID"])
)

fund_monthly = (
    fund_time.groupby("MONTH", as_index=False)["AMOUNT PAID"].sum()
    if not fund_time.empty
    else pd.DataFrame(columns=["MONTH", "AMOUNT PAID"])
)

equity_df = pd.DataFrame(
    {
        "Share": ["You", "Others"],
        "Amount": [user_total, max(fund_total - user_total, 0.0)],
    }
)

contributors = (
    df_all.groupby("NAME", as_index=False)["AMOUNT PAID"].sum().sort_values("AMOUNT PAID", ascending=False)
)


def style_axes(fig, height=260):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(x=0.5, xanchor="center"),
        xaxis_title="",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, tickprefix=CURRENCY_PREFIX, separatethousands=True)
    return fig


c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        if user_monthly.empty:
            st.info("No valid dated contributions found for you yet.")
        else:
            fig = px.line(user_monthly, x="MONTH", y="AMOUNT PAID", markers=True, title="Your Contributions Per Month")
            fig.update_traces(line_width=3, marker=dict(size=8), line=dict(color=GREEN))
            style_axes(fig, height=270)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    with st.container(border=True):
        if fund_monthly.empty:
            st.info("No valid dated contributions found in the fund yet.")
        else:
            fig = px.line(fund_monthly, x="MONTH", y="AMOUNT PAID", markers=True, title="Total Fund Inflow Per Month")
            fig.update_traces(line_width=3, marker=dict(size=8), line=dict(color=GREEN))
            style_axes(fig, height=270)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("")

c3, c4 = st.columns(2)
with c3:
    with st.container(border=True):
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=fund_total,
                number={"prefix": CURRENCY_PREFIX, "valueformat": ",.0f"},
                delta={"reference": TARGET_FUND, "valueformat": ",.0f", "position": "top"},
                title={"text": f"Target: {CURRENCY_PREFIX}{TARGET_FUND:,.0f} | Progress: {progress_pct:.1f}%", "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, TARGET_FUND], "tickformat": ",.0f"},
                    "bar": {"color": GREEN},
                    "bgcolor": "white",
                    "steps": [
                        {"range": [0, TARGET_FUND * 0.5], "color": GREEN_FAINT},
                        {"range": [TARGET_FUND * 0.5, TARGET_FUND * 0.85], "color": "#c8e6c9"},
                        {"range": [TARGET_FUND * 0.85, TARGET_FUND], "color": GREEN_LIGHT},
                    ],
                    "threshold": {"line": {"color": DARK, "width": 5}, "thickness": 0.85, "value": TARGET_FUND},
                },
            )
        )
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=65, b=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='text-align:center; color:{GREEN}; font-size:16px;'>Remaining: {CURRENCY_PREFIX}{remaining:,.0f}</div>",
            unsafe_allow_html=True,
        )

with c4:
    with st.container(border=True):
        fig = px.pie(
            equity_df,
            names="Share",
            values="Amount",
            hole=0.55,
            color="Share",
            color_discrete_map={"You": GREEN, "Others": GREEN_LIGHT},
        )
        fig.update_traces(textposition="inside", texttemplate="%{label}<br>%{percent}")
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=50, b=10),
            title=dict(text="Equity Breakdown (You vs Others)", x=0.5, xanchor="center"),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("")

with st.container(border=True):
    if contributors.empty:
        st.info("No contributors yet.")
    else:
        top_contributors = contributors.head(10).sort_values("AMOUNT PAID")
        fig = px.bar(top_contributors, x="AMOUNT PAID", y="NAME", orientation="h", text="AMOUNT PAID")
        fig.update_traces(texttemplate=f"{CURRENCY_PREFIX}%{{text:,.0f}}", textposition="outside")
        fig.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=50, b=10),
            title=dict(text="Top Contributors (Total So Far)", x=0.5, xanchor="center"),
            xaxis_title="",
            yaxis_title="",
        )
        fig.update_xaxes(tickprefix=CURRENCY_PREFIX, separatethousands=True, showgrid=True)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("View Full Leaderboard"):
        if contributors.empty:
            st.info("No leaderboard yet.")
        else:
            leaderboard = contributors.copy()
            leaderboard["RANK"] = range(1, len(leaderboard) + 1)
            leaderboard = leaderboard[["RANK", "NAME", "AMOUNT PAID"]]
            st.dataframe(leaderboard, use_container_width=True)

with st.expander("View My Transactions"):
    st.dataframe(user_df.sort_values("DATE", ascending=False), use_container_width=True)

st.markdown("")
a1, a2 = st.columns([2, 2])

with a1:
    if st.button("CLICK HERE TO SUBMIT CONTRIBUTION", use_container_width=True):
        st.switch_page("pages/submit_receipt.py")

with a2:
    if st.button("Logout", use_container_width=True):
        clear_login()
        st.switch_page("pages/login.py")

