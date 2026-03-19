

  create or replace view `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_sellers`
  OPTIONS()
  as with source as (
    select * from `olistdatapipelinebigquery`.`raw_olist`.`sellers`
),

renamed as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    from source
)

select * from renamed;

