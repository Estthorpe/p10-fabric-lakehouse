{{ config(materialized="table") }}

with products as (

    select * from {{ source("silver", "silver_products") }}

)

select
    product_id,
    product_name,
    category,
    temperature_zone,
    cast(unit_cost as decimal(10, 2))   as unit_cost,
    cast(unit_price as decimal(10, 2))  as unit_price,
    cast(shelf_life_days as int)        as shelf_life_days
from products