# CAP-001 Planning and Dataset-Package Implementation Report

## Decision state

| Field | Value |
|---|---|
| Implementation state | Accepted technical checkpoint; calibration reopened by WP7 |
| Owner state | Former package freeze superseded by the WP7 controlled-reopen decision on 19 August 2026 |
| Date | 19 August 2026 |
| Configuration | `CAP-001-DECISION-CONFIG` v0.3.1 |
| Planning seed | `9042027` |
| Governing design | `docs/PLANNING_AND_SCENARIO_DESIGN_CONTRACT.md` |
| Scenario decision | ADR-008, accepted on 19 August 2026 |

The accepted package set supplies the temporal and scenario data needed to test the
depth of CAP-001. This report does not approve an optimiser, retain a preferred
allocation, promote the packages into the student release or claim the solved
scenario materiality that belongs to whole-dataset calibration.

The subsequent whole-dataset audit found that all pinned-default incumbents
could serve the horizon with zero boundary supply. The 23 checks below remain
valid as package-integrity and component-depth evidence, but they are no longer
sufficient acceptance evidence for the combined dataset. WP6 calibration is
reopened for deterministic regeneration, new package hashes and renewed owner
review.

## Implemented artefacts

- `capstones/CAP-001/generator/generate_planning_data.py` creates the calendar,
  source and transformation capacity, inventory policy, opening stock, demand,
  performance history and incident history from the frozen network and
  commercial candidates.
- `capstones/CAP-001/generator/generate_dataset_packages.py` assembles BASE and
  SCN-01 through SCN-05 as six self-contained packages. Each package has all 26
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
time gaps rather than populating every pool. Non-opening plant streams begin
only once an approved P01 dispatch can physically arrive.

For each non-null shared-capacity group, the generated rows repeat one group
budget per period and provide recipe-specific resource coefficients. The
author-side physical check now constrains the coefficient-weighted sum, so the
group identifiers are executable facts rather than labels.

## Scenario packages

| Package | Changed rows | Controlled effect | Depth witness |
|---|---:|---|---|
| BASE | 0 | Normal facts; impacts header only | Common comparison and zero-shortage feasibility |
| SCN-01 | 2 disruption rows plus recovery | `NODE-0003` silicon capacity at 30% in P03–P05 and 60% in P06 | Three downstream terminal materials |
| SCN-02 | 5 disruption rows plus 5 recovery rows | Standard lane capacity ×0.75, transit ×1.75 and freight ×1.40 in P02–P07 | Five Asia–Europe corridors retain expedited alternatives |
| SCN-03 | 2 disruption/restart rows plus recovery | `NODE-0030` unavailable in P04 and at 50% in P05 | Nine plant/material streams retain an approved alternate |
| SCN-04 | 5 differentiated reductions plus 5 recovery rows | Five `EUROPE_CENTRAL` nodes at 60–80% capacity in P03–P06 | Tier 2, Tier 3 and Tier 4 all participate |
| SCN-05 | 15 changed rows plus 14 recovery rows | SCN-01 and SCN-02 effects plus 10–15% uplift on eight critical streams | Composed source, logistics and priority-demand pressure |

Every recovery is explicit. The first controlled package set leaves normal
facts intact and records the selected reality through its package-local impact
rows, avoiding both cross-package fallback and double application.

## Package hashes

| Package | SHA-256 |
|---|---|
| BASE | `b040291ddcbac6671400732f3c2a4859ec2fd7010d45bb33f707cd0640eb88d2` |
| SCN-01 | `504d15fdfafa29112691a127de32efa066e9215b6f6cf17c57dfb317d375047d` |
| SCN-02 | `66086c534ed4fb92ec7a4112f94eb6b448796845dfba92637141784299bf19fe` |
| SCN-03 | `bdc048febb316f8f6dcb058168d1a4d44c7432c8c297972efa31ff8b927a19ae` |
| SCN-04 | `7b14ddec2ed4a504d9181da79fed77d3083cfb33f78bf68468abff62959beaa7` |
| SCN-05 | `be619dff17206d2a0d80191a0b571c48d7c009f72277be135253eb77dd3f2a3a` |

These hashes change whenever any package file changes. The aggregate generation
manifest remains the authoritative machine record.

## Validation result

The independent assessment passes all 23 gates:

- six of six packages and 156 of 156 raw CSV instances are present and valid;
- no file resolves outside its selected package;
- all six manifests, identities and hashes agree;
- all six packages meet calendar and relationship-derived coverage;
- one loader and model-construction entry point accepts every package after a
  complete reload;
- the BASE physical MILP reaches zero shortage within the 45-second author
  smoke-check budget using HiGHS 1.15.1; and
- every temporal, historical and scenario-participation threshold passes.

The feasibility evidence records status, solver, budget and zero shortage only.
No allocation is retained or published.

Negative tests reject a missing file even when another package contains it,
manifest/hash tampering, an unknown impact target, missing recovery, stale
state after dataset replacement and incorrect per-mode treatment of an
approval share cap.

## Acceptance and hand-off

The capstone owner accepted the visible quantities, history, opening-stock
pattern and five scenario narratives on 19 August 2026. WP7 later demonstrated
that the combined horizon could avoid boundary replenishment and reopened this
checkpoint. The listed hashes remain the exact inputs to the failed audit, not
student-release candidates. The next candidate requires controlled
regeneration, full revalidation, new hashes and renewed acceptance.

Solved differences in cost, service, inventory, concentration and recourse
remain a separate WP7 whole-dataset viability activity; they should not be
inferred from these structural witnesses alone. The packages are not promoted
into the student release by this acceptance.
