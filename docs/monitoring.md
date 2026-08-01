# Monitoring & Observability Design — P10
Clarivance Analytics Group · Stage 5

## Principle
Capture live via exports; design offline so evidence survives teardown. The
monitoring *design* is the deliverable — a running Grafana stack is out of scope
for a managed lakehouse on trial capacity.

## What is monitored

### 1. Pipeline health (refresh)
| Signal | Source | Threshold | Action |
|--------|--------|-----------|--------|
| Bronze ingest row count | notebook log | must equal source file count | fail-closed; halt |
| Silver quarantine rate | enforce() gate | > 5% of ingested rows | fail-closed; halt + alert |
| dbt build result | CI / dbt exit code | any test failure | block promotion |
| Warehouse refresh latency | Fabric monitor | > 30 min | warn |

### 2. Data drift (the quarantine rate IS the drift signal)
The silver gate already computes quarantine rate per run. A rising rate over
successive loads is the drift indicator — no separate drift module needed. A
load that suddenly quarantines 8% when the baseline is 3% signals upstream
schema or quality change.

| Metric | Baseline | Drift alert |
|--------|----------|-------------|
| Quarantine rate | 2.98% | > 5.0% (hard gate) or +2pp over 7-day mean (soft) |
| Contract R7 orphan depots | 123 | any material increase = new depot not in dim |
| Cold-chain breach rate | ~4% | > 6% = investigate refrigeration fleet |

### 3. Retraining / refresh trigger logic
P10 has no ML model, so "retraining" maps to **dimension refresh**: when
dim_product or dim_depot gains members, the soft-delete recovery query and the
semantic model must re-run. Trigger: source master-data change detected at bronze.

## Incident response
1. Gate fails -> pipeline halts, nothing reaches gold (fail-closed)
2. Quarantine table (quarantine_silver) holds the offending rows with _dq_rule / _dq_reason
3. Triage from quarantine_silver: which rule, how many, systemic or one-off
4. Fix source or adjust contract; re-run; confirm gate green
5. Log incident in risk_log.md

## Observability split (from Master Execution Standard)
- Operational/real-time plane: Fabric pipeline monitor (native)
- Executive/scheduled plane: the analytics dashboard (reports/)