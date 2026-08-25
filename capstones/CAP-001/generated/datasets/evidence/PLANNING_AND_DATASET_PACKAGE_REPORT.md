# CAP-001 Planning and Dataset-Package Assessment

## Outcome

Assessment status: **PASS**.

The evidence concerns dataset completeness, planning depth, package interchangeability and a bounded physical-feasibility smoke check. It does not publish or endorse an allocation.

## Candidate profile

- Complete dataset roots: 6
- Raw CSV files validated: 156
- Positive opening-stock states: 48
- Shared capacity groups: 19
- Historical contrast pools: 40
- BASE feasibility: PASS (optimal)
- BASE boundary-source dependency: PASS (infeasible)

## Scenario profile

- SCN-01 downstream terminal materials: 4
- SCN-02 standard corridors retaining expedited alternatives: 5
- SCN-03 terminal streams retaining an alternate: 9
- SCN-04 affected nodes/tiers: 5/3
- SCN-05 demand-uplift streams: 8

## Gate results

| Gate | Value | Threshold | Result |
|---|---:|---:|---|
| Complete dataset packages | 6 | 6 | PASS |
| Required schema-valid raw files | 156 | 156 | PASS |
| Complete manifests with matching identity | 6 | 6 | PASS |
| Files resolving outside their selected package | 0 | 0 | PASS |
| Packages with complete derived-grain coverage | 6 | 6 | PASS |
| Packages accepted by one loader and model constructor | 6 | 6 | PASS |
| BASE zero-shortage physical MILP witness | 1 | 1 | PASS |
| BASE zero-shortage dependence on boundary sourcing | 1 | 1 | PASS |
| Terminal streams with planned variation | 24 | 24 | PASS |
| Terminal streams with material planned peaks | 21 | >=8 | PASS |
| Terminal streams supported by standard dispatch at least two periods earlier | 22 | >=8 | PASS |
| Positive opening-stock states | 48 | 32..56 | PASS |
| Opening-stock location classes | 4 | >=4 including plants | PASS |
| Multi-recipe shared-capacity groups | 19 | >=6 | PASS |
| Temporal pressure witnesses | 66 | >=16 | PASS |
| Multi-source pools with service contrast | 40 | >=8 | PASS |
| Partial historical rows | 0.0381 | 3%..10% | PASS |
| Stress packages with active targets | 5 | 5 | PASS |
| Packages matching controlled scenario targets and magnitudes | 6 | 6 | PASS |
| SCN-01 affected terminal materials | 4 | >=2 | PASS |
| SCN-02 standard lanes retaining expedited alternatives | 5 | >=4 | PASS |
| SCN-03 terminal streams with approved alternate | 9 | >=3 | PASS |
| SCN-04 affected nodes across supplier tiers | 5 | >=5 nodes, >=3 tiers | PASS |
| SCN-05 critical-demand uplift streams | 8 | >=1 at 10%..15% | PASS |
