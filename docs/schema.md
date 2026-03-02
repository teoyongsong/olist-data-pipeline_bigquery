# BigQuery Schema Reference

Datasets and tables used in this project. Raw data is loaded into **`raw_olist`**; dbt builds staging in **`dw_stg_olist`** and marts in **`dw_dw`**.

---

## 1. Raw — `raw_olist`

Loaded from CSV by `ingestion/ingest_raw_olist.py`. One table per Kaggle CSV.

| Table         | Source CSV                     |
|---------------|--------------------------------|
| customers     | olist_customers_dataset.csv   |
| orders        | olist_orders_dataset.csv      |
| order_items   | olist_order_items_dataset.csv |
| order_payments| olist_order_payments_dataset.csv |
| products      | olist_products_dataset.csv    |
| sellers       | olist_sellers_dataset.csv     |
| geolocation   | olist_geolocation_dataset.csv |
| order_reviews | olist_order_reviews_dataset.csv |

---

## 2. Staging — `dw_stg_olist`

Views: stg_customers, stg_orders, stg_order_items, stg_products, stg_sellers (same column logic as PostgreSQL version).

---

## 3. Data warehouse — `dw_dw`

| Table             | Type   | Description |
|-------------------|--------|-------------|
| dim_customer      | Table  | Customer key, attributes, tenure_segment, total_revenue |
| dim_product       | Table  | Product key, category, dimensions |
| dim_seller        | Table  | Seller key, location |
| dim_date          | Table  | Date spine 2016-01-01 to 2018-12-31 |
| fact_order_items  | Table  | Order item grain; FKs to dims; total_item_value, is_late_delivery, is_first_order |

**Fully qualified names:** `{BQ_PROJECT}.{BQ_DATASET_DW}.fact_order_items` etc.
