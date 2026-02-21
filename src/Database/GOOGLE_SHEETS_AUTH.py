from pathlib import Path
import json
import os

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = Path(__file__).resolve().parents[2] / "Database_credentials.json"

FAMILY_CONTRIBUTION_SHEET_ID = "1B8A_dYd9HpO7tjKDtofsby_cXvGqouCrklhZ-iSiO8Q"

if load_dotenv is not None:
    load_dotenv()


@st.cache_resource(show_spinner=False)
def _get_client():
    creds = _load_credentials()
    return gspread.authorize(creds)


def _load_credentials() -> Credentials:
    attempted_sources = []

    def normalize_info(data: dict) -> dict:
        info = dict(data)
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        return info

    def try_info(data: dict, source_name: str):
        attempted_sources.append(source_name)
        try:
            return Credentials.from_service_account_info(normalize_info(data), scopes=SCOPES)
        except Exception:
            return None

    candidate_sections = [
        "gcp_service_account",
        "google_service_account",
        "service_account",
        "google_credentials",
        "gcp",
    ]
    for key in candidate_sections:
        if key in st.secrets:
            creds = try_info(dict(st.secrets[key]), f"st.secrets[{key}]")
            if creds is not None:
                return creds

    creds = try_info(dict(st.secrets), "st.secrets(root)")
    if creds is not None:
        return creds

    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        creds = try_info(dict(st.secrets["connections"]["gsheets"]), "st.secrets[connections][gsheets]")
        if creds is not None:
            return creds

    env_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    if env_json:
        creds = try_info(json.loads(env_json), "GOOGLE_CREDENTIALS_JSON")
        if creds is not None:
            return creds

    env_json_alt = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if env_json_alt:
        creds = try_info(json.loads(env_json_alt), "GOOGLE_SERVICE_ACCOUNT_JSON")
        if creds is not None:
            return creds

    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if env_path and Path(env_path).exists():
        attempted_sources.append("GOOGLE_APPLICATION_CREDENTIALS(path)")
        return Credentials.from_service_account_file(env_path, scopes=SCOPES)

    if CREDENTIALS_PATH.exists():
        attempted_sources.append("Database_credentials.json")
        return Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=SCOPES)

    raise FileNotFoundError(
        "Google credentials not found or invalid. Checked: "
        + ", ".join(attempted_sources)
        + ". Configure Streamlit secrets or environment credentials."
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

