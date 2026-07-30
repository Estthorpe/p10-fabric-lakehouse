{{ config(materialized="table") }}

with deliveries as (

    select * from {{ ref("stg_deliveries") }}

)

select
    delivery_id,
    order_id,
    depot_id,             -- FK -> dim_depot
    vehicle_id,
    dispatched_at,
    delivered_at,
    status,
    temperature_breach_flag,
    distance_km,
    transit_minutes
from deliveries