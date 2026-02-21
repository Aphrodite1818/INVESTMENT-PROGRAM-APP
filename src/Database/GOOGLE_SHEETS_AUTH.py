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
    required = {"type", "project_id", "private_key", "client_email", "token_uri"}

    def has_required_fields(data: dict) -> bool:
        return required.issubset(set(data.keys()))

    candidate_sections = [
        "gcp_service_account",
        "google_service_account",
        "service_account",
        "google_credentials",
        "gcp",
    ]
    for key in candidate_sections:
        if key in st.secrets:
            section = dict(st.secrets[key])
            if has_required_fields(section):
                return Credentials.from_service_account_info(section, scopes=SCOPES)

    root_secrets = dict(st.secrets)
    if has_required_fields(root_secrets):
        return Credentials.from_service_account_info(root_secrets, scopes=SCOPES)

    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        gsheets = dict(st.secrets["connections"]["gsheets"])
        if has_required_fields(gsheets):
            return Credentials.from_service_account_info(gsheets, scopes=SCOPES)

    env_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    if env_json:
        return Credentials.from_service_account_info(json.loads(env_json), scopes=SCOPES)

    env_json_alt = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if env_json_alt:
        return Credentials.from_service_account_info(json.loads(env_json_alt), scopes=SCOPES)

    if CREDENTIALS_PATH.exists():
        return Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=SCOPES)

    raise FileNotFoundError(
        "Google credentials not found. Add service account fields to Streamlit secrets "
        "(section keys supported: gcp_service_account/google_service_account/service_account) "
        "or provide GOOGLE_CREDENTIALS_JSON env var or Database_credentials.json locally."
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

