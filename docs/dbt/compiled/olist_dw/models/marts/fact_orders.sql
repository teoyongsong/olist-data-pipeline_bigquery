
-- Aggregate first → then join (one row per order; prevents join multiplication).
-- Step 1: Aggregate order items (true merchandise value per order).
with item_revenue as (
    select
        order_id,
        sum(price) as item_value,
        sum(freight_value) as freight_value,
        sum(price + freight_value) as gross_order_value,
        count(*) as total_items
    from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_order_items`
    group by order_id
),

-- Step 2: Aggregate payments (an order can have multiple payment rows).
payment_summary as (
    select
        order_id,
        sum(payment_value) as payment_value,
        count(payment_sequential) as payment_count
    from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_order_payments`
    group by order_id
),

-- Step 3: Join with orders (safe: every table has one row per order).
orders as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_orders`
),

final_orders as (
    select
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_ts as order_purchase_timestamp,
        date(o.order_ts) as order_date_key,

        ir.item_value,
        ir.freight_value,
        ir.gross_order_value,
        ir.total_items,

        ps.payment_value,
        ps.payment_count
    from orders o
    left join item_revenue ir on ir.order_id = o.order_id
    left join payment_summary ps on ps.order_id = o.order_id
)

select * from final_orders