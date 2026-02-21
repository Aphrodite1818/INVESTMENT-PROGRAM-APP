import streamlit as st
try:
    from src.Tools.Auth import verify_creds, store_creds
    from src.Tools.background import set_background
    from src.Tools.session_auth import persist_login, restore_login
except ModuleNotFoundError:
    from Tools.Auth import verify_creds, store_creds
    from Tools.background import set_background
    from Tools.session_auth import persist_login, restore_login
from pathlib import Path

GREEN = "#1b8a3a"

restore_login()
if st.session_state.get("authenticated"):
    persist_login(st.session_state.get("username"), st.session_state.get("role", "user"))
    if st.session_state.get("role") == "admin":
        st.switch_page("pages/Admin_dashboard.py")
    st.switch_page("pages/user_dashboard.py")

set_background(Path(__file__).resolve().parents[2] / "images" / "login_page_image.png")

st.markdown(
    f"<h1 style='text-align: center; color: {GREEN};'>Family Investment App</h1>",
    unsafe_allow_html=True
)

# Center everything
left, center, right = st.columns([1, 2, 1])

with center:

    # Radio selector centered
    option = st.radio(
        "",
        ["Login", "Sign Up"],
        horizontal=True
    )

    st.markdown(
        f"<h2 style='color: {GREEN}; text-align: center;'>{option}</h2>",
        unsafe_allow_html=True
    )

    with st.container(border=True):

        if option == "Login":

            with st.form("login_form",border=False):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                success, message = verify_creds(username, password)
                if success:
                    clean_user = str(username).strip().title()
                    if clean_user.lower() == "admin":
                        persist_login(clean_user, "admin")
                        st.switch_page("pages/Admin_dashboard.py")
                    else:
                        persist_login(clean_user, "user")
                        st.switch_page("pages/user_dashboard.py")
                else:
                    st.error(message)

        else:

            with st.form("signup_form", border=False):
                new_username = st.text_input("New Username", key="signup_user")
                new_password = st.text_input("New Password", type="password", key="signup_pass")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                success, message = store_creds(new_username, new_password)
                if success:
                    clean_user = str(new_username).strip().title()
                    if clean_user.lower() == "admin":
                        persist_login(clean_user, "admin")
                        st.switch_page("pages/Admin_dashboard.py")
                    else:
                        persist_login(clean_user, "user")
                        st.switch_page("pages/user_dashboard.py")
                else:
                    st.error(message)
