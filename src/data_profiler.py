import pandas as pd


def profile_dataframe(df):
    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "null_percent": (df.isna().mean() * 100).round(2).to_dict(),
        "unique_values": df.nunique(dropna=False).to_dict()
    }

    return profile