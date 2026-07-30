select *
from {{ ref("fact_deliveries") }}
where transit_minutes < 0 
OR distance_km < 0