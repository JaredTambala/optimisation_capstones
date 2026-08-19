# CAP-001 WP1 Configuration Summary

> Generated from `config/cap001_decision_config.json`. Do not edit directly.

| Control | Value |
|---|---|
| Configuration | `0.3.1` |
| Capstone/data/model | `0.3.0` / `0.3.1` / `0.3.0` |
| Network | `TIER_N_DAG`, four supplier tiers plus four plants |
| Pooling | `WEIGHTED_AVERAGE` |
| Baseline | `FIXED_PRICE_MILP` |
| Assessed semantics | `RECURSIVE_COST_MINLP` |
| Raw contracts | 26 |
| Output contracts | 15 |
| Scenarios | BASE, SCN-01, SCN-02, SCN-03, SCN-04, SCN-05 |
| ADRs | 12: 1 accepted, 11 proposed |

## Release block

WP1 establishes contracts; it does not approve the controlled-open decisions.
No student release may be issued until the ADRs, miniature fixture, generator,
reference routes and all acceptance checks pass.
