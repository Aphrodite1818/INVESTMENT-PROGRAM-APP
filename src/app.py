import streamlit as st
try:
    from src.Tools.session_auth import restore_login
except ModuleNotFoundError:
    from Tools.session_auth import restore_login

st.set_page_config(
    page_title="Family Investment App",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Session defaults
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "username" not in st.session_state:
    st.session_state["username"] = None

if "role" not in st.session_state:
    st.session_state["role"] = "user"   # "admin" or "user"

restore_login()

# -----------------------------
# Routing (login-first)
# -----------------------------
# If not logged in, always force login page
if not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")

# If logged in, send user to correct dashboard by role
username = str(st.session_state.get("username") or "").strip().lower()
role = str(st.session_state.get("role") or "").strip().lower()
if role not in {"admin", "user"}:
    role = "admin" if username == "admin" else "user"
    st.session_state["role"] = role

if role == "admin":
    st.switch_page("pages/Admin_dashboard.py")
else:
    st.switch_page("pages/user_dashboard.py")
