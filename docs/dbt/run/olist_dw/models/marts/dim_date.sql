
  
    

    create or replace table `olistdatapipelinebigquery`.`dw_dw`.`dim_date`
      
    
    

    
    OPTIONS()
    as (
      
with date_spine as (
    select date_day
    from unnest(
        generate_date_array('2016-01-01', '2018-12-31')
    ) as date_day
),

renamed as (
    select
        date_day as date_key,
        date_day,
        extract(year from date_day) as year,
        extract(month from date_day) as month,
        extract(day from date_day) as day_of_month,
        format_date('%B', date_day) as month_name,
        extract(week from date_day) as week_of_year,
        extract(dayofweek from date_day) as day_of_week,
        format_date('%A', date_day) as day_name
    from date_spine
)

select * from renamed
    );
  