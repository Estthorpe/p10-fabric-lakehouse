select *
from {{ ref("fact_orders") }}
where line_value <= 0