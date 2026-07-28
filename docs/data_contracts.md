# P10 Data Contract Register — Bronze Source Profiling
Clarivance Analytics Group · Derived from `notebooks/01_bronze_profiling.py`

Every rule below traces to a check in the profiling notebook. Counts are measured, not estimated.

| # | Table | Column | Defect | Rows | Action | Rationale |
|---|-------|--------|--------|------|--------|-----------|
| 1 | products | product_id | Duplicate primary key | 2 | FAIL-CLOSED | Duplicated dimension key fans out every downstream join |
| 2 | products | unit_cost / unit_price | Cost exceeds price | 3 | FAIL-CLOSED | Selling below cost is a data entry error, not a strategy |
| 3 | depots | city | Conformance drift (" leeds", "SOUTHAMPTON") | 2 | CLEANSE | Correct value unambiguous |
| 4 | orders | order_line_id | Duplicate key (76 byte-identical) | 83 | FAIL-CLOSED | Double-load; directly inflates revenue and volume |
| 5 | orders | requested_delivery_date | Null | 211 | WARN | Order remains valid; only SLA metrics unavailable |
| 6 | orders | quantity | Zero or negative | 64 | FAIL-CLOSED | Not a small quantity — not a quantity |
| 7 | orders | depot_id | Orphan FK (D014, D017, D099) | 124 | FAIL-CLOSED | Rows vanish at join; regional totals silently low |
| 8 | orders | unit_price | Disagrees with product master | 1,373 | FAIL-CLOSED + escalate to product master owner | ~1,070 caused by #2. Fix #2 first, re-measure, then gate on the ~300 genuine drifts |
| 9 | orders | customer_id | No parent table in extract | n/a | DOCUMENT | Degenerate dimension; no RI rule possible |
| 10 | deliveries | order_id | Orphan FK | 33 | FAIL-CLOSED | Delivery against a non-existent order |
| 11 | deliveries | status | 9 distinct values collapsing to 4 | 290 | CLEANSE | Trim + upper; every GROUP BY currently splits categories |
| 12 | deliveries | temperature_breach_flag | Null; dtype object not bool | 96 | FAIL-CLOSED + per-row investigation | Null is not false. "Unknown cold chain" must not be read as "cold chain held" |
| 13 | deliveries | delivered_at | Earlier than dispatched_at | 48 | FAIL-CLOSED | Physically impossible |
| 14 | deliveries | distance_km | Negative | 14 | FAIL-CLOSED | Not a distance |
| 15 | deliveries | vehicle_id | No parent table in extract | n/a | DOCUMENT | Degenerate dimension |
| 16 | all | date / timestamp columns | Stored as text | all | CLEANSE | Parse in silver; typed contracts depend on it |

## Notes

**Defects propagate.** Row 8 is largely a symptom of row 2 — three products had prices altered in the master, so ~1,070 historic order lines now disagree with it. Remediation is sequenced: fix the master, re-measure, then gate on the residual. Gating on 7.7% of rows before that fix would produce an escalation volume nobody could process, and an unusable gate gets disabled — which is worse than no gate, because everyone believes it is still running.

**Degenerate dimensions.** `customer_id` and `vehicle_id` have no parent table in this extract. No `dim_customer` or `dim_vehicle` can be built; both keys remain on the fact tables and support counting and grouping but not attribute slicing. This is a documented boundary, not an omission.

**Escalation.** Row 8 stops the pipeline and raises a decision to the product master owner. A gate that halts without notifying anyone is an outage; a gate that halts and routes the decision is a control.
