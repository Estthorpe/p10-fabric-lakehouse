{{ config(materialized="table") }}

with depots as (

    select * from {{ source("silver", "silver_depots") }}

)

select
    depot_id,
    depot_name,
    city,
    region,
    capacity_pallets,
    opened_date
from depots