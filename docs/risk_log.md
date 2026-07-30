# P10 Risk Log — Fabric Lakehouse (Ingrifoods)
Clarivance Analytics Group · Esther Uzor

## Open risks

| # | Risk | Status | Mitigation |
|---|------|--------|------------|
| R1 | Fabric trial expires ~4 Aug 2026. Workspace and semantic model become inaccessible. | OPEN | Durable P8 contract capture in docs/semantic_model.md (DDL, measures, sample query/response pairs). All logic in git; platform loss costs the running instance, not the IP. |
| R2 | dbt-fabric adapter maturity unproven for this workload. | OPEN | Binding 3-hour friction trigger, then fall back to versioned Warehouse T-SQL + pytest assertions + hand-drawn lineage. |
| R3 | Fabric has no meaningful IaC path; provisioning is manual clicking. | ACCEPTED | Every step recorded as a numbered runbook entry. Runbook doubles as rebuild instructions. |
| R4 | Trial capacity may pause or throttle under Spark load. | OPEN | Modest data volumes; Spark kept small. |

## Discovered — Day 1 (27 July 2026)

| # | Finding | Impact | Action taken |
|---|---------|--------|--------------|
| D1 | Trial had 8 days remaining, not 60. Handover assumption invalid — trial was activated ~52 days before kickoff. | Project window cut from 60 days to 8. | Plan re-verified against the real window; fits with ~1 day margin. |
| D2 | Azure sign-up refused for Enuzor@ingrifoods.onmicrosoft.com — "not eligible to sign up for an Azure account". | Cannot buy F2 capacity on ingrifoods. Trial cannot be extended by purchase. | Abandoned. |
| D3 | Fabric capacities cannot serve workspaces in another tenant. | An estthorpe_20 capacity cannot rescue an ingrifoods workspace. | Migration would mean rebuild, not move. |
| D4 | Fabric trial refused on estthorpe_20 — "A Fabric trial isn't available for your account". Power BI Pro trial granted instead (60 days). | estthorpe_20 not viable as a Fabric host. | Abandoned. |
| D5 | Fabric capacity quota = 0 in UK South on the free-trial subscription. Provider registration succeeded; quota is separate and defaults to zero. | F2 deployment failed with BadRequest. | Abandoned. Echoes P9 lesson: quota is not entitlement. |
| D6 | Azure credit GBP 141.99 on estthorpe_20 expires 8 Aug 2026. | Affects P11, not P10. | PAYG upgrade decision due by 6 Aug. |
| D7 | SSH key passphrase for ~/.ssh/id_rsa unrecoverable. | p9-cloud-native-ml-lifecycle and clarivance-azure-foundation will fail on next push. | P10 switched to HTTPS + gh credential helper. Other repos to be fixed during the break. |

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| DC1 | Eventstream bounded to bronze only — no silver or gold path. | Least-known component on an 8-day window. Deliberate scope boundary, not an omission. |
| DC2 | dbt model count held at 10, with a pre-committed cut. **Thursday 30 July 20:00: if dbt build is not green in CI, drop to 6 models.** | Converts "try harder" into a threshold with a consequence. Fail-closed applied to the schedule. |
| DC3 | No Dockerfile or Makefile, despite the Master Execution Standard requiring both. | Fabric is fully managed; there is no container to build. Documented deviation preferred over an empty file shipped to satisfy a checklist. |
| DC4 | Tenant setting: "Service principals can call Fabric public APIs" enabled; "can create workspaces, connections and deployment pipelines" left disabled. | Least privilege. CI needs to connect and run SQL, not create workspaces. |
| DC5 | DC4 scoped to the entire organisation rather than a security group. | Single-user tenant. A production deployment would scope to a group. |
| DC6 | Two-tenant law retained: Azure on estthorpe_20, Fabric on ingrifoods, no cross-tenant data access. | Migration to a single tenant attempted and refused (D2, D4, D5). |

## Standing habit added to the Master Execution Standard

**H5 — Verify the platform window at kickoff.** Before any phase begins, record the platform's expiry date, quota limits, and eligibility terms in the risk log. Registration is not entitlement; a granted trial is not a fresh trial. Bought by D1.



Risk log, one line: DC2 executed — model count cut 10 → 6 at the Thursday gate; full star schema still delivered, DoD intact.