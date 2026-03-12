## Olist BigQuery Data Pipeline – Slide Deck Outline (10 slides)

This markdown outlines a 10-slide deck you can turn into PowerPoint, Google Slides, or Keynote.

---

### Slide 1 – Title & team

- **Title**: Olist E‑Commerce Data Pipeline on BigQuery
- **Subtitle**: From raw Kaggle CSVs to analytics-ready warehouse
- **Bullets**:
  - Names of team members / roles.
  - Date and context (course, project, client, etc.).

---

### Slide 2 – Business problem

- **Goal**:
  - Centralize Olist e-commerce data in BigQuery.
  - Provide trusted metrics for growth, category performance, and customer behavior.
- **Questions**:
  - How are sales evolving over time?
  - Which product categories drive revenue?
  - How valuable are our customers, and how reliable is delivery?

---

### Slide 3 – Dataset & scope

- **Source**:
  - Kaggle: Brazilian E-Commerce Public Dataset by Olist.
- **Tables**:
  - Customers, orders, order_items, payments, products, sellers, geolocation, reviews.
- **Scope**:
  - Build `raw_olist`, `dw_stg_olist`, `dw_dw` in BigQuery.
  - Expose three core metrics and late delivery KPIs.

---

### Slide 4 – Architecture overview

- **Diagram** (based on `docs/ARCHITECTURE.md`):
  - Kaggle → local `data/olist` → optional GCS → BigQuery `raw_olist` → dbt → `dw_dw`.
  - Orchestration: Prefect flow and Dagster job `olist_elt_job`.
  - Consumption: EDA notebook in `analysis/eda_and_metrics.ipynb`.

---

### Slide 5 – Ingestion design (local & GCS)

- **Local ingestion**:
  - `ingestion/ingest_raw_olist.py` with `pandas_gbq.to_gbq`.
- **GCS ingestion**:
  - `gcs_pipeline/upload_and_ingest_raw_olist.py`:
    - Uploads CSVs to `gs://$GCS_BUCKET/$GCS_PREFIX/…`.
    - Uses BigQuery load jobs with `allow_quoted_newlines`.
- **Kaggle helpers**:
  - `ingest_local_from_kaggle.sh` and `ingest_gcs_from_kaggle.sh`.

---

### Slide 6 – Warehouse & dbt

- **Datasets**:
  - `raw_olist` → `dw_stg_olist` (staging views) → `dw_dw` (star schema).
- **dbt project**:
  - Models in `dbt_olist/models/`.
  - Tests: relationships, uniqueness, not-null.
- **Schema**:
  - Facts: `fact_order_items`.
  - Dimensions: `dim_customer`, `dim_product`, `dim_seller`, `dim_date`.

---

### Slide 7 – Data quality & orchestration

- **Data quality**:
  - `data_quality/ge_raw_order_items.py`:
    - Pandas checks for nulls and negative values.
    - Optional Great Expectations suite.
- **Orchestration**:
  - `orchestration/flow.py` (Prefect).
  - `orchestration/dagster_olist/definitions.py` (Dagster `olist_elt_job`).
  - `USE_GCS_INGEST` flag to toggle ingestion method.

---

### Slide 8 – Metric 1 & 2 (trends & categories)

- **Monthly sales trends**:
  - Monthly revenue, orders, and items sold.
  - Plots from `eda_and_metrics.ipynb`.
- **Top categories**:
  - Top 15 categories by revenue.
  - Highlight: beauty & health, watches & gifts, home goods.

---

### Slide 9 – Metric 3 & late delivery

- **Customer segmentation & CLV**:
  - Segments: New, Loyal, Established.
  - Similar average revenue per customer (~R$158–160).
- **Late delivery**:
  - Late delivery rate ≈ 6.6% of items.
  - Business impact on satisfaction and reviews.

---

### Slide 10 – Results, lessons, next steps

- **Results**:
  - End-to-end pipeline in BigQuery with dbt, quality checks, and orchestration.
  - Three core metrics + late delivery KPI available via notebook.
- **Lessons learned**:
  - Handling CSV quirks (quoted newlines in reviews).
  - Aligning dbt dataset names (`dw_dw`) with config.
- **Next steps**:
  - Add dashboards (Looker Studio / Power BI).
  - Build more metrics (NPS, delivery time distributions, cohorts).
  - Enhance monitoring and alerting for the Dagster job.

