from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

POS_FILE = BASE_DIR / "data" / "resources" / "pos_transactions.csv"

def get_top_products():

    df = pd.read_csv(POS_FILE)

    products = (
        df["product_id"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    return products