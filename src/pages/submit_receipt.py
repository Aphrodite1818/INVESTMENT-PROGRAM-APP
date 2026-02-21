import streamlit as st
from datetime import datetime

from src.Database.GOOGLE_SHEETS import append_transaction, get_transaction_data
from src.Tools.data_clean import clean_transaction_data

GREEN = "#1b8a3a"
GREEN_LIGHT = "#a5d6a7"
MIN_AMOUNT = 1000.0
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


hide_sidebar()
st.markdown(f"<h1 style='text-align:center; color:{GREEN};'>Submit Contribution</h1>", unsafe_allow_html=True)

if not st.session_state.get("authenticated"):
    st.error("Please log in first.")
    st.stop()

if st.session_state.get("role") == "admin":
    st.switch_page("pages/Admin_dashboard.py")

username = st.session_state.get("username")
if not username:
    st.error("No username found in session.")
    st.stop()

st.markdown(f"<h3 style='color:{GREEN};'>User: {str(username).strip().title()}</h3>", unsafe_allow_html=True)

l, c, r = st.columns([1, 2, 1])
with c:
    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:center; color:{GREEN_LIGHT};'>Enter your weekly amount and choose the contribution week.</div>",
            unsafe_allow_html=True,
        )

        amount = st.number_input("Amount Paid (N)", min_value=MIN_AMOUNT, step=100.0, format="%.2f")
        week_number = st.selectbox("Contribution Week", options=list(range(START_WEEK, END_WEEK + 1)), index=0)
        week = f"week {week_number}"

        submitted = st.button("Submit", use_container_width=True)

    if submitted:
        if amount < MIN_AMOUNT:
            st.error(f"Amount must not be less than N{MIN_AMOUNT:,.0f}.")
            st.stop()

        if week_number < START_WEEK or week_number > END_WEEK:
            st.error(f"Week must be between {START_WEEK} and {END_WEEK}.")
            st.stop()

        date_str = datetime.now().strftime("%d/%m/%Y")

        try:
            existing_df = clean_transaction_data(get_transaction_data(force_refresh=True))
            if not existing_df.empty:
                existing_df["NAME"] = existing_df["NAME"].astype(str).str.strip().str.title()
                existing_df["WEEK"] = existing_df["WEEK"].astype(str).str.strip().str.lower()
                is_duplicate = (
                    (existing_df["NAME"] == str(username).strip().title())
                    & (existing_df["WEEK"] == week.lower())
                ).any()
                if is_duplicate:
                    st.error(f"You have already submitted for {week.title()}.")
                    st.stop()

            append_transaction(
                name=username,
                amount_paid=float(amount),
                week=week,
                date_str=date_str,
            )

            st.session_state["submission_success_message"] = f"Saved {week.title()} contribution: N{float(amount):,.2f}."
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
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["role"] = "user"
        st.switch_page("pages/login.py")

