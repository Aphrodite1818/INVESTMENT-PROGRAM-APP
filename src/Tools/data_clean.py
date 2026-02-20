import pandas as pd
from src.Database.GOOGLE_SHEETS import get_transaction_data


def clean_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize column names
    df.columns = df.columns.str.strip().str.upper()

    # Clean NAME
    df["NAME"] = df["NAME"].astype(str).str.strip().str.title()

    # Clean AMOUNT PAID (handle commas or currency symbols safely)
    df["AMOUNT PAID"] = (
        df["AMOUNT PAID"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₦", "", regex=False)
        .str.strip()
    )
    df["AMOUNT PAID"] = pd.to_numeric(df["AMOUNT PAID"], errors="coerce")

    # Parse DATE explicitly (15/02/2026 format)
    df["DATE"] = pd.to_datetime(
        df["DATE"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Clean WEEK
    df["WEEK"] = df["WEEK"].astype(str).str.strip().str.lower()

    return df


# Run cleaning
df = clean_transaction_data(get_transaction_data())
print(df.head())