with source as (
    select * from {{ source('raw_olist', 'orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        cast(order_purchase_timestamp as timestamp) as order_ts,
        cast(order_approved_at as timestamp) as order_approved_ts,
        cast(order_delivered_carrier_date as timestamp) as shipped_ts,
        cast(order_delivered_customer_date as timestamp) as delivered_ts,
        cast(order_estimated_delivery_date as timestamp) as estimated_delivery_ts,
        order_status
    from source
)

select * from renamed
