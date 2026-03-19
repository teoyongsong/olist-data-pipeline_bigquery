
  
    

    create or replace table `olistdatapipelinebigquery`.`dw_dw`.`dim_seller`
      
    
    

    
    OPTIONS()
    as (
      
with sellers as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_sellers`
)

select
    row_number() over (order by seller_id) as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
from sellers
    );
  