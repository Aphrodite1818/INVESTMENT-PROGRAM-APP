import re

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from src.Database.GOOGLE_SHEETS import get_transaction_data
    from src.Tools.data_clean import clean_transaction_data
except ModuleNotFoundError:
    from Database.GOOGLE_SHEETS import get_transaction_data
    from Tools.data_clean import clean_transaction_data

st.set_page_config(page_title="Admin Dashboard", layout="wide")

GREEN = "#1b8a3a"
GREEN_LIGHT = "#a5d6a7"
GREEN_FAINT = "#e8f5e9"
CURRENCY_PREFIX = "N"
START_WEEK = 6
TOTAL_MONTHS = 10
WEEKS_PER_MONTH = 4
END_WEEK = TOTAL_MONTHS * WEEKS_PER_MONTH


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


def extract_week_number(value: str) -> float:
    match = re.search(r"(\d+)", str(value))
    return float(match.group(1)) if match else float("nan")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def load_data() -> pd.DataFrame:
    raw_df = get_transaction_data()
    df = clean_transaction_data(raw_df)
    required_cols = {"NAME", "AMOUNT PAID", "DATE", "WEEK"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Missing required columns in sheet: {', '.join(sorted(missing))}")
        st.stop()

    df["NAME"] = df["NAME"].astype(str).str.strip().str.title()
    df["AMOUNT PAID"] = pd.to_numeric(df["AMOUNT PAID"], errors="coerce")
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df["WEEK NUMBER"] = df["WEEK"].apply(extract_week_number)
    df["YEAR-MONTH"] = df["DATE"].dt.strftime("%Y-%m")
    df = df.dropna(subset=["NAME", "AMOUNT PAID"]).copy()
    return df


hide_sidebar()

if not st.session_state.get("authenticated"):
    st.error("Please log in first.")
    st.stop()

if st.session_state.get("role") != "admin":
    st.switch_page("pages/user_dashboard.py")

st.markdown(f"<h1 style='text-align:center; color:{GREEN};'>Admin Dashboard</h1>", unsafe_allow_html=True)

main_df = load_data()

if main_df.empty:
    st.info("No transaction data available yet.")
else:
    latest_date = main_df["DATE"].dropna().max()
    cutoff = latest_date - pd.Timedelta(days=30) if pd.notna(latest_date) else pd.Timestamp.min

    total_fund = float(main_df["AMOUNT PAID"].sum())
    total_txns = int(main_df["AMOUNT PAID"].count())
    unique_members = int(main_df["NAME"].nunique())
    recent_30 = float(main_df[main_df["DATE"] >= cutoff]["AMOUNT PAID"].sum()) if pd.notna(latest_date) else 0.0

    in_scope = main_df[(main_df["WEEK NUMBER"] >= START_WEEK) & (main_df["WEEK NUMBER"] <= END_WEEK)].copy()
    expected_member_weeks = unique_members * (END_WEEK - START_WEEK + 1)
    submitted_member_weeks = int(in_scope.dropna(subset=["WEEK NUMBER"]).drop_duplicates(subset=["NAME", "WEEK NUMBER"]).shape[0])
    coverage_pct = (submitted_member_weeks / expected_member_weeks * 100) if expected_member_weeks > 0 else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>TOTAL FUND</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;color:{GREEN};'>{CURRENCY_PREFIX}{total_fund:,.2f}</h3>", unsafe_allow_html=True)

    with k2:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>TRANSACTIONS</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;color:{GREEN};'>{total_txns}</h3>", unsafe_allow_html=True)

    with k3:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>ACTIVE MEMBERS</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;color:{GREEN};'>{unique_members}</h3>", unsafe_allow_html=True)

    with k4:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>LAST 30 DAYS</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;color:{GREEN};'>{CURRENCY_PREFIX}{recent_30:,.2f}</h3>", unsafe_allow_html=True)

    with k5:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>WEEK COVERAGE</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;color:{GREEN};'>{coverage_pct:.1f}%</h3>", unsafe_allow_html=True)

    st.markdown("")

    f1, f2, f3 = st.columns([2, 1, 1])
    member_options = ["All"] + sorted(main_df["NAME"].dropna().unique().tolist())
    selected_member = f1.selectbox("Filter by Member", member_options, index=0)

    month_options = ["All"]
    dated = main_df.dropna(subset=["DATE"]).copy()
    if not dated.empty:
        month_options.extend(sorted(dated["YEAR-MONTH"].unique().tolist()))
    selected_month = f2.selectbox("Filter by Month", month_options, index=0)

    week_values = sorted(
        set(main_df["WEEK NUMBER"].dropna().astype(int).tolist()) | set(range(START_WEEK, END_WEEK + 1))
    )
    week_options = ["All"] + [f"Week {w}" for w in week_values]
    selected_week = f3.selectbox("Filter by Week", week_options, index=0)

    filtered = main_df.copy()
    if selected_member != "All":
        filtered = filtered[filtered["NAME"] == selected_member]
    if selected_month != "All":
        filtered = filtered[filtered["YEAR-MONTH"] == selected_month]
    if selected_week != "All":
        week_num = int(selected_week.split()[1])
        filtered = filtered[filtered["WEEK NUMBER"] == week_num]

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            member_totals = (
                filtered.groupby("NAME", as_index=False)["AMOUNT PAID"]
                .sum()
                .sort_values("AMOUNT PAID", ascending=False)
                .head(10)
            )
            if member_totals.empty:
                st.info("No contributor data for selected filters.")
            else:
                fig = px.bar(
                    member_totals.sort_values("AMOUNT PAID"),
                    x="AMOUNT PAID",
                    y="NAME",
                    orientation="h",
                    text="AMOUNT PAID",
                    title="Top Contributors",
                    color_discrete_sequence=[GREEN],
                )
                fig.update_traces(texttemplate=f"{CURRENCY_PREFIX}%{{text:,.0f}}", textposition="outside")
                fig.update_layout(height=340, xaxis_title="", yaxis_title="", margin=dict(l=10, r=10, t=50, b=10))
                fig.update_xaxes(tickprefix=CURRENCY_PREFIX, separatethousands=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        with st.container(border=True):
            monthly = filtered.dropna(subset=["DATE"]).copy()
            if monthly.empty:
                st.info("No valid dates for selected filters.")
            else:
                monthly["MONTH"] = monthly["DATE"].dt.to_period("M").dt.to_timestamp()
                monthly = monthly.groupby("MONTH", as_index=False)["AMOUNT PAID"].sum()
                fig = px.line(
                    monthly,
                    x="MONTH",
                    y="AMOUNT PAID",
                    markers=True,
                    title="Monthly Inflow",
                    color_discrete_sequence=[GREEN],
                )
                fig.update_traces(line_width=3, marker=dict(size=7))
                fig.update_layout(height=340, xaxis_title="", yaxis_title="", margin=dict(l=10, r=10, t=50, b=10))
                fig.update_yaxes(tickprefix=CURRENCY_PREFIX, separatethousands=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.container(border=True):
        recent = filtered.sort_values("DATE", ascending=False).head(20).copy()
        if recent.empty:
            st.info("No submissions found for selected filters.")
        else:
            recent_display = recent[["NAME", "AMOUNT PAID", "DATE", "WEEK"]].copy()
            recent_display["DATE"] = recent_display["DATE"].dt.strftime("%d/%m/%Y")
            st.markdown(f"<h4 style='color:{GREEN};'>Recent Submissions</h4>", unsafe_allow_html=True)
            st.dataframe(recent_display, use_container_width=True)
            st.download_button(
                "Download Recent Submissions (CSV)",
                data=to_csv_bytes(recent_display),
                file_name="recent_submissions.csv",
                mime="text/csv",
                use_container_width=True,
            )

st.markdown("")
a1, a2, a3 = st.columns(3)

with a1:
    if st.button("Open Admin Review", use_container_width=True):
        st.switch_page("pages/Admin_review.py")

with a2:
    if st.button("Refresh Dashboard", use_container_width=True):
        get_transaction_data(force_refresh=True)
        st.rerun()

with a3:
    if st.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["role"] = "user"
        st.switch_page("pages/login.py")
