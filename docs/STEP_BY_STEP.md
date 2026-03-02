# Step-by-Step: Complete the Olist BigQuery Pipeline

Follow these steps in order to run the full project from scratch.

---

## Step 1: Prerequisites

Before starting, ensure you have:

| Requirement | How to check |
|-------------|----------------|
| **Python 3.10+** | `python --version` |
| **Conda** (recommended) or **pip/venv** | `conda --version` or `pip --version` |
| **Google Cloud account** | [console.cloud.google.com](https://console.cloud.google.com) |
| **GCP project with BigQuery enabled** | In GCP Console: APIs & Services → enable BigQuery API |
| **Kaggle account** (for dataset) | [kaggle.com](https://www.kaggle.com) |

---

## Step 2: Clone / open the project

```bash
cd /path/to/olist-data-pipeline_bigquery
```

Use the directory where this project lives (e.g. your workspace path).

---

## Step 3: Create and activate the conda environment

```bash
conda env create -f environment.yml
conda activate olist-bq
```

**Verify:** From the project root, run:

```bash
python -c "from config import BQ_PROJECT; print('OK:', BQ_PROJECT)"
```

You should see something like `OK: olistdatapipelinebigquery` (or your project ID from `.env` if it exists).

---

## Step 4: Configure environment variables

1. Copy the example env file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set at least:

   | Variable | Description | Example |
   |----------|-------------|---------|
   | `BQ_PROJECT` | Your GCP project ID | `my-gcp-project-id` |
   | `DATA_DIR` | Path to folder with Olist CSVs | `./data/olist` |

   Optional: `GOOGLE_APPLICATION_CREDENTIALS` if using a service account JSON instead of `gcloud auth`.

3. **Verify:** From project root:

   ```bash
   python -c "from config import BQ_PROJECT, DATA_DIR; print(BQ_PROJECT, DATA_DIR)"
   ```

---

## Step 5: Authenticate with Google Cloud

Choose one:

**Option A – Application Default Credentials (good for local dev)**

```bash
gcloud auth application-default login
```

**Option B – Service account**

1. Create a service account in GCP with BigQuery permissions.
2. Download the JSON key.
3. In `.env`, set:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json
   ```

**Verify:** List a BigQuery dataset (use your project ID):

```bash
bq ls --project_id=YOUR_BQ_PROJECT
```

---

## Step 6: Download the Olist dataset

1. Go to [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle.
2. Click **Download** (you may need to accept rules and have Kaggle CLI or browser download).
3. Unzip the archive and place the CSV files in `data/olist/` so that you have paths like:

   ```
   data/olist/olist_customers_dataset.csv
   data/olist/olist_orders_dataset.csv
   data/olist/olist_order_items_dataset.csv
   data/olist/olist_order_payments_dataset.csv
   data/olist/olist_products_dataset.csv
   data/olist/olist_sellers_dataset.csv
   data/olist/olist_geolocation_dataset.csv
   data/olist/olist_order_reviews_dataset.csv
   data/olist/product_category_name_translation.csv
   ```

**Verify:**

```bash
ls data/olist/*.csv
```

You should see the files listed above (or at least the ones used by the pipeline).

---

## Step 7: Ingest raw data into BigQuery

You have **two options** for ingestion:

### Option A: Direct upload from local disk (current behavior)

From the **project root** (with `olist-bq` activated and `.env` set):

```bash
python ingestion/ingest_raw_olist.py
```

**Expected:** Messages like “Loaded N rows into …” for each CSV. The script creates the `raw_olist` dataset if it does not exist.

**If it fails:** Check `BQ_PROJECT`, `DATA_DIR`, and GCP auth (Step 5).

### Option B: Upload to GCS, then ingest into BigQuery (next version)

1. In `.env`, set:

   ```bash
   GCS_BUCKET=your-gcs-bucket-name   # must already exist in GCP
   GCS_PREFIX=olist_raw              # or any prefix you prefer
   ```

2. From the **project root**:

   ```bash
   python gcs_pipeline/upload_and_ingest_raw_olist.py
   ```

   This will:
   - Upload CSVs from `DATA_DIR` to `gs://$GCS_BUCKET/$GCS_PREFIX/…`
   - Use BigQuery load jobs to create/replace tables in `raw_olist`.

3. **Optional:** To have the orchestrated flow use the GCS-based ingestion, set:

   ```bash
   export USE_GCS_INGEST=1
   ```

   Then later, when you run:

   ```bash
   python orchestration/flow.py
   ```

   it will call the GCS-based ingestion script instead of the direct one.

---

## Step 8: Install dbt dependencies and run dbt

1. Go to the dbt project:

   ```bash
   cd dbt_olist
   ```

2. Install dbt packages:

   ```bash
   dbt deps
   ```

3. Build staging and marts (views and tables):

   ```bash
   dbt run
   ```

4. Run dbt tests:

   ```bash
   dbt test
   ```

5. Return to project root:

   ```bash
   cd ..
   ```

**Expected:** `dbt run` builds models in `dw_stg_olist` and `dw_dw`. `dbt test` should pass.

**If it fails:** Ensure `BQ_PROJECT` is set (e.g. in `.env`) so `profiles.yml` can read it. Check BigQuery for datasets `raw_olist`, `dw_stg_olist`, `dw_dw`.

---

## Step 9: Run data quality checks

From the **project root**:

```bash
python data_quality/ge_raw_order_items.py
```

**Expected:** “Data quality checks passed.”

Optional: run with Great Expectations by setting:

```bash
USE_GREAT_EXPECTATIONS=1 python data_quality/ge_raw_order_items.py
```

---

## Step 10: Run the analysis notebook

1. Start Jupyter from the project root (so `config` can be imported):

   ```bash
   jupyter notebook
   ```

   Or in VS Code / Cursor: open `analysis/eda_and_metrics.ipynb` and ensure the kernel uses the `olist-bq` conda environment.

2. Open `analysis/eda_and_metrics.ipynb` and run all cells (Cell → Run All, or run cell by cell).

**Expected:** Plots and tables for monthly revenue, top categories, customer segments, and late delivery rate. No import or `pandas_gbq` errors if the env and `.env` are correct.

**If the kernel can’t find `config`:** Run the notebook from the project root directory, or run the first cell (which does `sys.path.insert(0, '..')`) so that `config` is on `sys.path`.

---

## Step 11 (Optional): Run the full pipeline in one go

From the **project root**:

```bash
python orchestration/flow.py
```

This runs, in order: **ingest → dbt run → dbt test → data quality**. Use this after you’ve already completed Steps 7–9 at least once and want to re-run the whole pipeline.

**Optional – run via shell script (e.g. cron):**

```bash
chmod +x orchestration/run_pipeline.sh
./orchestration/run_pipeline.sh
```

Logs go to `logs/pipeline.log`.

---

## Quick reference: order of steps

| Step | Action |
|------|--------|
| 1 | Prerequisites (Python, GCP, Kaggle) |
| 2 | Open project directory |
| 3 | `conda env create -f environment.yml` → `conda activate olist-bq` |
| 4 | `cp .env.example .env` and set `BQ_PROJECT`, `DATA_DIR` |
| 5 | `gcloud auth application-default login` (or service account) |
| 6 | Download Olist CSV from Kaggle → extract into `data/olist/` |
| 7 | `python ingestion/ingest_raw_olist.py` |
| 8 | `cd dbt_olist` → `dbt deps` → `dbt run` → `dbt test` → `cd ..` |
| 9 | `python data_quality/ge_raw_order_items.py` |
| 10 | Open and run `analysis/eda_and_metrics.ipynb` |
| 11 | (Optional) `python orchestration/flow.py` |

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `ModuleNotFoundError: config` | Run scripts and Jupyter from **project root**; notebook first cell has `sys.path.insert(0, '..')`. |
| `No module named 'pandas_gbq'` | Activate the correct env: `conda activate olist-bq` and ensure `environment.yml` was used. |
| BigQuery permission / 403 | GCP auth (Step 5); ensure BigQuery API is enabled and the project in `.env` is correct. |
| `DATA_DIR not found` | Set `DATA_DIR` in `.env` and ensure CSVs are in that folder (Step 6). |
| dbt “project not found” or profile error | Run dbt from `dbt_olist/` and ensure `BQ_PROJECT` is set in the environment (e.g. from `.env`). |

For schema details, see `docs/schema.md`.
