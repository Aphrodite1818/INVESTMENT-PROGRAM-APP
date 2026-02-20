import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Define the scope for Google Sheets API
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# Authenticate and create a client to interact with the Google Sheets API
creds = Credentials.from_service_account_file("Database_credentials.json", scopes=scopes)
client = gspread.authorize(creds)

sheets_id = "1B8A_dYd9HpO7tjKDtofsby_cXvGqouCrklhZ-iSiO8Q" #found this from the url of the sheet

def get_transaction_data():
    sheet = client.open_by_key(sheets_id).worksheet("TRANSACTION")
    values = sheet.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df



if __name__ == "__main__":
    df = get_transaction_data()
    print(df)