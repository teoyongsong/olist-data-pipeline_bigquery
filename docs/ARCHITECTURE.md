## Olist BigQuery Data Pipeline – Architecture

This document describes the end-to-end architecture for the Olist e‑commerce data pipeline on Google Cloud.

---

### 1. High-level overview

At a high level, the pipeline follows an **ELT** pattern:

- **Extract / Land**: Raw CSVs from Kaggle (Olist dataset) are downloaded locally and optionally uploaded to **GCS**.
- **Load**: BigQuery ingests CSVs from **local disk** or **GCS** into the `raw_olist` dataset.
- **Transform**: **dbt** builds staging views and star-schema marts in `dw_stg_olist` and `dw_dw`.
- **Quality**: A Python data-quality step validates `raw_olist.order_items`.
- **Orchestrate**: **Prefect** and **Dagster** can run the entire pipeline as a single job/flow.
- **Consume**: The **EDA notebook** queries `dw_dw` in BigQuery for metrics and visualizations.

In text:

- **User / Developer**
  - ↕️ runs scripts, Dagster job, Prefect flow, or notebooks
- **Kaggle**
  - ➝ `ingest_*_from_kaggle.sh` ➝ local `data/olist/*.csv`
- **Local disk (`DATA_DIR`)**
  - ➝ `ingestion/ingest_raw_olist.py` ➝ BigQuery `raw_olist`
  - ➝ `gcs_pipeline/upload_and_ingest_raw_olist.py` ➝ GCS ➝ BigQuery `raw_olist`
- **BigQuery**
  - `raw_olist` ➝ dbt (`dbt_olist/`) ➝ `dw_stg_olist` ➝ `dw_dw`
  - `raw_olist.order_items` ➝ `data_quality/ge_raw_order_items.py`
  - `dw_dw` ➝ `analysis/eda_and_metrics.ipynb`
- **Orchestration**
  - `orchestration/flow.py` (Prefect) or `orchestration/dagster_olist/definitions.py` (Dagster)

---

### 2. Components and responsibilities

- **Local filesystem**
  - `data/olist/*.csv`: raw source files from Kaggle.
  - `ingestion/ingest_raw_olist.py`: loads CSVs directly into BigQuery using `pandas_gbq.to_gbq`.
  - `gcs_pipeline/upload_and_ingest_raw_olist.py`: uploads CSVs to `gs://$GCS_BUCKET/$GCS_PREFIX/...` and uses BigQuery load jobs from GCS.
  - `orchestration/ingest_local_from_kaggle.sh` / `ingest_gcs_from_kaggle.sh`: helper scripts to download from Kaggle + call the appropriate ingestion path.

- **Google Cloud Storage (optional)**
  - Bucket: `GCS_BUCKET` (from `.env`).
  - Prefix: `GCS_PREFIX` (e.g. `olist_raw`).
  - Holds a copy of the raw CSVs used as load sources for BigQuery.

- **BigQuery**
  - Dataset `raw_olist`: raw tables loaded 1:1 from CSVs.
  - Dataset `dw_stg_olist`: dbt staging views.
  - Dataset `dw_dw`: dbt star-schema marts:
    - `dim_customer`, `dim_product`, `dim_seller`, `dim_date`, `fact_order_items`, `fact_orders`.
    - `fact_orders` is built with an **aggregate first → then join** pattern (one row per order; use for order-level analytics and benchmarks).

- **dbt (`dbt_olist/`)**
  - Reads from `raw_olist` via `models/sources.yml`.
  - Staging layer in `dw_stg_olist` (views).
  - Marts in `dw_dw` (tables).
  - Tests ensure referential integrity and other constraints.

- **Data quality**
  - `data_quality/ge_raw_order_items.py`:
    - Loads `raw_olist.order_items` with `pandas_gbq`.
    - Runs simple Pandas checks and optional Great Expectations suite.

- **Analysis**
  - `analysis/eda_and_metrics.ipynb`:
    - Uses `pandas_gbq` and `config.BQ_PROJECT`, `config.BQ_DATASET_DW`.
    - Produces:
      - Monthly revenue & order volume.
      - Top product categories by revenue.
      - Customer tenure segments & CLV.
      - Late delivery rate.

- **Orchestration**
  - `orchestration/flow.py`:
    - Python + Prefect-based flow.
    - Runs: ingest → dbt run → dbt test → data quality.
    - Controlled by `USE_GCS_INGEST` env var for ingestion mode.
  - `orchestration/dagster_olist/definitions.py`:
    - Dagster job `olist_elt_job` with ops for ingest, dbt run/test, and data quality.
    - Also respects `USE_GCS_INGEST` to pick local vs. GCS ingestion.

---

### 3. Data flow (step-by-step)

1. **Download / land**
   - Run `orchestration/ingest_local_from_kaggle.sh` or `ingest_gcs_from_kaggle.sh`:
     - Uses Kaggle CLI to download the zip.
     - Unzips into `DATA_DIR` (e.g. `data/olist`).

2. **Ingest raw data**
   - Local mode:
     - `ingestion/ingest_raw_olist.py`:
       - Reads each CSV into Pandas.
       - Writes to `raw_olist.<table>` via `pandas_gbq.to_gbq`.
   - GCS mode:
     - `gcs_pipeline/upload_and_ingest_raw_olist.py`:
       - Uploads CSVs to `gs://$GCS_BUCKET/$GCS_PREFIX/`.
       - Uses BigQuery load jobs with `allow_quoted_newlines` to create/replace `raw_olist.<table>`.

3. **Transform with dbt**
   - `dbt_olist/`:
     - `dbt deps` to install packages.
     - `dbt run` to build `dw_stg_olist` views and `dw_dw` tables.
     - `dbt test` for schema and data tests.

4. **Run data quality checks**
   - `python data_quality/ge_raw_order_items.py`:
     - Checks key columns for nulls.
     - Ensures price and freight are non-negative.
     - Optionally runs a Great Expectations suite.

5. **Run the EDA notebook**
   - Start Jupyter with the `olist-bq` environment from the project root.
   - Open `analysis/eda_and_metrics.ipynb`.
   - Run all cells:
     - Reads from `dw_dw.fact_order_items` and other dims.
     - Generates charts and prints out key metrics.

6. **Run orchestrated flows (optional)**
   - Prefect:
     - `python orchestration/flow.py`
   - Dagster:
     - `dagster dev -f orchestration/dagster_olist/definitions.py` then run `olist_elt_job` from the UI, or:
     - `dagster job execute -f orchestration/dagster_olist/definitions.py -j olist_elt_job`

---

### 4. Operational concerns

- **Configuration**
  - `.env`:
    - `BQ_PROJECT`, `BQ_DATASET_RAW`, `BQ_DATASET_DW`, `DATA_DIR`.
    - `GCS_BUCKET`, `GCS_PREFIX`.
    - Optional `GOOGLE_APPLICATION_CREDENTIALS` for service account JSON.
  - `config.py` wraps these with defaults and helper getters.

- **Authentication**
  - Application Default Credentials:
    - `gcloud auth application-default login`
  - Or service account JSON pointed to by `GOOGLE_APPLICATION_CREDENTIALS`.

- **Environments**
  - Conda env: `olist-bq` defined in `environment.yml`.
  - All scripts, dbt, Dagster, Prefect, and the notebook are expected to run under this env.

---

### 4.1 Publishing dbt documentation (GitHub Pages)

By default, dbt writes generated docs into `dbt_olist/target/` (ignored by git). To make the docs visible to GitHub repo viewers, this project publishes a copy under `docs/dbt/`, which can be served by GitHub Pages.

- **Generate docs**
  - Run the Dagster job (includes `dbt docs generate`) or run locally:
    - `cd dbt_olist && dbt docs generate`

- **Publish docs to GitHub Pages**
  - Copy the generated site bundle:
    - `cp -R dbt_olist/target/* docs/dbt/`
  - Commit + push `docs/dbt/`.

- **View**
  - Locally:
    - `cd docs/dbt && python3 -m http.server 8000` then open `http://localhost:8000/index.html`
  - On GitHub Pages (if configured to serve `/docs`):
    - `.../dbt/index.html`

---

### 5. How the three core metrics map to the architecture

- **Monthly revenue trend**
  - Source: `dw_dw.fact_order_items` (via EDA notebook).
  - Upstream:
    - `ingestion/*` → `raw_olist.order_items`.
    - `dbt_olist/models/marts/fact_order_items.sql`.

- **Top product categories by revenue**
  - Source: join of `fact_order_items` and `dim_product`.
  - Upstream:
    - `raw_olist.products`, `raw_olist.order_items`.
    - dbt staging + marts layer.

- **Customer segmentation & CLV + late delivery rate**
  - `dim_customer` (tenure segment, total_revenue) + `fact_order_items` (is_late_delivery).
  - All built in `dw_dw` by dbt, then visualized in the notebook.

