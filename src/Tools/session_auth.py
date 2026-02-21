import hashlib
import os

import streamlit as st

_SECRET = os.getenv("SESSION_SECRET", "family-investment-session-secret")
_QP_USER = "u"
_QP_ROLE = "r"
_QP_SIG = "s"


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
        for k, v in params.items():
            qp[k] = str(v)
    except Exception:
        current = st.experimental_get_query_params()
        merged = {k: (v[0] if isinstance(v, list) and v else str(v)) for k, v in current.items()}
        merged.update({k: str(v) for k, v in params.items()})
        st.experimental_set_query_params(**merged)


def _remove_query_params(keys: list[str]) -> None:
    try:
        qp = st.query_params
        for key in keys:
            if key in qp:
                del qp[key]
    except Exception:
        current = st.experimental_get_query_params()
        merged = {k: (v[0] if isinstance(v, list) and v else str(v)) for k, v in current.items()}
        for key in keys:
            merged.pop(key, None)
        st.experimental_set_query_params(**merged)


def persist_login(username: str, role: str) -> None:
    username = str(username or "").strip().title()
    if not username:
        return
    role = str(role or "user").strip().lower()
    st.session_state["logged_out"] = False
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = role
    signature = _sign(username, role)
    params = _get_query_params()
    if (
        params.get(_QP_USER) == username
        and params.get(_QP_ROLE) == role
        and params.get(_QP_SIG) == signature
    ):
        return
    _set_query_params({_QP_USER: username, _QP_ROLE: role, _QP_SIG: signature})


def restore_login() -> None:
    if st.session_state.get("logged_out"):
        return

    if st.session_state.get("authenticated"):
        return

    params = _get_query_params()
    username = str(params.get(_QP_USER, "")).strip().title()
    role = str(params.get(_QP_ROLE, "user")).strip().lower()
    sig = str(params.get(_QP_SIG, "")).strip()
    if not username or not sig:
        return

    if sig == _sign(username, role):
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = role


def clear_login() -> None:
    st.session_state["logged_out"] = True
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["role"] = "user"
    _remove_query_params([_QP_USER, _QP_ROLE, _QP_SIG])
