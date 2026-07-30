{{ config(materialized="table") }}

with orders as (

    select * from {{ ref("stg_orders") }}

)

select
    order_line_id,
    order_id,
    customer_id,          -- degenerate dimension (no parent table)
    depot_id,             -- FK -> dim_depot
    product_id,           -- FK -> dim_product
    ordered_at,
    requested_delivery_date,
    quantity,
    unit_price,
    line_value
from orders