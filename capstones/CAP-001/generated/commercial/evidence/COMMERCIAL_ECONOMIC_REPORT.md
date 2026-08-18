# CAP-001 Commercial and Economic Report

## Outcome

Commercial assessment status: **PASS**.

This report assesses dataset coverage, accounting coherence and the presence of potential commercial trade-offs. It does not contain an optimised allocation or claim BASE feasibility.

## Candidate profile

| Dataset | Rows |
|---|---:|
| `supply_contracts.csv` | 138 |
| `incoterm_rules.csv` | 6 |
| `import_duty_rates.csv` | 138 |
| `shipping_lanes.csv` | 116 |
| `external_source_prices.csv` | 396 |
| `conversion_costs.csv` | 624 |
| `cost_allocation_rules.csv` | 47 |
| `fx_rates.csv` | 216 |
| `baseline_standard_costs.csv` | 576 |

## Decision-depth evidence

- Fixed/variable crossovers: 4
- Speed or reliability premiums: 12
- Tariff, FX or origin contrasts: 49
- Intermediate weighted-average mix effects: 36
- Baseline-versus-recursive ranking conflicts: 9
- Terminal materials below witness coverage: none

## Plausibility range profile

| Measure | Minimum | Maximum |
|---|---:|---:|
| fixed order cost eur | 90 | 5408.07 |
| horizon activation cost eur | 548.366 | 2773.22 |
| external unit price eur | 4.75431 | 55.406 |
| variable conversion cost eur | 5.9134 | 45.7283 |
| markup rate | 0.0535 | 0.1355 |
| duty rate | 0 | 0.075 |
| insurance rate | 0.00203 | 0.00966 |
| lane reliability | 78.2 | 96.2 |
| Maximum twelve-period FX movement | — | 3.85% |

## Interpretation

The witnesses establish that the commercial facts are not decorative and that reasonable alternatives can trade cost against lot size, transport service or exposure. They are calibration evidence only. WP6 must add demand, capacity, inventory and disruptions; WP7 must then test feasibility, scenario materiality and solved decision differences.

## Gate results

| Gate | Value | Threshold | Result |
|---|---:|---:|---|
| Approved flows with exactly one active contract | 138 | 138 | PASS |
| Active node pairs with a standard lane | 104 | 104 | PASS |
| Boundary contracts with twelve period prices | 33 | 33 | PASS |
| Intermediate contracts with external prices | 0 | 0 | PASS |
| Recipe-period conversion rows | 624 | 624 | PASS |
| Currency-period FX rows | 216 | 216 | PASS |
| Intermediate state-period comparator rows | 576 | 576 | PASS |
| Terminal materials retaining commercialised structural lineages | 8 | 8 | PASS |
| Distinct retained commercial trade-off witnesses | 115 | >= 16 | PASS |
| Terminal materials supported by at least two trade-off witnesses | 8 | 8 | PASS |
| Fixed/variable ranking crossovers | 4 | >= 4 | PASS |
| Faster options carrying a logistics premium | 12 | >= 4 | PASS |
| Tariff, FX or origin contrasts | 49 | >= 4 | PASS |
| Intermediate pools with material weighted-average cost sensitivity | 36 | >= 4 | PASS |
| Baseline-versus-recursive ranking conflicts | 9 | >= 4 | PASS |
| Corridors with expedited alternatives | 12 | 8–16 | PASS |
| Asia–Europe corridors with expedited alternatives | 5 | >= 2 | PASS |
| Strictly dominated options without a diversification rationale | 0 | 0 | PASS |
| Commercially dominated options retained for distinct dependency exposure | 5 | review | PASS |
| Synthetic commercial range controls outside their review bands | 0 | 0 | PASS |
| Cost disappearance, duplication or rule ambiguity | 0 | 0 | PASS |
