# CAP-001 Whole-Dataset Viability Audit

## Outcome

Audit status: **PASS** (10 of 10 gates).

The audit used explicit MILP and MINLP formulations only. It retained aggregate evidence and did not create a reference allocation, preferred recommendation or application.

## Owner decision

The package set passes the bounded author-side viability audit. This accepts the datasets as sufficiently deep examination inputs; it does not approve an optimiser or expected answer.

No controlled reopen is required.

## Private physical-seed MILP cases

| Dataset | Service status | Shortage | Seed status | Proxy-cost band (EUR) |
|---|---|---:|---|---:|
| BASE | globally_optimal | 0.000 | feasible_time_limited | 610,000–620,000 |
| SCN-01 | globally_optimal | 0.000 | feasible_time_limited | 600,000–610,000 |
| SCN-02 | globally_optimal | 0.000 | feasible_time_limited | 670,000–680,000 |
| SCN-03 | globally_optimal | 0.000 | feasible_time_limited | 580,000–590,000 |
| SCN-04 | globally_optimal | 0.000 | feasible_time_limited | 570,000–580,000 |
| SCN-05 | globally_optimal | 0.000 | feasible_time_limited | 670,000–680,000 |

## Gate results

| Gate | Result | Evidence summary |
|---|---|---|
| G1 — Frozen identity | PASS | six package hashes and identities match the accepted checkpoint |
| G2 — Common explicit MILP formulation | PASS | one builder and two-stage solve path accepted all six packages |
| G3 — Feasibility and service classification | PASS | See machine-readable scorecard |
| G4 — Scenario materiality | PASS | See machine-readable scorecard |
| G5 — Configuration sensitivity | PASS | See machine-readable scorecard |
| G6 — Opposed decision trade-off | PASS | See machine-readable scorecard |
| G7 — Recursive-cost MINLP viability | PASS | See machine-readable scorecard |
| G8 — Bounds and accounting | PASS | See machine-readable scorecard |
| G9 — Data-family usefulness | PASS | See machine-readable scorecard |
| G10 — Accessibility and privacy | PASS | See machine-readable scorecard |

## Evidence boundary

Economic stages may be time-limited and are reported as incumbents with solver gaps. Zero-shortage feasibility, scenario-witness replay and physical/accounting reconciliation are checked independently. No global-optimality claim is made for the bounded decision pairs or the non-convex recursive formulation.

A cost difference is accepted as material only when the two solver objective intervals are materially disjoint. Scenario materiality is otherwise established by independent physical replay of a valid BASE witness against the complete replacement dataset. Bounded incumbent decision pairs may demonstrate an available trade-off, but not that it is uniquely optimal or unavoidable.

No row-level orders, shipments, production, inventory, service allocation, pool values or expected student objective are retained.
