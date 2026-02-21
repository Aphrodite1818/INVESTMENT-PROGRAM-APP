import pandas as pd
import streamlit as st
from datetime import date, datetime, timedelta

try:
    from src.Database.GOOGLE_SHEETS import append_transaction, get_transaction_data
    from src.Tools.data_clean import clean_transaction_data
    from src.Tools.session_auth import clear_login, persist_login, restore_login
except ModuleNotFoundError:
    from Database.GOOGLE_SHEETS import append_transaction, get_transaction_data
    from Tools.data_clean import clean_transaction_data
    from Tools.session_auth import clear_login, persist_login, restore_login

GREEN = "#1b8a3a"
GREEN_LIGHT = "#a5d6a7"
MIN_AMOUNT = 1000.0
START_WEEK = 6
TOTAL_MONTHS = 10
WEEKS_PER_MONTH = 4
END_WEEK = TOTAL_MONTHS * WEEKS_PER_MONTH
WEEK6_START_DATE = date(2026, 2, 9)  # Monday


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


def current_open_week(today: date) -> int:
    if today <= WEEK6_START_DATE:
        return START_WEEK
    weeks_elapsed = (today - WEEK6_START_DATE).days // 7
    return min(START_WEEK + weeks_elapsed, END_WEEK)


def next_monday(today: date) -> date:
    days_ahead = (7 - today.weekday()) % 7
    days_ahead = 7 if days_ahead == 0 else days_ahead
    return today + timedelta(days=days_ahead)


def next_due_week(paid_weeks: set[int]) -> int:
    week = START_WEEK
    while week in paid_weeks and week <= END_WEEK:
        week += 1
    return week


hide_sidebar()
restore_login()
st.markdown(f"<h1 style='text-align:center; color:{GREEN};'>Submit Contribution</h1>", unsafe_allow_html=True)

if not st.session_state.get("authenticated"):
    st.switch_page("pages/login.py")

if st.session_state.get("role") == "admin":
    st.switch_page("pages/Admin_dashboard.py")

username = st.session_state.get("username")
if not username:
    clear_login()
    st.switch_page("pages/login.py")

normalized_user = str(username).strip().title()
persist_login(normalized_user, "user")
st.markdown(f"<h3 style='color:{GREEN};'>User: {normalized_user}</h3>", unsafe_allow_html=True)

existing_df = clean_transaction_data(get_transaction_data())
if not existing_df.empty:
    existing_df["NAME"] = existing_df["NAME"].astype(str).str.strip().str.title()
    user_existing = existing_df[existing_df["NAME"] == normalized_user].copy()
    user_existing["WEEK NUMBER"] = pd.to_numeric(
        user_existing["WEEK"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )
    paid_weeks = set(user_existing["WEEK NUMBER"].dropna().astype(int).tolist())
else:
    paid_weeks = set()

today = date.today()
open_week = current_open_week(today)
due_week = next_due_week(paid_weeks)
can_submit = due_week <= open_week and due_week <= END_WEEK

l, c, r = st.columns([1, 2, 1])
with c:
    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:center; color:{GREEN_LIGHT};'>Pay in order. If you missed a week, pay that week first.</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='text-align:center; color:{GREEN};'>Current Open Week: <b>Week {open_week}</b></div>",
            unsafe_allow_html=True,
        )

        amount = st.number_input("Amount Paid (N)", min_value=MIN_AMOUNT, step=100.0, format="%.2f")

        if due_week > END_WEEK:
            st.success("You have completed all scheduled contributions.")
            submitted = False
        elif can_submit:
            st.info(f"Next required week: Week {due_week}")
            submitted = st.button(f"Pay Week {due_week}", use_container_width=True)
        else:
            next_open = next_monday(today)
            st.warning(
                f"You have already paid through Week {open_week}. "
                f"Next payment (Week {due_week}) opens on {next_open.strftime('%d/%m/%Y')}"
            )
            submitted = False

    if submitted:
        if amount < MIN_AMOUNT:
            st.error(f"Amount must not be less than N{MIN_AMOUNT:,.0f}.")
            st.stop()

        date_str = datetime.now().strftime("%d/%m/%Y")
        week = f"week {due_week}"

        try:
            fresh_df = clean_transaction_data(get_transaction_data(force_refresh=True))
            if not fresh_df.empty:
                fresh_df["NAME"] = fresh_df["NAME"].astype(str).str.strip().str.title()
                fresh_df["WEEK"] = fresh_df["WEEK"].astype(str).str.strip().str.lower()
                is_duplicate = ((fresh_df["NAME"] == normalized_user) & (fresh_df["WEEK"] == week)).any()
                if is_duplicate:
                    st.error(f"You already paid for {week.title()}.")
                    st.stop()

            append_transaction(
                name=normalized_user,
                amount_paid=float(amount),
                week=week,
                date_str=date_str,
            )

            st.session_state["submission_success_message"] = (
                f"Saved {week.title()} contribution: N{float(amount):,.2f}."
            )
            st.switch_page("pages/user_dashboard.py")

        except Exception as e:
            st.error(f"Submission failed: {e}")

st.markdown("")
b1, b2 = st.columns([2, 2])

with b1:
    if st.button("Back to Dashboard", use_container_width=True):
        st.switch_page("pages/user_dashboard.py")

with b2:
    if st.button("Logout", use_container_width=True):
        clear_login()
        st.switch_page("pages/login.py")
