import hashlib
try:
    from src.Database.GOOGLE_SHEETS_AUTH import clear_auth_cache, get_auth_records, get_authentication_data
except ModuleNotFoundError:
    from Database.GOOGLE_SHEETS_AUTH import clear_auth_cache, get_auth_records, get_authentication_data

SALT = "super_random_secret_string"


def hash_password(password: str) -> str:
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()


def store_creds(username: str, password: str):
    username = str(username or "").strip().title()
    password = str(password or "")
    if not username or not password:
        return False, "Username and password are required."

    auth_sheet = get_authentication_data()

    records = get_auth_records()

    existing_users = [str(row.get("USERNAME", "")).strip().title() for row in records]

    if username in existing_users:
        return False, "Username already exists. Please choose a different one."

    hashed_password = hash_password(password)
    auth_sheet.append_row([username, hashed_password])
    clear_auth_cache()

    return True, "User created successfully."


def verify_creds(username: str, password: str):
    username = str(username or "").strip().title()
    password = str(password or "")
    if not username or not password:
        return False, "Username and password are required."

    hashed_input = hash_password(password)
    records = get_auth_records()

    for row in records:
        if str(row.get("USERNAME", "")).strip().title() == username and row.get("PASSWORD") == hashed_input:
            return True, "Logged in successfully!" 

    return False, "Invalid username or password."


if __name__ == "__main__":
    success, message = store_creds("test", "test123")
    print(message)

    success, message = verify_creds("test", "test123")
    print(message)
