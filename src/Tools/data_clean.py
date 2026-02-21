import pandas as pd


def clean_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["NAME", "AMOUNT PAID", "DATE", "WEEK", "RECEIPT LINK"])

    df = df.copy()
    df.columns = df.columns.str.strip().str.upper()

    for col in ["NAME", "AMOUNT PAID", "DATE", "WEEK", "RECEIPT LINK"]:
        if col not in df.columns:
            df[col] = ""

    df["NAME"] = df["NAME"].astype(str).str.strip().str.title()

    df["AMOUNT PAID"] = (
        df["AMOUNT PAID"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("?", "", regex=False)
        .str.replace("N", "", regex=False)
        .str.strip()
    )
    df["AMOUNT PAID"] = pd.to_numeric(df["AMOUNT PAID"], errors="coerce")

    df["DATE"] = pd.to_datetime(df["DATE"], format="%d/%m/%Y", errors="coerce")
    df["WEEK"] = df["WEEK"].astype(str).str.strip().str.lower()

    return df

