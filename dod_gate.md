# P10 — Definition of Done Gate
Clarivance Analytics Group · Fabric Lakehouse (Ingrifoods) · 1 August 2026

## 7-stage lifecycle — all evidenced

| Stage | Requirement | Evidence | Status |
|-------|-------------|----------|--------|
| 1 Template | Reproducible scaffold, CI-ready | Repo scaffold, .gitignore, docs structure, runbook | DONE |
| 2 Ingestion & Contracts | Validated data, contracts in code | Bronze (row-faithful), 12 silver DQ contracts, quarantine-and-gate | DONE |
| 3 Evaluation-as-Tests | Metrics as enforceable gates | dbt build: 6 models, 13 tests; sabotage drill (red->green) | DONE |
| 4 Serving | Model as operational system | Semantic model sm_clariv_p10, 8 measures, verified output | DONE |
| 5 Monitoring | Reliability post-deployment | monitoring.md: quarantine-rate drift signal, incident response | DONE (design) |
| 6 GenAI | LLM augmentation, safely bounded | metric_explainer_design.md: grounded, bounded, versioned prompt | DONE (design) |
| 7 Agentic | Tool-based agent, constrained | p8_tool_contract.md: read-only, bounded measure set, guardrails | DONE (contract) |

## Quality gates

| Gate | Result |
|------|--------|
| dbt build green | PASS=19 (6 models, 13 tests), 0 errors |
| Fail-closed contracts | 12 contracts, 708 rows quarantined (2.98%), under 5% threshold |
| Test-failure demo captured | Sabotage drill: FAIL 16916 then restored to PASS |
| Referential integrity | All FK relationships tested; soft-delete resolved R17 (1058 -> 0) |
| Zero stored credentials | dbt auth via CLI session; no secret in repo |
| Cost | GBP 0 (trial capacity) |

## Deliverables

| Artefact | Location |
|----------|----------|
| Data contract register | docs/data_contracts.md |
| Semantic model spec (P8 grounding) | docs/semantic_model.md |
| Monitoring design | docs/monitoring.md |
| GenAI explainer design | src/explain/metric_explainer_design.md |
| P8 tool contract | src/config/p8_tool_contract.md |
| Analytics layer (3-page dashboard) | reports/ingrifoods_dashboard_mock.html |
| Provisioning runbook | docs/runbook.md |
| Risk log | docs/risk_log.md |
| Learning ledger | docs/learning_ledger.md |
| dbt project (6 models, 13 tests) | src/transform/dbt/ |
| Spark contract notebooks | src/transform/spark/ |
| Data generator | scripts/generate_ingrifoods_data.py |

## Documented deviations (judgement, not gaps)

| Deviation | Reason |
|-----------|--------|
| No Dockerfile / Makefile | Fabric is fully managed; no container to build. Documented, not faked. |
| dbt covers silver->gold only, not full pipeline | Platform fact: Lakehouse SQL endpoint is read-only; dbt must target the Warehouse. |
| 6 models not 10 | Thursday gate (DC2) executed after a lost day; full star schema still delivered. |
| Eventstream bounded to bronze-only | Least-known component on a tight window; deliberate scope boundary. |
| 3-page dashboard not 5 | 5-page standard is for ML projects; pages 4-5 (predictive/prescriptive) not applicable to a data-engineering project and would be fabricated. |
| Live Power BI report descoped | Trial capacity; analytics design captured as HTML mock + governed measures instead. |
| CI-via-OIDC descoped | Local dbt build + sabotage drill is honest evaluation-as-tests evidence. |
| Monitoring/GenAI/agentic as designs | Master Execution Standard asks for designs at this phase, not running systems. |



## Gate decision
All 7 stages evidenced. All quality gates passed. All deviations documented with
rationale. **P10 SIGNED OFF.**