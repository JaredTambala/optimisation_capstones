# CAP-001 Whole-Dataset Viability Audit

## Outcome

Audit status: **FAIL** (8 of 10 gates).

The audit used explicit MILP and MINLP formulations only. It retained aggregate evidence and did not create a reference allocation, preferred recommendation or application.

## Owner decision

The frozen package set is **not accepted for WP7**. The controlled reopen is WP6 planning and scenario calibration: every default incumbent uses zero boundary supply, so the source interruption and correlated regional constraints are not proven material.

Regenerate all six complete packages after recalibrating demand, opening stock and affected scenario targets; assign new hashes and obtain renewed owner acceptance before rerunning this audit.

## Fixed-price MILP cases

| Dataset | Service status | Shortage | Economic status | Cost band (EUR) |
|---|---|---:|---|---:|
| BASE | globally_optimal | 0.000 | feasible_time_limited | 3,190,000–3,200,000 |
| SCN-01 | globally_optimal | 0.000 | feasible_time_limited | 3,120,000–3,130,000 |
| SCN-02 | globally_optimal | 0.000 | feasible_time_limited | 3,140,000–3,150,000 |
| SCN-03 | globally_optimal | 0.000 | feasible_time_limited | 3,140,000–3,150,000 |
| SCN-04 | globally_optimal | 0.000 | feasible_time_limited | 3,120,000–3,130,000 |
| SCN-05 | globally_optimal | 0.000 | feasible_time_limited | 3,230,000–3,240,000 |

## Gate results

| Gate | Result | Evidence summary |
|---|---|---|
| G1 — Frozen identity | PASS | six package hashes and identities match the accepted checkpoint |
| G2 — Common explicit MILP formulation | PASS | one builder and two-stage solve path accepted all six packages |
| G3 — Feasibility and service classification | PASS | See machine-readable scorecard |
| G4 — Scenario materiality | FAIL | See machine-readable scorecard |
| G5 — Configuration sensitivity | FAIL | See machine-readable scorecard |
| G6 — Opposed decision trade-off | PASS | See machine-readable scorecard |
| G7 — Recursive-cost MINLP viability | PASS | See machine-readable scorecard |
| G8 — Bounds and accounting | PASS | See machine-readable scorecard |
| G9 — Data-family usefulness | PASS | See machine-readable scorecard |
| G10 — Accessibility and privacy | PASS | See machine-readable scorecard |

## Evidence boundary

Economic stages may be time-limited and are reported as incumbents with solver gaps. Service-stage optimality and physical/accounting reconciliation are checked independently. No global-optimality claim is made for the non-convex recursive formulation.

A cost difference is accepted as material only when the two solver objective intervals are materially disjoint. Aggregate choices from overlapping time-limited incumbents are reported as uncertified differences, not as scenario proof.

No row-level orders, shipments, production, inventory, service allocation, pool values or expected student objective are retained.
