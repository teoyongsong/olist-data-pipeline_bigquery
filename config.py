"""
BigQuery pipeline configuration. Uses environment variables with fallbacks for local dev.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# BigQuery
BQ_PROJECT = os.getenv("BQ_PROJECT", "olistdatapipelinebigquery")  # GCP project id
BQ_DATASET_RAW = os.getenv("BQ_DATASET_RAW", "raw_olist")
BQ_DATASET_STAGING = os.getenv("BQ_DATASET_STAGING", "dw_stg_olist")
# Warehouse dataset (dbt marts). Normally "dw_dw" for this project.
BQ_DATASET_DW = os.getenv("BQ_DATASET_DW", "dw_dw")
# Optional: path to service account JSON; if unset, uses ADC (gcloud auth application-default login)
BQ_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data", "olist"))


def get_bq_project():
    return BQ_PROJECT


def get_bq_raw_dataset():
    return BQ_DATASET_RAW


def get_bq_dw_dataset():
    return BQ_DATASET_DW
