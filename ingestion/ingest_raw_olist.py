"""
Ingest Olist Brazilian E-Commerce CSV files into Google BigQuery.
Download dataset from Kaggle: Brazilian E-Commerce Public Dataset by Olist.
Place CSVs in DATA_DIR (default: project/data/olist).
Uses BigQuery load jobs (CSV) or pandas-gbq; creates dataset if missing.
"""
import os
import sys

import pandas as pd
import pandas_gbq
from google.cloud import bigquery

# Add project root for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BQ_PROJECT, BQ_DATASET_RAW, DATA_DIR

# Map Kaggle CSV filenames to BigQuery table names
TABLE_MAPPING = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_reviews_dataset.csv": "order_reviews",
}


def main():
    if not os.path.isdir(DATA_DIR):
        print(f"DATA_DIR not found: {DATA_DIR}")
        print("Create it and place Olist CSV files there (from Kaggle).")
        sys.exit(1)

    client = bigquery.Client(project=BQ_PROJECT)
    dataset_id = f"{BQ_PROJECT}.{BQ_DATASET_RAW}"
    try:
        client.get_dataset(dataset_id)
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {BQ_DATASET_RAW}.")

    for filename, table in TABLE_MAPPING.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.isfile(path):
            print(f"Skip (file not found): {path}")
            continue
        df = pd.read_csv(path)
        table_id = f"{BQ_PROJECT}.{BQ_DATASET_RAW}.{table}"
        destination = f"{BQ_DATASET_RAW}.{table}"
        pandas_gbq.to_gbq(
            df,
            destination_table=destination,
            project_id=BQ_PROJECT,
            if_exists="replace",
            progress_bar=True,
        )
        print(f"Loaded {len(df)} rows into {table_id}")

    print("Ingestion complete.")


if __name__ == "__main__":
    main()
