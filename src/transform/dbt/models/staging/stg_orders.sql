{{ config(materialized="view") }}

with source as (

    select * from {{ source("silver", "silver_orders") }}

),

renamed as (

    select
        order_line_id,
        order_id,
        customer_id,
        depot_id,
        product_id,
        cast(order_datetime as datetime2)        as ordered_at,
        cast(requested_delivery_date as date)    as requested_delivery_date,
        cast(quantity as int)                    as quantity,
        cast(unit_price as decimal(10, 2))       as unit_price,
        cast(quantity * unit_price as decimal(12, 2)) as line_value

    from source

)

select * from renamed