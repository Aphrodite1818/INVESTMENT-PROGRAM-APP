import hashlib
import os

import streamlit as st

_SECRET = os.getenv("SESSION_SECRET", "family-investment-session-secret")


def _sign(username: str, role: str) -> str:
    payload = f"{username}|{role}|{_SECRET}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_query_params() -> dict:
    try:
        qp = st.query_params
        return {k: str(v) for k, v in qp.items()}
    except Exception:
        params = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) and v else str(v)) for k, v in params.items()}


def _set_query_params(params: dict) -> None:
    try:
        qp = st.query_params
        qp.clear()
        for k, v in params.items():
            qp[k] = str(v)
    except Exception:
        st.experimental_set_query_params(**params)


def persist_login(username: str, role: str) -> None:
    username = str(username or "").strip().title()
    role = str(role or "user").strip().lower()
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = role
    _set_query_params({"u": username, "r": role, "s": _sign(username, role)})


def restore_login() -> None:
    if st.session_state.get("authenticated"):
        return

    params = _get_query_params()
    username = str(params.get("u", "")).strip().title()
    role = str(params.get("r", "user")).strip().lower()
    sig = str(params.get("s", "")).strip()
    if not username or not sig:
        return

    if sig == _sign(username, role):
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = role


def clear_login() -> None:
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["role"] = "user"
    _set_query_params({})
