from pathlib import Path
from datetime import datetime
import json
import os

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = Path(__file__).resolve().parents[2] / "Database_credentials.json"

SHEETS_ID = "1B8A_dYd9HpO7tjKDtofsby_cXvGqouCrklhZ-iSiO8Q"
WORKSHEET_NAME = "TRANSACTION"


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


def _get_sheet():
    return _get_client().open_by_key(SHEETS_ID).worksheet(WORKSHEET_NAME)


@st.cache_data(ttl=45, show_spinner=False)
def _get_transaction_data_cached() -> pd.DataFrame:
    sheet = _get_sheet()
    values = sheet.get_all_values()
    if not values:
        return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0])


def clear_transaction_cache() -> None:
    _get_transaction_data_cached.clear()


def get_transaction_data(force_refresh: bool = False) -> pd.DataFrame:
    if force_refresh:
        clear_transaction_cache()
    return _get_transaction_data_cached().copy()


def append_transaction(
    name: str,
    amount_paid: float,
    week: str,
    date_str: str | None = None,
) -> None:
    ws = _get_sheet()

    if date_str is None:
        date_str = datetime.now().strftime("%d/%m/%Y")

    header = ws.row_values(1)
    header_upper = [h.strip().upper() for h in header]
    row = [""] * len(header_upper)

    def set_col(col_name: str, value) -> None:
        if col_name in header_upper:
            row[header_upper.index(col_name)] = value

    set_col("NAME", str(name).strip().title())
    set_col("AMOUNT PAID", float(amount_paid))
    set_col("DATE", date_str)
    set_col("WEEK", str(week).strip().lower())
    set_col("RECEIPT LINK", "")

    ws.append_row(row, value_input_option="USER_ENTERED")
    clear_transaction_cache()

