import hashlib
from src.Database.GOOGLE_SHEETS_AUTH import get_authentication_data

SALT = "super_random_secret_string"


def hash_password(password: str) -> str:
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()


def store_creds(username: str, password: str):
    auth_sheet = get_authentication_data()

    # get_all_records() already skips header row
    records = auth_sheet.get_all_records()

    existing_users = [row["USERNAME"] for row in records]

    if username in existing_users:
        return False, "Username already exists. Please choose a different one."

    hashed_password = hash_password(password)
    auth_sheet.append_row([username, hashed_password])

    return True, "User created successfully."


def verify_creds(username: str, password: str):
    auth_sheet = get_authentication_data()
    hashed_input = hash_password(password)

    records = auth_sheet.get_all_records()

    for row in records:
        if row["USERNAME"] == username and row["PASSWORD"] == hashed_input:   #headers from spreadsheet
            return True, "Logged in successfully!" 

    return False, "Invalid username or password."


if __name__ == "__main__":
    success, message = store_creds("test", "test123")
    print(message)

    success, message = verify_creds("test", "test123")
    print(message)