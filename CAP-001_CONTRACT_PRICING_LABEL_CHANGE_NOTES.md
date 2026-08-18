# CAP-001 Contract Pricing Label Change Notes

## Document control

| Field | Value |
|---|---|
| Change note | CN-003 — Remove the contract-level recursive-pricing label |
| Status | Approved by capstone owner; implementation authorised |
| Date | 18 August 2026 |
| Current specification | *CAP-001 Tier-N End-to-End Cost Model, Modelling Decisions and Dataset Generation Specification* v0.3, raw contract `supply_contracts.csv` |
| Current specification SHA-256 | `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` (unchanged — this note amends the contract by reference) |
| Effective configuration | `0.3.1` |
| Effective data/schema version | `0.3.1` |
| Change class | Removal of one redundant required raw-data field and its two-value domain |
| Explicitly unchanged | All 26 raw-data files; every other raw-data field; external-price boundary policy; pooling, transformation and value equations; formulation and assessment requirements |

## 1. Decision

Remove `pricing_method` from `supply_contracts.csv`. Withdraw the values
`EXTERNAL_UNIT_PRICE` and `RECURSIVE_COST_PLUS` from the raw-data contract.

The removed field did not describe a leg-local commercial fact and was not
used by the fixture reconciler or private model-data loader. In particular,
`RECURSIVE_COST_PLUS` incorrectly presented recursion as a property of an
individual contract row. The nested value structure is instead created by
joining approvals, contracts, lanes, node/material pools and transformations.
It is part of the problem that the candidate must identify and formulate, not
a label to repeat on every internal relationship.

## 2. Replacement control

Boundary pricing is determined from existing relationships:

1. a contract resolves to an approval;
2. the approval resolves to its seller node and material;
3. an active contract whose seller has `external_boundary_flag=true` must have
   exactly one `external_source_prices.csv` row for its material in each active
   period; and
4. every other contract must have no external-price row.

An external price on a non-boundary relationship, or a missing external price
on an active boundary relationship, is a validation failure. Internal goods
value must be formed from the supplying node/material/period pool under the
common accounting policy.

## 3. Consequences

- `supply_contracts.csv` has 13 fields instead of 14.
- The complete raw-data contract has 247 fields instead of 248.
- The effective configuration, data and schema versions move to `0.3.1`; the
  capstone and model versions remain `0.3.0`.
- Configuration-derived schemas, dictionaries, empty raw contracts, manifests
  and checksums must be regenerated.
- Both authored miniature-fixture copies must remove the column and its values.
- The source-document audit must compare the frozen DOCX after applying this
  one controlled omission and continue to reject every other field difference.
- WP5 validation replaces enum checking with the stronger relational boundary
  price checks in §2.

## 4. Acceptance

The amendment is complete when:

1. `pricing_method` is absent from the configuration, schemas, dictionaries,
   empty contracts, fixture data and planned full commercial data;
2. generated-artifact and source-alignment audits pass;
3. fixture reconciliation totals remain unchanged;
4. an adversarial non-boundary external price is rejected; and
5. the full test suite passes.
