# Semantic Model — sm_clariv_p10
Clarivance Analytics Group · P10 Fabric Lakehouse · Stage 4 (Serving)

## Purpose
Direct Lake semantic model over the gold star schema. Serving layer for P10 and
the grounding surface for the P8 data-agent capstone. P8 consumes this contract;
it never modifies it. Documented here so it survives trial expiry — the live
model is disposable, this specification is durable.

## Source
Direct Lake over Fabric Warehouse wh_clariv_p10 (workspace ws-clariv-p10).
No import, no copy — reads Delta gold tables in OneLake directly.

## Tables
| Table | Grain | Role |
|-------|-------|------|
| fact_orders | one order line | fact |
| fact_deliveries | one delivery | fact |
| dim_depot | one depot | dimension |
| dim_product | one product (incl. soft-deleted) | dimension |

## Relationships
| From | To | Cardinality | Direction |
|------|----|-----------  |-----------|
| fact_orders[depot_id] | dim_depot[depot_id] | many-to-one | single |
| fact_orders[product_id] | dim_product[product_id] | many-to-one | single |
| fact_deliveries[depot_id] | dim_depot[depot_id] | many-to-one | single |

customer_id and vehicle_id are degenerate dimensions (no parent table) and
remain on the facts without relationships.

## Measures
| Measure | DAX | Pattern |
|---------|-----|---------|
| Total Revenue | `SUM(fact_orders[line_value])` | base aggregation |
| Total Orders | `DISTINCTCOUNT(fact_orders[order_id])` | distinct count |
| Order Lines | `COUNTROWS(fact_orders)` | row count |
| Avg Line Value | `DIVIDE([Total Revenue], [Order Lines], 0)` | safe ratio |
| Active Products | `CALCULATE(DISTINCTCOUNT(dim_product[product_id]), dim_product[is_active] = TRUE())` | filtered count |
| Total Deliveries | `COUNTROWS(fact_deliveries)` | row count |
| Delivery Success Rate | `DIVIDE(CALCULATE(COUNTROWS(fact_deliveries), fact_deliveries[status]="DELIVERED"), [Total Deliveries], 0)` | filtered ratio |
| Cold Chain Breaches | `CALCULATE(COUNTROWS(fact_deliveries), fact_deliveries[temperature_breach_flag]=TRUE())` | filtered count |

## Verified output (captured for P8 grounding)
Evaluated 2026-08-01 via DAX query view:

| Measure | Value |
|---------|-------|
| Total Revenue | £6,637,602.71 |
| Total Orders | 5,962 |
| Order Lines | 17,351 |
| Avg Line Value | £382.55 |
| Active Products | 47 |
| Total Deliveries | 5,326 |
| Delivery Success Rate | 0.88 |
| Cold Chain Breaches | 207 |

## Sample question -> measure mapping (P8 grounding)
| Business question | Measure(s) |
|-------------------|-----------|
| "What was total revenue last year?" | Total Revenue |
| "How many active products do we sell?" | Active Products |
| "What share of deliveries succeed?" | Delivery Success Rate |
| "How many cold-chain breaches occurred?" | Cold Chain Breaches |
| "What is the average order line value?" | Avg Line Value |

## Design notes
- Active Products returns 47, not 50: the 3 negative-margin products withdrawn by
  silver contract R2 are retained in dim_product as is_active = false (soft delete)
  for referential integrity, but excluded from active counts. This is the
  quarantine decision made queryable at the serving layer.
- All ratios use DIVIDE (divide-by-zero safe), never the / operator.
- Measures live in the model, never in report visuals, so every consumer —
  report or agent — reads one definition.