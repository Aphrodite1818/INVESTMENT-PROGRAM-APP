import re

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from src.Database.GOOGLE_SHEETS import get_transaction_data
    from src.Tools.data_clean import clean_transaction_data
    from src.Tools.session_auth import clear_login, persist_login, restore_login
except ModuleNotFoundError:
    from Database.GOOGLE_SHEETS import get_transaction_data
    from Tools.data_clean import clean_transaction_data
    from Tools.session_auth import clear_login, persist_login, restore_login

st.set_page_config(page_title="Admin Review", layout="wide")

GREEN = "#1b8a3a"
GREEN_LIGHT = "#a5d6a7"
GREEN_FAINT = "#e8f5e9"
RED = "#c62828"
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
    return df.dropna(subset=["NAME", "AMOUNT PAID"]).copy()


hide_sidebar()
restore_login()

if not st.session_state.get("authenticated"):
    st.switch_page("pages/login.py")

if st.session_state.get("role") != "admin":
    st.switch_page("pages/user_dashboard.py")

persist_login(st.session_state.get("username"), "admin")

st.markdown(f"<h1 style='text-align:center; color:{GREEN};'>Admin Review</h1>", unsafe_allow_html=True)

main_df = load_data()

if main_df.empty:
    st.info("No contribution data available yet.")
else:
    expected_weeks = list(range(START_WEEK, END_WEEK + 1))

    valid_week_df = main_df[(main_df["WEEK NUMBER"] >= START_WEEK) & (main_df["WEEK NUMBER"] <= END_WEEK)].copy()

    unique_members = sorted(valid_week_df["NAME"].dropna().unique().tolist())
    if not unique_members:
        unique_members = sorted(main_df["NAME"].dropna().unique().tolist())

    member_expected = len(expected_weeks)
    expected_total = len(unique_members) * member_expected if unique_members else 0

    submitted_unique = valid_week_df.drop_duplicates(subset=["NAME", "WEEK NUMBER"]).shape[0]
    missing_total = max(expected_total - submitted_unique, 0)
    completion_pct = (submitted_unique / expected_total * 100) if expected_total > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>MEMBERS TRACKED</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center; color:{GREEN};'>{len(unique_members)}</h3>", unsafe_allow_html=True)

    with k2:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>WEEKS EXPECTED</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center; color:{GREEN};'>{expected_total}</h3>", unsafe_allow_html=True)

    with k3:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>WEEKS SUBMITTED</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center; color:{GREEN};'>{submitted_unique}</h3>", unsafe_allow_html=True)

    with k4:
        with st.container(border=True):
            st.markdown("<h5 style='text-align:center;'>MISSING WEEKS</h5>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center; color:{RED};'>{missing_total}</h3>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='text-align:center; color:{GREEN}; font-size:16px;'>Completion: {completion_pct:.1f}%</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            if valid_week_df.empty:
                st.info("No valid in-range week data yet (weeks 6-40).")
            else:
                member_progress = (
                    valid_week_df.drop_duplicates(subset=["NAME", "WEEK NUMBER"])
                    .groupby("NAME", as_index=False)["WEEK NUMBER"]
                    .count()
                    .rename(columns={"WEEK NUMBER": "SUBMITTED WEEKS"})
                )
                member_progress["MISSING WEEKS"] = member_expected - member_progress["SUBMITTED WEEKS"]
                member_progress = member_progress.sort_values(["MISSING WEEKS", "NAME"], ascending=[False, True])

                fig = px.bar(
                    member_progress,
                    x="NAME",
                    y="MISSING WEEKS",
                    text="MISSING WEEKS",
                    title="Missing Weeks By Member",
                    color_discrete_sequence=[GREEN],
                )
                fig.update_layout(height=320, xaxis_title="", yaxis_title="", margin=dict(l=10, r=10, t=50, b=10))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.download_button(
                    "Download Missing Weeks By Member (CSV)",
                    data=to_csv_bytes(member_progress),
                    file_name="missing_weeks_by_member.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

    with c2:
        with st.container(border=True):
            total_by_member = (
                main_df.groupby("NAME", as_index=False)["AMOUNT PAID"].sum().sort_values("AMOUNT PAID", ascending=False)
            )
            if total_by_member.empty:
                st.info("No member totals yet.")
            else:
                fig = px.pie(
                    total_by_member.head(8),
                    names="NAME",
                    values="AMOUNT PAID",
                    hole=0.55,
                    title="Fund Share (Top Members)",
                    color_discrete_sequence=[GREEN, GREEN_LIGHT, GREEN_FAINT, "#7cb342", "#66bb6a", "#43a047", "#2e7d32", "#1b5e20"],
                )
                fig.update_traces(textposition="inside", texttemplate="%{label}<br>%{percent}")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("")

    if unique_members:
        selected_member = st.selectbox("Inspect Member", unique_members, index=0)
        member_weeks = set(
            valid_week_df[valid_week_df["NAME"] == selected_member]["WEEK NUMBER"].dropna().astype(int).tolist()
        )
        missing_weeks = [w for w in expected_weeks if w not in member_weeks]

        d1, d2 = st.columns(2)
        with d1:
            with st.container(border=True):
                st.markdown(f"<h4 style='color:{GREEN};'>Member Detail: {selected_member}</h4>", unsafe_allow_html=True)
                total_paid = float(main_df[main_df["NAME"] == selected_member]["AMOUNT PAID"].sum())
                st.markdown(f"<div>Total Paid: <b>{CURRENCY_PREFIX}{total_paid:,.2f}</b></div>", unsafe_allow_html=True)
                st.markdown(f"<div>Weeks Submitted: <b>{len(member_weeks)}</b> / {member_expected}</div>", unsafe_allow_html=True)
                st.markdown(f"<div>Weeks Missing: <b>{len(missing_weeks)}</b></div>", unsafe_allow_html=True)

        with d2:
            with st.container(border=True):
                st.markdown(f"<h4 style='color:{GREEN};'>Missing Weeks</h4>", unsafe_allow_html=True)
                if missing_weeks:
                    missing_df = pd.DataFrame({"MISSING WEEK": [f"Week {w}" for w in missing_weeks]})
                    st.dataframe(missing_df, use_container_width=True, height=210)
                    st.download_button(
                        "Download Missing Weeks (CSV)",
                        data=to_csv_bytes(missing_df),
                        file_name=f"{selected_member.lower().replace(' ', '_')}_missing_weeks.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.success("No missing weeks for this member in the contribution window.")

    with st.expander("View Full Contribution Log"):
        display_df = main_df.sort_values("DATE", ascending=False).copy()
        display_df["DATE"] = display_df["DATE"].dt.strftime("%d/%m/%Y")
        st.dataframe(display_df[["NAME", "AMOUNT PAID", "DATE", "WEEK"]], use_container_width=True)
        st.download_button(
            "Download Full Contribution Log (CSV)",
            data=to_csv_bytes(display_df[["NAME", "AMOUNT PAID", "DATE", "WEEK"]]),
            file_name="full_contribution_log.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.markdown("")
a1, a2, a3 = st.columns(3)

with a1:
    if st.button("Back to Admin Dashboard", use_container_width=True):
        st.switch_page("pages/Admin_dashboard.py")

with a2:
    if st.button("Refresh Review", use_container_width=True):
        get_transaction_data(force_refresh=True)
        st.rerun()

with a3:
    if st.button("Logout", use_container_width=True):
        clear_login()
        st.switch_page("pages/login.py")
