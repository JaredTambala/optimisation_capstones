# CAP-001 Commercial and Economic Implementation Status

## Outcome

The first full-scale commercial candidate has been generated from the frozen
network and passes all nineteen contract, coverage, accounting and
economic-depth gates. The capstone owner accepted the candidate on 18 August
2026. Its exact data, private seed and scorecard thresholds are frozen as the
input to WP6.

This work proves that the structural alternatives can be assigned coherent and
meaningfully different commercial facts. It does not prove BASE feasibility,
scenario materiality, final formulation bounds or an optimal allocation.

## Schema amendment

CN-003 removed the unused `supply_contracts.pricing_method` field. The effective
CN-005 later removed the synthetic standard-cost diagnostic. The effective
configuration and schema version is `0.3.3`, the data version is `0.3.2`, and
the contract now has 240 raw fields across 25 raw files. Boundary prices are
validated relationally from the
seller node and `external_source_prices.csv`; no row labels itself as
"recursive".

The configuration-derived schemas, dictionaries, empty contracts and manifests
were regenerated. Both miniature-fixture copies use the amended contract, and
their accounting totals are unchanged.

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

Every approval has one active contract, every active node pair has a standard
lane, all 33 boundary contracts have twelve price rows, and no intermediate
contract has an external price. The candidate contains twelve expedited lanes,
including five Asia–Europe corridors.

## Economic-depth result

| Gate | Result | Frozen threshold |
|---|---:|---:|
| Commercialised terminal lineages | 8 | 8 |
| Distinct trade-off and documented-retention witnesses | 106 | At least 16 |
| Fixed/variable ranking crossovers | 4 | At least 4 |
| Speed/reliability premiums | 12 | At least 4 |
| Tariff, FX or origin contrasts | 49 | At least 4 |
| Material intermediate-pool mix effects | 36 | At least 4 |
| Unexplained strictly dominated options | 0 | 0 |
| Documented diversification exceptions | 5 | Review |
| Terminal materials with at least two witnesses | 8 | 8 |
| Synthetic plausibility-range failures | 0 | 0 |
| Cost disappearance, duplication or rule ambiguity | 0 | 0 |

The five diversification exceptions are options dominated on the currently
available commercial dimensions but retained because their seller has a
different country, region or ultimate-parent exposure. WP6 and WP7 must verify
that this structural difference becomes useful in at least one controlled
disruption; otherwise those options should be regenerated or removed.

## Implementation and evidence

| Purpose | Evidence |
|---|---|
| Deterministic generation | `generator/generate_commercial_data.py` |
| Independent assessment | `tooling/assess_commercial_data.py` |
| Positive and adversarial tests | `tests/test_commercial_generation.py` |
| Eight generated tables | `generated/commercial/data/` |
| Seed, row-count and checksum record | `generated/commercial/generation_manifest.json` |
| Machine-readable gates | `generated/commercial/evidence/commercial_depth_scorecard.json` |
| Trade-off and retention witnesses | `generated/commercial/evidence/tradeoff_witnesses.json` |
| Conditional cost envelopes | `generated/commercial/evidence/conditional_cost_envelopes.json` |
| Seller-included boundary-price audit | `generated/commercial/evidence/external_price_build_up.json` |
| Human-readable review | `generated/commercial/evidence/COMMERCIAL_ECONOMIC_REPORT.md` |
| Student-visible accounting rules | `student_release/CAP-001-tier-n-release/COST_POLICY.md` |

The assessor independently reconstructs conditional values at low, central and
high quantity bands. These are calibration envelopes, not model solutions or
final big-M bounds.

## Adversarial coverage

The commercial tests reject:

- a missing contract or standard lane;
- an external price attached to a non-boundary relationship;
- a cost-rule precedence tie;
- freight incorrectly added to the markup base;
- a buyer-borne logistics component also embedded in a boundary quote;
- removal of the fixed-cost differences that create the required crossovers;
  and
- non-deterministic regeneration.

## Reproduction

```bash
python generator/generate_commercial_data.py --check
python -m tooling.assess_commercial_data --check
pytest -q tests/test_commercial_generation.py
```

## Progress gates

| Gate | Status | Finding |
|---|---|---|
| Policy ready | Implemented; formal review pending | CN-003 is applied, the public cost policy is populated and ADR-005 contains the proposed Incoterm and ledger decision |
| Candidate complete | Passed | All eight tables generate deterministically and pass contract and coverage checks |
| Depth demonstrated | Passed | All proposed commercial-depth thresholds pass with retained witnesses |
| Owner accepted | Passed | The capstone owner accepted the generated report, ranges and five diversification exceptions on 18 August 2026 |

WP5 is complete. The candidate, thresholds and seed are frozen inputs to WP6.
Any later change requires an explicit recalibration decision and a complete
assessment rerun; individual CSV rows must not be hand-edited. Formal ADR-005
review remains a separate release-level governance gate.
