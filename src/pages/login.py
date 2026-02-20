import streamlit as st
from src.Tools.Auth import verify_creds, store_creds
from src.Tools.background import set_background
from pathlib import Path

def login_page():
    set_background(Path(__file__).parent.resolve() / "images" / "login_page_image.png")

    st.title("Family Investment App")
    option = st.radio("Choose an option", ["Login", "Sign Up"], horizontal=True)

    if option == "Login":
        st.subheader("Login")

        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login")

        if submitted:
            success, message = verify_creds(username, password)
            if success:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success(message)
            else:
                st.error(message)

    elif option == "Sign Up":
        st.subheader("Sign Up")

        with st.form("signup_form"):
            new_username = st.text_input("New Username", key="signup_user")
            new_password = st.text_input("New Password", type="password", key="signup_pass")
            submitted = st.form_submit_button("Create Account")

        if submitted:
            success, message = store_creds(new_username, new_password)
            if success:
                st.success(message)
                st.info("Now switch to Login and sign in.")
            else:
                st.error(message)