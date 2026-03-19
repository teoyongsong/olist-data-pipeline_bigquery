

  create or replace view `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_customers`
  OPTIONS()
  as with source as (
    select * from `olistdatapipelinebigquery`.`raw_olist`.`customers`
),

renamed as (
    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    from source
)

select * from renamed;

