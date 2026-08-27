# CAP-001 Planning and Dataset-Package Implementation Report

## Decision state

| Field | Value |
|---|---|
| Implementation state | Accepted recalibrated checkpoint; WP7 passed 10/10 gates |
| Owner state | Recalibrated package set accepted as the whole-dataset audit input |
| Date | 25 August 2026 |
| Configuration | `CAP-001-DECISION-CONFIG` v0.3.1 |
| Planning seed | `9042027` |
| Governing design | `docs/PLANNING_AND_SCENARIO_DESIGN_CONTRACT.md` |
| Scenario decision | ADR-008, recalibrated on 25 August 2026 |

The accepted package set supplies the temporal and scenario data needed to test the
depth of CAP-001. This report does not approve an optimiser, retain a preferred
allocation, promote the packages into the student release or claim the solved
scenario materiality that belongs to whole-dataset calibration.

Every package represents one deterministic 12-week plan constructed with the
complete P01–P12 horizon known at P01. Period-specific disruption and recovery
rows are therefore planning assumptions available to the formulation from the
start, not surprises revealed while the plan is executing.

The first whole-dataset audit exposed excessive opening stock: all default
incumbents could avoid boundary replenishment. The deterministic recalibration
replaced arbitrary upstream quantities with flow-derived startup coverage,
aligned hard safety stock with opened pools and delayed non-opening terminal
demand without changing its horizon total. The renewed audit proves that every
default package uses boundary replenishment and passes all ten viability gates.

## Implemented artefacts

- `capstones/CAP-001/generator/generate_planning_data.py` creates the calendar,
  source and transformation capacity, inventory policy, opening stock, demand,
  performance history and incident history from the frozen network and
  commercial candidates.
- `capstones/CAP-001/generator/generate_dataset_packages.py` assembles BASE and
  SCN-01 through SCN-05 as six self-contained packages. Each package has all 25
  CSVs and its own manifest, file hashes and aggregate dataset hash.
- `cap001_model/data.py` resolves only the selected package's active scenario
  facts. It rebuilds effective period capacity, demand and lane routes without
  reading another package.
- `tooling/assess_dataset_packages.py` independently validates packages,
  manifests, schemas, keys, identities, derived-grain coverage, scenario
  profiles, common model construction and the bounded BASE feasibility smoke
  check.
- `tests/test_dataset_generation.py` exercises reproducibility,
  self-containment, state reset, impact resolution and adversarial failures.

The generated planning source is under
`capstones/CAP-001/generated/planning/`. The six candidate packages and their
retained evidence are under `capstones/CAP-001/generated/datasets/`.

## Planning profile

| Measure | Candidate |
|---|---:|
| Planning periods | 12 |
| Boundary source/material/period rows | 264 |
| Recipe/period transformation rows | 624 |
| Explicit inventory-policy states | 159 |
| Positive opening-stock states | 48 |
| Plant/terminal-material/period demand rows | 288 |
| Seller/material/month history rows | 2,100 |
| Historical incidents | 30 |
| Demand streams with variation | 24 of 24 |
| Demand streams with a material planned peak | 21 |
| Streams with a standard dispatch lead of at least two periods | 22 |
| Multi-recipe shared-capacity groups | 19 |
| Temporal-pressure witnesses | 66 |
| Multi-source pools with persistent service contrast | 40 |
| Historical rows marked `PARTIAL` | 3.81% |

Opening inventory spans eight plant states, sixteen Tier-1 states, sixteen
Tier-2 states and eight Tier-3 states. It bridges genuine opening-horizon lead
time and recipe-input gaps rather than populating every pool. Non-opening plant
streams begin after their replenishment lead plus a batching/startup allowance;
their deferred quantities are redistributed over the remaining periods.

For each non-null shared-capacity group, the generated rows repeat one group
budget per period and provide recipe-specific resource coefficients. The
author-side physical check now constrains the coefficient-weighted sum, so the
group identifiers are executable facts rather than labels.

## Scenario packages

| Package | Changed rows | Controlled effect | Depth witness |
|---|---:|---|---|
| BASE | 0 | Normal facts; impacts header only | Common comparison and zero-shortage feasibility |
| SCN-01 | 2 disruption rows plus recovery | `NODE-0005` polymer-resin capacity at 7% in P01–P03 and 50% in P04–P05 | Four downstream terminal materials |
| SCN-02 | 5 disruption rows plus 5 recovery rows | Standard lane capacity ×0.75, transit ×1.75 and freight ×1.40 in P02–P07 | Five Asia–Europe corridors retain expedited alternatives |
| SCN-03 | 2 disruption/restart rows plus recovery | `NODE-0030` unavailable in P04 and at 50% in P05 | Nine plant/material streams retain an approved alternate |
| SCN-04 | 5 differentiated reductions plus 5 recovery rows | Four `EUROPE_CENTRAL` nodes at 35–50% in P03–P06; anchor `NODE-0027` at 10% through P10 | Tier 2, Tier 3 and Tier 4 all participate |
| SCN-05 | 15 changed rows plus 14 recovery rows | SCN-01 and SCN-02 effects plus 10–15% uplift on eight critical streams | Composed source, logistics and priority-demand pressure |

Every recovery is explicit. The first controlled package set leaves normal
facts intact and records the selected reality through its package-local impact
rows, avoiding both cross-package fallback and double application.

## Package hashes

| Package | SHA-256 |
|---|---|
| BASE | `30e6d6dd1452cd70c5e396192a66c442f434029ccb24e81adf627748da90a86b` |
| SCN-01 | `08d2acd5b55e1d4c938e1aecc05357bb128bcbcc97ceb60e86efae7dc23ad05b` |
| SCN-02 | `0d24401da9f735f87359e2885bb1623268b29f658b70e885c4525dfc2c311adb` |
| SCN-03 | `21a4945ee516b299f17d7aca424aa4b7d19a2a25b029cfbb7f905ae40f20a892` |
| SCN-04 | `0a78513c4baea536af1a666d8777db1bae2c9fff2f613fc7f54218f9285a49da` |
| SCN-05 | `a786114ff06fb19928db94445ccd2dfaece294a530215578bd56d6262f82e800` |

These hashes change whenever any package file changes. The aggregate generation
manifest remains the authoritative machine record.

## Validation result

The independent assessment passes all 24 gates:

- six of six packages and 150 of 150 raw CSV instances are present and valid;
- no file resolves outside its selected package;
- all six manifests, identities and hashes agree;
- all six packages meet calendar and relationship-derived coverage;
- one loader and model-construction entry point accepts every package after a
  complete reload;
- the BASE physical MILP reaches zero shortage within the 45-second author
  smoke-check budget using HiGHS 1.15.1; and
- a second MILP proves that zero shortage is infeasible when all boundary
  sourcing is disabled; and
- every temporal, historical and scenario-participation threshold passes.

The feasibility evidence records status, solver, budget and zero shortage only.
No allocation is retained or published.

Negative tests reject a missing file even when another package contains it,
manifest/hash tampering, an unknown impact target, missing recovery, stale
state after dataset replacement and incorrect per-mode treatment of an
approval share cap.

## Acceptance and hand-off

The recalibrated quantities, opening-stock pattern and five scenario narratives
were accepted on 25 August 2026. The listed hashes are the exact inputs to the
passing 10/10 whole-dataset audit. Every scenario is zero-shortage feasible but
requires physical adaptation when a valid BASE witness is replayed against the
complete replacement dataset.

The audit retains aggregate feasibility, decision-pair and reconciliation
evidence only. It does not retain a reference allocation, endorse a policy or
promote the packages into the student release.
