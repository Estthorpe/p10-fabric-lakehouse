{{ config(materialized="view") }}

with source as (

    select * from {{ source("silver", "silver_deliveries") }}

),

renamed as (

    select
        delivery_id,
        order_id,
        depot_id,
        vehicle_id,
        cast(dispatched_at as datetime2)         as dispatched_at,
        cast(delivered_at as datetime2)          as delivered_at,
        status,
        temperature_breach_flag,
        cast(distance_km as decimal(10, 2))      as distance_km,
        datediff(minute, dispatched_at, delivered_at) as transit_minutes

    from source

)

select * from renamed