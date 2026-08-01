# P8 Data-Agent Tool Contract (Stage 7)
Clarivance Analytics Group · P10 provides, P8 consumes

## Contract direction
P10 exposes a read-only querying surface. P8 (data-agent capstone) consumes it.
P8 never modifies the semantic model or the gold tables.

## Tool: query_ingrifoods_metrics
Purpose: answer business questions by evaluating governed measures.

Input:
  measure: string (one of the 8 defined measures)
  filter:  optional { dimension: string, value: string }

Output:
  measure: string
  value:   number
  grounded_from: "sm_clariv_p10"

Allowed measures (from docs/semantic_model.md):
  Total Revenue, Total Orders, Order Lines, Avg Line Value,
  Active Products, Total Deliveries, Delivery Success Rate, Cold Chain Breaches

Allowed filter dimensions:
  dim_depot[region], dim_depot[city], dim_product[category],
  dim_product[temperature_zone], fact_deliveries[status]

## Guardrails
- Read-only: no write, no schema change.
- Bounded measure set: requests outside the 8 measures are rejected.
- Grounded: every answer traces to a measure evaluation, never a raw-table scan.
- Audit: each call logs measure + filter + returned value.

## Why this is safe for an agent
The agent cannot invent metrics — it can only invoke defined measures. The
semantic model is the authority; the agent is a bounded caller. This is the
"tool-based agent with constrained action space" the lifecycle Stage 7 requires.