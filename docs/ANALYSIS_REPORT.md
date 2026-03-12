## Olist E-Commerce – Analysis Report (BigQuery)

This report summarizes the key findings from the Olist data pipeline and EDA notebook, using the `dw_dw` star schema in BigQuery.

---

### 1. Business context

Olist is a Brazilian e-commerce platform that connects merchants to multiple marketplaces. The goal of this project is to:

- Build a reliable BigQuery warehouse from the Kaggle Olist dataset.
- Expose three core business metrics:
  1. Monthly sales trends.
  2. Top product categories by revenue.
  3. Customer segmentation & CLV, plus late delivery performance.

All metrics are computed from the `dw_dw` dataset, populated via dbt.

---

### 2. Metric 1 – Monthly sales trends

- **Definition**
  - Monthly total revenue (`SUM(total_item_value)`).
  - Number of orders and number of items sold.
  - Data source: `dw_dw.fact_order_items` with `order_date_key` truncated to month.

- **Observations**
  - Revenue starts very low in late 2016, then ramps up sharply in 2017.
  - There is a clear peak in mid-to-late 2017, followed by sustained high volume into 2018.
  - Seasonal patterns are visible:
    - Noticeable lift in Q4 months, consistent with holiday shopping.
    - Some dips in early-year months.

- **Implications**
  - Growth trajectory suggests a scaling marketplace with increasing order volumes.
  - Capacity planning (customer service, logistics, infrastructure) should align with seasonal spikes.

---

### 3. Metric 2 – Top product categories by revenue

- **Definition**
  - Revenue by product category:
    - `SUM(total_item_value)` grouped by `product_category_name`.
  - Data source: `dw_dw.fact_order_items` joined to `dw_dw.dim_product`.
  - Top 15 categories by total revenue.

- **Top categories (example from notebook output)**
  - `beleza_saude` (Beauty & Health)
  - `relogios_presentes` (Watches & Gifts)
  - `cama_mesa_banho` (Bedding & Bath)
  - `esporte_lazer` (Sports & Leisure)
  - Others: `informatica_acessorios`, `moveis_decoracao`, `utilidades_domesticas`, etc.

- **Observations**
  - Revenue is not dominated by a single category; several verticals contribute meaningfully.
  - Beauty/health, gifting, and home goods are consistently strong performers.
  - Long tails exist (many smaller categories with modest revenue).

- **Implications**
  - Category management teams should prioritize high-revenue segments for:
    - Promotion.
    - Inventory and assortment optimization.
    - Partner acquisition and retention strategies.

---

### 4. Metric 3 – Customer segmentation & CLV

- **Definition**
  - Customer segments calculated in `dw_dw.dim_customer`:
    - `New`: first-time buyers with shorter tenure.
    - `Loyal`: returning customers with mid-to-long tenure.
    - `Established`: oldest/highest-tenure customers.
  - For each segment:
    - Number of customers.
    - Total revenue.
    - Average revenue per customer (CLV proxy).

- **Example from notebook output**
  - Established:
    - ~59k customers.
    - ~9.4M in total revenue.
    - ≈ R$159 per customer.
  - Loyal:
    - ~30k customers.
    - ~4.8M in total revenue.
    - ≈ R$160 per customer.
  - New:
    - ~10k customers.
    - ~1.6M in total revenue.
    - ≈ R$158 per customer.

- **Observations**
  - Average revenue per customer is remarkably stable across segments, despite different tenures.
  - Established and Loyal segments drive the majority of revenue.
  - New customers represent growth potential but are a smaller share of current revenue.

- **Implications**
  - Retention and engagement programs for Established/Loyal customers are critical to sustaining revenue.
  - Onboarding flows, cross-sell/upsell campaigns, and category discovery can help increase CLV for New customers.

---

### 5. Metric 3b – Late delivery performance

- **Definition**
  - Late delivery rate by item:
    - `items` where `is_late_delivery = True` vs. all delivered items.
  - Data source: `dw_dw.fact_order_items` filtered to `delivery_date_key IS NOT NULL`.

- **Example from notebook output**
  - Overall late delivery rate (by items): **~6.6%**.
  - Revenue from late deliveries:
    - ~R$1.15M out of ~R$15.36M total delivered revenue.

- **Observations**
  - The majority of items are delivered on time, but a non-trivial minority (~6–7%) are late.
  - Late deliveries still represent significant revenue (and customer impact).

- **Implications**
  - Late deliveries are a known driver of lower review scores and churn.
  - Improvement levers:
    - SLA monitoring and vendor/carrier scorecards.
    - Proactive notifications and compensation policies.
    - Routing and warehouse optimization for high-late-rate SKUs or regions.

---

### 6. Data quality and reliability

- `data_quality/ge_raw_order_items.py` confirms:
  - No nulls in key identifiers (`order_id`, `order_item_id`, `product_id`, `seller_id`).
  - No negative prices or freight values.
  - Optional Great Expectations suite can formalize and persist expectations.
- dbt tests:
  - Validate relationships between facts and dims.
  - Check for uniqueness, non-null constraints, and conformance to modeling assumptions.

Combined, these checks increase confidence that the metrics above are computed on clean, consistent data.

---

### 7. Summary

- The pipeline successfully:
  - Ingests raw Olist CSVs from Kaggle into BigQuery.
  - Builds a star-schema warehouse with dbt.
  - Enforces data quality constraints.
  - Exposes three core business metrics plus late delivery performance via a reproducible notebook.

- Business takeaways:
  - **Growth**: Strong and increasing monthly revenue, with visible seasonality.
  - **Category mix**: Beauty, gifting, and home goods are top revenue drivers.
  - **Customers**: Established and Loyal customers generate the bulk of revenue; CLV is stable across segments.
  - **Operations**: Late delivery rate (~6.6% of items) is an important operational KPI with meaningful revenue impact.

This report, together with the EDA notebook, can be used as a starting point for deeper analyses (geography, payment methods, cohort behavior, etc.) building on the same BigQuery warehouse.

