import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
]


creds = Credentials.from_service_account_file("Database_credentials.json", scopes=scopes)
client = gspread.authorize(creds)


family_contribution_sheet_id = "1B8A_dYd9HpO7tjKDtofsby_cXvGqouCrklhZ-iSiO8Q"


def get_authentication_data():
    auth_sheet = client.open_by_key(family_contribution_sheet_id).worksheet("AUTHENTICATION")
    return auth_sheet


def view_authentication_data():
    auth_sheet = get_authentication_data()
    return auth_sheet.get_all_records()

if __name__ == "__main__":
    auth_data = get_authentication_data()
    print(auth_data)