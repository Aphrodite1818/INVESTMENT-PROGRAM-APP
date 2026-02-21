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

