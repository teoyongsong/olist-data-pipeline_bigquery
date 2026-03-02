"""
Upload Olist CSVs to a GCS bucket, then ingest them into BigQuery (raw_olist).

Flow (v2):
- Read CSVs from DATA_DIR
- Upload each to gs://GCS_BUCKET/GCS_PREFIX/<filename>
- Use BigQuery load jobs to load from GCS into raw_olist tables

Requirements:
- GCS bucket already exists
- Env/config: BQ_PROJECT, BQ_DATASET_RAW, DATA_DIR, GCS_BUCKET, (optional) GCS_PREFIX
"""
import os
import sys
from typing import Dict

from google.cloud import bigquery
from google.cloud import storage

# Add project root for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (  # noqa: E402
    BQ_PROJECT,
    BQ_DATASET_RAW,
    DATA_DIR,
    GCS_BUCKET,
    GCS_PREFIX,
)

# Map Kaggle CSV filenames to BigQuery table names
TABLE_MAPPING: Dict[str, str] = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_reviews_dataset.csv": "order_reviews",
}


def ensure_raw_dataset(client: bigquery.Client) -> None:
    dataset_id = f"{BQ_PROJECT}.{BQ_DATASET_RAW}"
    try:
        client.get_dataset(dataset_id)
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {BQ_DATASET_RAW}.")


def upload_file(storage_client: storage.Client, local_path: str, blob_name: str) -> str:
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    print(f"Uploading {local_path} to gs://{GCS_BUCKET}/{blob_name} ...")
    blob.upload_from_filename(local_path)
    return f"gs://{GCS_BUCKET}/{blob_name}"


def load_from_gcs(
    bq_client: bigquery.Client,
    uri: str,
    table: str,
) -> None:
    table_id = f"{BQ_PROJECT}.{BQ_DATASET_RAW}.{table}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    print(f"Loading {uri} into {table_id} ...")
    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()
    dest_table = bq_client.get_table(table_id)
    print(f"Loaded {dest_table.num_rows} rows into {table_id}")


def main() -> int:
    if not DATA_DIR or not os.path.isdir(DATA_DIR):
        print(f"DATA_DIR not found: {DATA_DIR}")
        print("Create it and place Olist CSV files there (from Kaggle).")
        return 1

    if not GCS_BUCKET:
        print("GCS_BUCKET is not set. Set it in .env before running this script.")
        return 1

    storage_client = storage.Client(project=BQ_PROJECT)
    bq_client = bigquery.Client(project=BQ_PROJECT)

    ensure_raw_dataset(bq_client)

    for filename, table in TABLE_MAPPING.items():
        local_path = os.path.join(DATA_DIR, filename)
        if not os.path.isfile(local_path):
            print(f"Skip (file not found): {local_path}")
            continue

        blob_name = f"{GCS_PREFIX.rstrip('/')}/{filename}"
        uri = upload_file(storage_client, local_path, blob_name)
        load_from_gcs(bq_client, uri, table)

    print("GCS upload + BigQuery ingestion complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

