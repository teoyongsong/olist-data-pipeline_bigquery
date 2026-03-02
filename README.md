# Olist E-Commerce Data Pipeline (BigQuery)

Same pipeline as the PostgreSQL version, but **CSVs are uploaded to Google BigQuery** and the star schema is built in BigQuery using dbt-bigquery.

**→ [Step-by-step process to complete the project](docs/STEP_BY_STEP.md)**

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
│   └── flow.py
└── docs/
    └── schema.md
```

## Schema

- **Raw:** dataset `raw_olist` (tables: customers, orders, order_items, products, sellers, etc.)
- **Staging:** dataset `dw_stg_olist` (views)
- **Marts:** dataset `dw_dw` (dim_customer, dim_product, dim_seller, dim_date, fact_order_items)

See `docs/schema.md` for details.
