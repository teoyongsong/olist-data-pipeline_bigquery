## Olist BigQuery Data Pipeline – User Manual

This manual explains how to install, configure, and run the Olist E‑Commerce data pipeline on Google BigQuery, including the newer version that uploads CSVs to Google Cloud Storage (GCS) before ingestion.

---

### 1. Audience and Overview

- **Who this is for**: Data engineers or analysts who want a ready‑made BigQuery warehouse for the Olist Brazilian E‑Commerce dataset, plus an EDA notebook with key metrics.
- **What it does**:
  - Ingests raw CSVs from the Olist Kaggle dataset into BigQuery (`raw_olist`).
  - Builds a star schema (`dw_dw`) using dbt.
  - Runs basic data quality checks.
  - Provides a Jupyter notebook to explore monthly revenue, top categories, customer segments, and late delivery rates.
  - Supports two ingestion modes:
    - **V1**: Direct from local disk → BigQuery.
    - **V2**: Local disk → GCS bucket → BigQuery (recommended for “cloud‑native” flows).

---

### 2. Prerequisites

- **Accounts and projects**
  - Google Cloud project with **BigQuery** and **Cloud Storage** enabled.
  - Kaggle account to download the Olist dataset.
- **Local tools**
  - Python 3.10+
  - Conda (recommended) or Python venv.
  - Google Cloud SDK (`gcloud`, `bq`, `gsutil`) installed and configured.

---

### 3. Installation

From your terminal (WSL in your case):

```bash
cd ~/olist-data-pipeline_bigquery
conda env create -f environment.yml
conda activate olist-bq
```

This installs:
- BigQuery and GCS clients (`google-cloud-bigquery`, `google-cloud-storage`)
- `pandas`, `pandas-gbq`, `dbt-bigquery`, `jupyter`, and other dependencies.

---

### 4. Configuration

#### 4.1 Environment file

Create and edit `.env` in the project root:

```bash
cd ~/olist-data-pipeline_bigquery
cp .env.example .env
```

Open `.env` and set at least:

- **`BQ_PROJECT`** – your GCP project ID  
  Example: `BQ_PROJECT=my-gcp-project-id`
- **`DATA_DIR`** – where the CSVs live  
  Example: `DATA_DIR=./data/olist`
- **`GCS_BUCKET`** – (for v2) a GCS bucket you created in that project  
  Example: `GCS_BUCKET=my-olist-raw-bucket`
- **`GCS_PREFIX`** – sub‑folder/prefix in that bucket (optional, defaults to `olist_raw`)  
  Example: `GCS_PREFIX=olist_raw`

Optional:
- `GOOGLE_APPLICATION_CREDENTIALS` – if you use a service account JSON instead of `gcloud auth application-default login`.

To load the env into your shell:

```bash
set -a && source .env && set +a
```

#### 4.2 Authentication

Either:

- **Application Default Credentials** (simple for local dev):

  ```bash
  gcloud auth application-default login
  ```

Or:

- **Service account JSON**:
  - Create a service account with BigQuery + Storage permissions.
  - Download the JSON key.
  - Set in `.env`:

    ```bash
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    ```

Verify:

```bash
bq ls --project_id="$BQ_PROJECT"
```

---

### 5. Data Preparation (Olist CSVs)

1. Download the **Brazilian E-Commerce Public Dataset by Olist** from Kaggle.
2. Unzip and copy all CSV files into the directory configured as `DATA_DIR` (default: `data/olist/`).

You should have files including:

- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `product_category_name_translation.csv`

Check:

```bash
ls data/olist/*.csv
```

---

### 6. Running the Pipeline – Summary

You have two ingestion options, but the rest of the pipeline is the same:

1. **Ingest raw data into BigQuery** (choose A or B below).
2. Run **dbt** to build the warehouse.
3. Run **data quality** checks.
4. Use the **EDA notebook**.
5. Optionally, run the entire flow via **Prefect** orchestration.

Each step is described below.

---

### 7. Ingestion Option A – Direct Local → BigQuery

From the project root:

```bash
cd ~/olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a

python ingestion/ingest_raw_olist.py
```

What this does:
- Ensures dataset `raw_olist` exists.
- Reads each CSV with `pandas.read_csv`.
- Uses `pandas_gbq.to_gbq` to write tables:
  - `raw_olist.customers`, `orders`, `order_items`, `order_payments`,
    `products`, `sellers`, `geolocation`, `order_reviews`.

Expected output: “Loaded N rows into …” for each table.

---

### 8. Ingestion Option B – Local → GCS → BigQuery (New)

This is the “next version” flow you asked for.

From the project root:

```bash
cd ~/olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a

python gcs_pipeline/upload_and_ingest_raw_olist.py
```

What this does:
- Verifies `DATA_DIR` and `GCS_BUCKET` are set.
- Uploads each CSV to:
  - `gs://$GCS_BUCKET/$GCS_PREFIX/<filename>`
- Uses **BigQuery load jobs** (`load_table_from_uri`) to load:
  - `gs://…/olist_customers_dataset.csv` → `raw_olist.customers`
  - etc.

You’ll see logs for each upload and load, e.g. “Loaded 99,441 rows into …”.

> If you run the orchestrated flow (`python orchestration/flow.py`)
> with `USE_GCS_INGEST=1`, it will call this script automatically.

---

### 9. Build the Warehouse with dbt

Once raw tables exist in `raw_olist`, run dbt:

```bash
cd ~/olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a

cd dbt_olist
dbt deps
dbt run
dbt test
cd ..
```

What this does:
- Creates **staging views** in `dw_stg_olist`.
- Creates **warehouse tables** in `dw_dw`:
  - `dim_customer`, `dim_product`, `dim_seller`, `dim_date`, `fact_order_items`.
- Runs data tests defined in the dbt project.

You can verify datasets in BigQuery:

```bash
bq ls "$BQ_PROJECT:raw_olist"
bq ls "$BQ_PROJECT:dw_stg_olist"
bq ls "$BQ_PROJECT:dw_dw"
```

---

### 10. Data Quality Checks

From the project root:

```bash
cd ~/olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a

python data_quality/ge_raw_order_items.py
```

What this does:
- Pulls `raw_olist.order_items` into a DataFrame using `pandas_gbq`.
- Runs basic checks (no nulls in key columns, no negative prices/freight).
- Optionally uses Great Expectations if `USE_GREAT_EXPECTATIONS=1`.

Expected: “Data quality checks passed.”

---

### 11. Exploratory Analysis & Metrics Notebook

1. Start Jupyter from the project root:

   ```bash
   cd ~/olist-data-pipeline_bigquery
   conda activate olist-bq
   jupyter notebook
   ```

2. In your editor/browser, open:
   - `analysis/eda_and_metrics.ipynb`

3. Ensure the selected kernel is the `olist-bq` environment.

4. Run all cells (or step through them).

The notebook:
- Connects to `dw_dw` using `pandas_gbq` and `BQ_PROJECT`, `BQ_DATASET_DW` from `config.py`.
- Produces:
  - Monthly revenue trend.
  - Top product categories by revenue.
  - Customer segmentation by tenure and CLV.
  - Late delivery rate.

If a query errors with “Not found: Dataset … or table …”, check that **dbt run** has completed and that you’re using the correct project/dataset.

---

### 12. Full Orchestrated Flow (Optional)

You can run the entire pipeline—ingestion, dbt, tests, and data quality—through the Prefect‑backed flow:

#### 12.1 Using direct local ingestion

```bash
cd ~/olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a

unset USE_GCS_INGEST   # ensure it's off
python orchestration/flow.py
```

#### 12.2 Using the GCS ingestion

```bash
cd ~/olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a

export USE_GCS_INGEST=1
python orchestration/flow.py
```

Notes:
- Prefect will start a **temporary local server** on a URL like `http://127.0.0.1:8340` to coordinate the flow.
- You do **not** need to open this URL; it’s just for the Prefect engine.

---

### 13. Troubleshooting (Quick Reference)

- **`Not found: Dataset … dw_dw`**
  - Run `dbt run` and verify with: `bq ls "$BQ_PROJECT:dw_dw"`.
- **Notebook `pandas_gbq` or `config` import errors**
  - Make sure `conda activate olist-bq` and run Jupyter from the project root.
  - First notebook cell adds the project root to `sys.path` (`'..'`), so `config.py` is importable.
- **BigQuery CSV load errors for `olist_order_reviews_dataset.csv`** (GCS ingestion)
  - The reviews file contains quotes and commas in text.
  - Consider:
    - Allowing a higher error threshold via BigQuery load job options (not yet implemented), or
    - Pre‑cleaning that CSV locally before uploading.
- **“Must specify authentication method” in dbt**
  - `profiles.yml` uses `method: oauth`; make sure you ran `gcloud auth application-default login`.
- **Env variables not seen by dbt**
  - Run `set -a && source .env && set +a` in the same shell before `dbt run`.

For a more procedural, step‑by‑step walkthrough, also see `docs/STEP_BY_STEP.md`.

