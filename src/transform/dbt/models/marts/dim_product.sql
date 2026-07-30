{{ config(materialized="table") }}

with active_products as (

    select
        product_id,
        product_name,
        category,
        temperature_zone,
        cast(unit_cost as decimal(10, 2))   as unit_cost,
        cast(unit_price as decimal(10, 2))  as unit_price,
        cast(shelf_life_days as int)        as shelf_life_days,
        cast(1 as bit)                      as is_active
    from {{ source("silver", "silver_products") }}

),

withdrawn_products as (

    select distinct
        product_id,
        product_name,
        category,
        temperature_zone,
        cast(unit_cost as decimal(10, 2))   as unit_cost,
        cast(unit_price as decimal(10, 2))  as unit_price,
        cast(shelf_life_days as int)        as shelf_life_days,
        cast(0 as bit)                      as is_active
    from {{ source("bronze", "bronze_products") }}
    where product_id not in (select product_id from {{ source("silver", "silver_products") }})

)

select * from active_products
union all
select * from withdrawn_products