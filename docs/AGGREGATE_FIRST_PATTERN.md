# Aggregate First → Then Join

This document describes the pattern used for **order-level** analytics in the Olist pipeline and how to get correct, reproducible numbers.

## Why this pattern

- **order_items** has multiple rows per order (one per line item).
- **order_payments** has multiple rows per order (installments, multiple payment methods).
- If you join `orders` directly to `order_items` or `order_payments` and then aggregate, you can get **join multiplication** and wrong counts/sums (e.g. double-counting payments when an order has many items).

**Rule:** Aggregate each child table **by order_id** first so you have one row per order; then join those aggregates to `orders`. That way there is no duplication.

---

## Implementation in dbt

### Step 1 — Aggregate order items (merchandise value per order)

```sql
item_revenue AS (
    SELECT
        order_id,
        SUM(price) AS item_value,
        SUM(freight_value) AS freight_value,
        SUM(price + freight_value) AS gross_order_value,
        COUNT(*) AS total_items
    FROM order_items
    GROUP BY order_id
)
```

→ One row per order: `item_value`, `freight_value`, `gross_order_value`, `total_items`.

### Step 2 — Aggregate payments

```sql
payment_summary AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value,
        COUNT(payment_sequential) AS payment_count
    FROM order_payments
    GROUP BY order_id
)
```

→ One row per order: `payment_value`, `payment_count`. An order can have multiple payment rows (installments, vouchers).

### Step 3 — Join with orders (safe join)

```sql
final_orders AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_purchase_timestamp,
        ir.item_value,
        ir.freight_value,
        ir.gross_order_value,
        ir.total_items,
        ps.payment_value,
        ps.payment_count
    FROM orders o
    LEFT JOIN item_revenue ir ON o.order_id = ir.order_id
    LEFT JOIN payment_summary ps ON o.order_id = ps.order_id
)
```

Every table has **one row per order** before joining → no duplication.

### Step 4 — Where this lives

- **Staging:** `stg_order_items`, `stg_order_payments`, `stg_orders`.
- **Mart:** `dw_dw.fact_orders` — built exactly with the steps above. All order-level dashboards and ML models should read from `fact_orders` (or from this pattern) for correct totals.

---

## Expected benchmark numbers (approx)

When the pipeline is correct:

| Metric | Expected value |
|--------|----------------|
| Orders | ~99,000 |
| Customers | ~96,000 |
| Order items | ~112,000 |
| Total revenue (gross_order_value) | ~16M BRL |

If you see very different numbers, the most likely causes are:

- Join multiplication (not aggregating before join).
- Counting from the wrong table (e.g. counting rows in order_items instead of distinct orders).
- Not filtering `order_status` when relevant (e.g. only `delivered`).

### Example check query (delivered orders)

```sql
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(gross_order_value) AS total_merchandise_value,
    SUM(payment_value) AS total_payments_received,
    AVG(total_items) AS avg_items_per_order
FROM dw_dw.fact_orders
WHERE order_status = 'delivered';
```

---

## Why this works in both Spark and dbt

The flow is deterministic:

```
RAW
  ↓
AGGREGATE (order_items, order_payments by order_id)
  ↓
JOIN (orders)
  ↓
ANALYTICS (fact_orders)
```

Aggregating first removes differences caused by distributed joins in Spark or query optimizers in the warehouse; the result is one row per order and consistent metrics.
