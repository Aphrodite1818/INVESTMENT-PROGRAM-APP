from pathlib import Path
import json
import os

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = Path(__file__).resolve().parents[2] / "Database_credentials.json"

FAMILY_CONTRIBUTION_SHEET_ID = "1B8A_dYd9HpO7tjKDtofsby_cXvGqouCrklhZ-iSiO8Q"


@st.cache_resource(show_spinner=False)
def _get_client():
    creds = _load_credentials()
    return gspread.authorize(creds)


def _load_credentials() -> Credentials:
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)

    env_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    if env_json:
        return Credentials.from_service_account_info(json.loads(env_json), scopes=SCOPES)

    if CREDENTIALS_PATH.exists():
        return Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=SCOPES)

    raise FileNotFoundError(
        "Google credentials not found. Provide st.secrets['gcp_service_account'] on Streamlit Cloud "
        "or add Database_credentials.json locally."
    )


def get_authentication_data():
    return _get_client().open_by_key(FAMILY_CONTRIBUTION_SHEET_ID).worksheet("AUTHENTICATION")


@st.cache_data(ttl=60, show_spinner=False)
def get_auth_records():
    return get_authentication_data().get_all_records()


def clear_auth_cache() -> None:
    get_auth_records.clear()


def view_authentication_data():
    return get_auth_records()

