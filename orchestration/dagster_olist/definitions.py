"""
Dagster definitions for the Olist BigQuery pipeline.

Pipeline (Dagster-orchestrated):
  ingest (local or GCS) -> dbt run -> dbt test (store failures) -> data_quality -> dbt docs generate.

Run:
  cd olist-data-pipeline_bigquery
  conda activate olist-bq
  set -a && source .env && set +a

  # Option A: UI and run from there
  dagster dev -f orchestration/dagster_olist/definitions.py

  # Option B: execute job from CLI (default: local ingest)
  dagster job execute -f orchestration/dagster_olist/definitions.py -j olist_elt_job

  # Option B with GCS ingest
  USE_GCS_INGEST=1 dagster job execute -f orchestration/dagster_olist/definitions.py -j olist_elt_job
"""
import os
import subprocess
import sys

from dagster import Definitions, JobDefinition, ScheduleDefinition, job, op

# Project root (parent of orchestration/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DBT_DIR = os.path.join(ROOT_DIR, "dbt_olist")


def _load_dotenv():
    """Load .env into os.environ so subprocesses see BQ_PROJECT, etc."""
    env_path = os.path.join(ROOT_DIR, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def _run(cmd, cwd=None):
    env = os.environ.copy()
    _load_dotenv()
    subprocess.run(cmd, check=True, cwd=cwd or ROOT_DIR, env=env)


@op
def ingest_op(context):
    """Ingest raw CSVs into BigQuery (raw_olist). Uses USE_GCS_INGEST env to pick script."""
    use_gcs = os.environ.get("USE_GCS_INGEST", "0").strip().lower() in ("1", "true", "yes")
    script = (
        "gcs_pipeline/upload_and_ingest_raw_olist.py"
        if use_gcs
        else "ingestion/ingest_raw_olist.py"
    )
    if not use_gcs:
        context.log.warning(
            "Using local-drive ingestion (USE_GCS_INGEST is false). "
            "If you expected a Kaggle extractor, it is bypassed in this pipeline."
        )
    context.log.info(f"Running ingestion: {script} (USE_GCS_INGEST={use_gcs})")
    _run([sys.executable, script])


@op
def dbt_run_op(_previous):  # noqa: ARG001 - dependency only, no data passed
    _run(["dbt", "run"], cwd=DBT_DIR)


@op
def dbt_test_op(_previous):  # noqa: ARG001 - dependency only
    # Store failures so test failures are materialized (helps isolate root causes)
    # Note: this is safe even if there are no failures.
    _run(["dbt", "test", "--store-failures"], cwd=DBT_DIR)


@op
def data_quality_op(_previous):  # noqa: ARG001 - dependency only
    _run([sys.executable, "data_quality/ge_raw_order_items.py"], cwd=ROOT_DIR)


@op
def dbt_docs_op(_previous):  # noqa: ARG001 - dependency only
    """Generate dbt docs artifacts (manifest/catalog), used by downstream analysis tooling."""
    _run(["dbt", "docs", "generate"], cwd=DBT_DIR)


@job
def olist_elt_job():
    """Full pipeline: ingest -> dbt run -> dbt test (store failures) -> data_quality -> dbt docs."""
    dbt_docs_op(data_quality_op(dbt_test_op(dbt_run_op(ingest_op()))))


olist_daily_schedule = ScheduleDefinition(
    job=olist_elt_job,
    cron_schedule="0 2 * * *",  # daily at 02:00
)


defs = Definitions(
    jobs=[olist_elt_job],
    schedules=[olist_daily_schedule],
)
