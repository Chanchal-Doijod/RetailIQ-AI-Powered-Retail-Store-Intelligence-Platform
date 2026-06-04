import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

POS_FILE = BASE_DIR / "data" / "resources" / "pos_transactions.csv"

def get_store_summary(store_id):

    df = pd.read_csv(POS_FILE)

    store_df = df[
        df["store_id"].astype(str) == str(store_id)
    ]

    if len(store_df) == 0:
        return {
            "store_id": store_id,
            "transactions": 0
        }

    return {
    "store_id": store_id,
    "transactions": len(store_df),

    "revenue": float(
        store_df["total_amount"].sum()
    ),

    "top_brand":
    store_df["brand_name"]
    .value_counts()
    .idxmax(),

    "top_product":
    str(
        store_df["product_id"]
        .value_counts()
        .idxmax()
    )
}