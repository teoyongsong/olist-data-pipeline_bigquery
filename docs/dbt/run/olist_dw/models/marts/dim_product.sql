
  
    

    create or replace table `olistdatapipelinebigquery`.`dw_dw`.`dim_product`
      
    
    

    
    OPTIONS()
    as (
      
with products as (
    select * from `olistdatapipelinebigquery`.`dw_stg_olist`.`stg_products`
)

select
    row_number() over (order by product_id) as product_key,
    product_id,
    product_category_name,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from products
    );
  