
  
    

    create or replace table `olistdatapipelinebigquery`.`dw_dw`.`dim_customer`
      
    
    

    
    OPTIONS()
    as (
      
with customers as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_customers`
),

orders as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_orders`
),

order_items as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_order_items`
),

order_revenue as (
    select
        o.order_id,
        o.customer_id,
        sum(oi.price + oi.freight_value) as order_revenue
    from orders o
    join order_items oi on oi.order_id = o.order_id
    group by 1, 2
),

last_order as (
    select
        max(date(order_ts)) as max_order_date
    from orders o
),

agg as (
    select
        c.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        min(date(o.order_ts)) as first_order_date,
        max(date(o.order_ts)) as last_order_date,
        count(distinct o.order_id) as total_orders,
        coalesce(sum(r.order_revenue), 0) as total_revenue
    from customers c
    left join orders o on o.customer_id = c.customer_id
    left join order_revenue r on r.order_id = o.order_id
    group by 1, 2, 3, 4
)

select
    row_number() over (order by customer_id) as customer_key,
    customer_id,
    customer_unique_id,
    customer_city,
    customer_state,
    first_order_date,
    last_order_date,
    total_orders,
    round(cast(total_revenue as numeric), 2) as total_revenue,
    round(cast(total_revenue as numeric), 2) as customer_lifetime_value,
    case
        when first_order_date is null then 'No orders'
        when first_order_date >= date_sub(max_order_date, interval 3 month) then 'New'
        when first_order_date >= date_sub(max_order_date, interval 12 month) then 'Established'
        else 'Loyal'
    end as tenure_segment
from agg
cross join last_order
    );
  