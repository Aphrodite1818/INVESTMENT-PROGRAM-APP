from pathlib import Path

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = Path(__file__).resolve().parents[2] / "Database_credentials.json"

FAMILY_CONTRIBUTION_SHEET_ID = "1B8A_dYd9HpO7tjKDtofsby_cXvGqouCrklhZ-iSiO8Q"


@st.cache_resource(show_spinner=False)
def _get_client():
    creds = Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=SCOPES)
    return gspread.authorize(creds)


def get_authentication_data():
    return _get_client().open_by_key(FAMILY_CONTRIBUTION_SHEET_ID).worksheet("AUTHENTICATION")


@st.cache_data(ttl=60, show_spinner=False)
def get_auth_records():
    return get_authentication_data().get_all_records()


def clear_auth_cache() -> None:
    get_auth_records.clear()


def view_authentication_data():
    return get_auth_records()

