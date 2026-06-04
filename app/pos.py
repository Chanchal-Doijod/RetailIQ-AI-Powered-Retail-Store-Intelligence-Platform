import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

POS_FILE = BASE_DIR / "data" / "resources" / "pos_transactions.csv"

def load_transactions():

    try:
        df = pd.read_csv(POS_FILE)
        return df

    except Exception as e:
        print("POS Load Error:", e)
        return None


def get_transaction_count(store_id):

    df = load_transactions()

    if df is None:
        return 0

    if "store_id" not in df.columns:
        return len(df)

    return len(
        df[df["store_id"] == store_id]
    )