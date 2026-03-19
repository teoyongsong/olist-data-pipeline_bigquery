
  
    

    create or replace table `olistdatapipelinebigquery`.`dw_dw`.`fact_order_items`
      
    
    

    
    OPTIONS()
    as (
      
with oi as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_order_items`
),

orders as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_orders`
),

customers as (
    select * from `olistdatapipelinebigquery`.`dw_dw`.`dim_customer`
),

products as (
    select * from `olistdatapipelinebigquery`.`dw_dw`.`dim_product`
),

sellers as (
    select * from `olistdatapipelinebigquery`.`dw_dw`.`dim_seller`
),

joined as (
    select
        oi.order_id,
        oi.order_item_id,
        c.customer_key,
        p.product_key,
        s.seller_key,
        date(orders.order_ts) as order_date_key,
        date(orders.delivered_ts) as delivery_date_key,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value) as total_item_value,
        case
            when orders.delivered_ts is not null
                 and orders.estimated_delivery_ts is not null
                 and date(orders.delivered_ts) > date(orders.estimated_delivery_ts)
            then true
            else false
        end as is_late_delivery,
        case
            when date(orders.order_ts) = c.first_order_date then true
            else false
        end as is_first_order
    from oi
    join orders on orders.order_id = oi.order_id
    join customers c on c.customer_id = orders.customer_id
    left join products p on p.product_id = oi.product_id
    left join sellers s on s.seller_id = oi.seller_id
)

select
    row_number() over (order by order_id, order_item_id) as order_item_key,
    *
from joined
    );
  