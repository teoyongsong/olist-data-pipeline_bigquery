# Olist E-Commerce Data Pipeline (BigQuery)

Same pipeline as the PostgreSQL version, but **CSVs are uploaded to Google BigQuery** and the star schema is built in BigQuery using dbt-bigquery.

**→ [Step-by-step process](docs/STEP_BY_STEP.md)**  
**→ [Architecture overview](docs/ARCHITECTURE.md)**  
**→ [User manual](docs/USER_MANUAL.md)**  
**→ [Analysis report](docs/ANALYSIS_REPORT.md)**  
**→ [Slide deck outline](docs/SLIDES_OUTLINE.md)**

## Prerequisites

- Python 3.10+
- Google Cloud project with BigQuery enabled
- Authentication: `gcloud auth application-default login` or a service account JSON in `GOOGLE_APPLICATION_CREDENTIALS`
- [dbt-core](https://docs.getdbt.com/docs/get-started/installation) with **dbt-bigquery**: `pip install dbt-bigquery`

## Quick Start

### 1. Install

**Option A – Conda (recommended)**

```bash
cd olist-data-pipeline_bigquery
conda env create -f environment.yml
conda activate olist-bq
```

**Option B – venv**

```bash
cd olist-data-pipeline_bigquery
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
pip install dbt-bigquery
```

### 2. Configure

Copy `.env.example` to `.env` and set:

- `BQ_PROJECT` = your GCP project ID
- `DATA_DIR` = path to folder containing Olist CSV files (e.g. `./data/olist`)

### 3. Download data

Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle and extract CSVs into `data/olist/`.

### 4. Run the pipeline

```bash
# Option A: Direct upload from local disk -> BigQuery raw_olist
python ingestion/ingest_raw_olist.py

# Option B (next version): Upload CSVs to GCS, then ingest into BigQuery
# 1) Set GCS_BUCKET (and optionally GCS_PREFIX) in .env
# 2) Run:
python gcs_pipeline/upload_and_ingest_raw_olist.py

# dbt: install packages, build staging + marts, run tests
cd dbt_olist && dbt deps && dbt run && dbt test && cd ..

# Data quality on raw order_items
python data_quality/ge_raw_order_items.py
```

### 5. Analysis

Open `analysis/eda_and_metrics.ipynb` and run all cells (uses `pandas_gbq` and config `BQ_PROJECT`, `BQ_DATASET_DW`).

### 6. Optional: full pipeline in one go

```bash
python orchestration/flow.py
```

### 7. Run the pipeline with Dagster

From the project root, with `.env` loaded:

```bash
cd olist-data-pipeline_bigquery
conda activate olist-bq
set -a && source .env && set +a
```

**Option A – Dagster UI (recommended)**  
Start the Dagster process and open the UI; then run the job from the UI:

```bash
dagster dev -f orchestration/dagster_olist/definitions.py
```

In the UI, open **Jobs** → **olist_elt_job** → **Launch run**.

**Option B – Run job from CLI**

- Local ingestion (default):

  ```bash
  dagster job execute -f orchestration/dagster_olist/definitions.py -j olist_elt_job
  ```

- GCS ingestion:

  ```bash
  USE_GCS_INGEST=1 dagster job execute -f orchestration/dagster_olist/definitions.py -j olist_elt_job
  ```

The Dagster job runs: **ingest** → **dbt run** → **dbt test** → **data_quality**. Ingestion uses `ingestion/ingest_raw_olist.py` unless `USE_GCS_INGEST=1`, in which case it uses `gcs_pipeline/upload_and_ingest_raw_olist.py`.

## Project structure

```
olist-data-pipeline_bigquery/
├── config.py              # BQ_PROJECT, BQ_DATASET_RAW, BQ_DATASET_DW, DATA_DIR
├── requirements.txt
├── .env.example
├── ingestion/
│   └── ingest_raw_olist.py # Load CSVs into BigQuery raw_olist
├── dbt_olist/              # dbt BigQuery project
│   ├── dbt_project.yml
│   ├── profiles.yml        # uses BQ_PROJECT
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/
│   │   └── marts/
│   └── packages.yml
├── data_quality/
│   └── ge_raw_order_items.py
├── analysis/
│   └── eda_and_metrics.ipynb
├── orchestration/
│   ├── flow.py
│   ├── dagster_olist/
│   │   └── definitions.py   # Dagster job: ingest → dbt → data_quality
│   ├── ingest_local_from_kaggle.sh
│   └── ingest_gcs_from_kaggle.sh
└── docs/
    ├── schema.md
    ├── ARCHITECTURE.md
    ├── USER_MANUAL.md
    ├── STEP_BY_STEP.md
    ├── ANALYSIS_REPORT.md
    └── SLIDES_OUTLINE.md
```

## Schema

- **Raw:** dataset `raw_olist` (tables: customers, orders, order_items, products, sellers, etc.)
- **Staging:** dataset `dw_stg_olist` (views)
- **Marts:** dataset `dw_dw` (dim_customer, dim_product, dim_seller, dim_date, fact_order_items)

See `docs/schema.md` for details.
