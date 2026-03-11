"""
Pipeline orchestration for BigQuery (ingest -> dbt run -> dbt test -> data quality).
Set BQ_PROJECT, DATA_DIR in .env. Install: pip install dbt-bigquery.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

USE_GCS_INGEST = os.environ.get("USE_GCS_INGEST", "0").strip().lower() in ("1", "true", "yes")


def ingest():
    script = (
        "gcs_pipeline/upload_and_ingest_raw_olist.py"
        if USE_GCS_INGEST
        else "ingestion/ingest_raw_olist.py"
    )
    subprocess.run([sys.executable, script], check=True, cwd=ROOT)


def dbt_run():
    subprocess.run(["dbt", "run"], check=True, cwd=os.path.join(ROOT, "dbt_olist"))


def dbt_test():
    subprocess.run(["dbt", "test"], check=True, cwd=os.path.join(ROOT, "dbt_olist"))


def data_quality():
    subprocess.run(
        [sys.executable, "data_quality/ge_raw_order_items.py"],
        check=True,
        cwd=ROOT,
    )


def run_all():
    ingest()
    dbt_run()
    dbt_test()
    data_quality()
    print("Pipeline finished successfully.")


if __name__ == "__main__":
    try:
        from prefect import flow
        @flow(name="olist_elt_pipeline_bq")
        def elt_flow():
            ingest()
            dbt_run()
            dbt_test()
            data_quality()
        elt_flow()
    except ImportError:
        run_all()
