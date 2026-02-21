import streamlit as st 
from src.Database.GOOGLE_SHEETS import get_transaction_data
from src.Tools.data_clean import clean_transaction_data
st.session_state["username"] = "Naomi"


st.title("My Dashboard")

    # Guard
    
#if not st.session_state.get("authenticated"):
    #st.error("Please log in to view this page.")
    #st.stop()
    
username = st.session_state.get("username")

st.write(f"WELCOME: {username}")

# Pull + clean data
df = clean_transaction_data(get_transaction_data())

# Filter to this user only (make sure your sheet has a NAME column)
df = df[df["NAME"].str.strip().str.lower() == str(username).strip().lower()]


    






