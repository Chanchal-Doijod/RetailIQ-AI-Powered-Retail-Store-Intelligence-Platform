import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

POS_FILE = BASE_DIR / "data" / "resources" / "pos_transactions.csv"
def get_top_brands():

    df = pd.read_csv(POS_FILE)

    brands = (
        df["brand_name"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    return brands