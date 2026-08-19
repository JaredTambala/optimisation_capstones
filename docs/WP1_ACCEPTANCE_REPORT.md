# CAP-001 WP1 Acceptance Report

## Decision

| Field | Value |
|---|---|
| Work package | WP1 — Decision configuration and schemas |
| Status | Passed |
| Acceptance date | 31 July 2026 |
| Configuration version | `0.3.0` |
| Governing CAP specification | CAP-001 v0.3, SHA-256 `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` |
| Governing control standard | v0.2, SHA-256 `2741ebd6b1e01e4102c39c9f43de3a9f05b081aa61a3efd2838a431024a45637` |

WP1 is complete as a contract-and-scaffolding work package. This decision does
not approve the twelve ADRs, release a student dataset or claim completion of
the miniature recursive-cost fixture. Those are later gates.

## Requirement-by-requirement evidence

| WP1 requirement | Implementation evidence | Verification evidence | Result |
|---|---|---|---|
| Versioned source of truth for business, network, time, pooling, cost, bounds, scenarios, tolerances, outputs and assessment | `config/cap001_decision_config.json` | `tests/test_frozen_policies.py`; `tooling/contract_runtime.py` | Passed |
| All 26 raw-data contracts | `raw_contracts` configuration and `schemas/raw_data/` | DOCX tables 25–50 compared by `tooling/audit_source_documents.py`: 26 files and 248 fields | Passed |
| Miniature-fixture contracts | `miniature_fixture_contracts` and `schemas/miniature_fixture/` | Schema and empty-example validation | Passed |
| Submission metadata | `submission_manifest_example`, `schemas/submission_manifest.schema.json` and generated `submission.yaml` | Strict schema and YAML parse | Passed |
| CAP-specific and common required outputs | `output_contracts` and `schemas/required_outputs/` | 13 CAP outputs plus five common outputs reconciled to 15 unique contracts | Passed |
| Human-readable dictionary | `docs/generated/CAP-001_DATA_DICTIONARY.md` and release copy | Generated-artifact drift test and contract inventory test | Passed |
| Empty valid raw contracts | 26 header-only CSVs under the student-release scaffold and a second complete set under miniature-fixture inputs | Exact header/type validator; read-only mount test | Passed |
| Empty valid output contracts | CSV headers and minimal JSON objects under `reference/empty_contracts/` | Project validator and independent JSON Schema 2020-12 validation | Passed |
| Stable IDs, FKs, units, currency, effective periods and null rules | Field metadata in `raw_contracts`; generated dictionary and schemas | Configuration semantic tests and source-document audit | Passed |
| Controlled run modes, formulation classes and statuses | Decision configuration and `run_metadata` schema | Frozen-policy and invalid-status tests | Passed |
| ADR-001 through ADR-012 records | `adrs/ADR-001.md` through `ADR-012.md`, template and register | Required-section and sequence tests | Passed |
| Private control skeleton | `capstones/CAP-001/` | Required-directory test | Passed |
| Student-release skeleton | `student_release/CAP-001-tier-n-release/` | Required-directory and artefact tests | Passed |
| Submission skeleton | `templates/student_submission/` | Required-directory, command and executable-mode checks | Passed |
| Generated artefacts agree with source configuration | `generated/WP1_ARTIFACT_MANIFEST.json` and SHA-256 lineage file | `python -m tooling.build_contract_artifacts --check` | Passed |
| Unsupported fields and semantic drift fail | Strict schemas, field fingerprints and runtime validator | Extra-field, renamed-field, wrong-constant, bad-enum, bad-header and file-set negative tests | Passed |
| Raw data supports read-only mount | `CAPSTONE_DATA_DIR` resolver and read-only validator | `tests/test_read_only_data.py` hashes all files before and after validation | Passed |

## Original acceptance snapshot

The counts and command output below record the 31 July 2026 acceptance run and
are retained as historical evidence. The current verification state appears
after Amendment 1.

| Evidence | Count |
|---|---:|
| Raw-data contracts | 26 |
| Raw-data fields traced to v0.3 | 248 |
| Required/common output contracts | 15 |
| Output fields | 225 |
| Miniature-fixture contracts | 2 |
| JSON Schemas including control schemas | 46 |
| ADR records | 12 |
| Deterministically generated WP1 files | 235 |
| Automated tests | 22 |

## Originally executed acceptance commands

```text
python -m tooling.build_contract_artifacts --check
WP1 generated artefacts are current (235 files).

python -m tooling.audit_source_documents
Source-document audit passed: 2 governing documents, 26 raw contracts,
248 raw fields, 13 CAP outputs, 5 common outputs, 10 rubric categories and
6 solution statuses.

python -m tooling.validate_wp1
WP1 validation passed: 26 raw contracts, 15 output contracts,
2 fixture contracts, 12 ADRs and 235 generated files.

pytest
22 passed.
```

An additional independent check validated all 46 schemas against the JSON
Schema 2020-12 metaschema, validated the decision configuration, submission and
release examples, and validated every empty JSON/CSV contract. Ruby's safe YAML
loader independently parsed all three generated YAML files.

## Deliberate remaining controls at original acceptance

The following are not WP1 gaps:

- ADR-001 through ADR-012 remain `PROPOSED` and require controlled approval.
- The generated raw CSVs contain headers only; populated synthetic data belongs
  to WP4–WP6.
- The miniature fixture directories and schemas exist, but the five-period
  hand calculation and negative cases belong to WP2.
- Solver placeholders fail explicitly; solver adapters belong to WP3 and WP7.
- Student-facing prose files are controlled scaffolds; completed learning and
  release material belongs to WP9.
- `release_manifest.template.json` is explicitly marked as a template. A signed
  release manifest and checksums belong to the release gate.

The capstone therefore remains blocked from student release even though WP1 has
passed.

## Amendment 1 (CN-002) — 6 August 2026

During WP2 implementation, the capstone owner directed that the miniature
fixture be expanded from the single-chain topology described in the frozen
v0.3 specification's §12.8/Appendix E to a richer, multi-sourced four-layer
network (`CAP-001_MINIATURE_FIXTURE_TOPOLOGY_CHANGE_NOTES.md`, CN-002). This
reopened two pieces of already-accepted WP1 evidence:

1. `config/cap001_decision_config.json`'s `miniature_fixture_contracts.fixture_manifest.json.fields[supplier_tier_count].const`
   changed from `4` to `3`, reflecting that the fixture now instantiates three
   supplier tiers (Tier 4, Tier 3, Tier 2) plus a separate plant layer, with
   Tier 1 no longer instantiated as a distinct fixture layer. The corresponding
   hard-coded value in `tooling/build_contract_artifacts.py`'s fixture-manifest
   generation was updated to match. `period_count` (`const: 5`) and every
   full-release constant (`network.release_instance_supplier_tiers = 4`,
   `network.plant_count = 4`, `network.target_scale`) are unaffected.
2. `tooling/build_contract_artifacts.py` previously generated header-only content
   for the 26 fixture input files and both `expected_reconciliation` files,
   and its `--check` drift detector treated any populated row content as
   "generated artefact drifted" or "unsupported stale generated artefact."
   Since WP2's job is to populate those files with real, hand-authored data,
   ownership of those specific paths (`data/miniature_fixture/inputs/*`,
   `data/miniature_fixture/expected_reconciliation/*`,
   `data/miniature_fixture/fixture_control_totals.csv`, and the generated
   `reference/miniature_fixture/ACCOUNTING_WALKTHROUGH.md`) was formally
   relinquished to the authored fixture via an `AUTHORED_FIXTURE_PREFIXES` exclusion in
   `check_artifacts`'s stale-file sweep, and the "otherwise materialized"
   `.gitkeep` placeholder loop was updated to skip those same paths.

Both changes were regenerated and re-verified end to end:
`python -m tooling.build_contract_artifacts --check`, `python -m tooling.validate_wp1`,
`python -m tooling.audit_source_documents` and the full `pytest` suite (22
tests) all passed unchanged after the amendment — no test in the WP1 suite
asserts `supplier_tier_count`, so no test required modification. WP1's
"Passed" acceptance decision stands; this amendment record exists so the
`supplier_tier_count` and fixture-path-ownership changes are traceable rather
than a silent edit to previously accepted evidence.

## Current verification snapshot — 14 August 2026

The fixture implementation adds twenty-one tests to the original twenty-two,
and the contract generator now owns 206 artefacts after fixture-row ownership
was transferred to the authored fixture.

| Evidence | Current count/result |
|---|---:|
| Configuration-derived contract/scaffold artefacts | 206 |
| Fixture-derived artefacts | 12 |
| Automated tests | 43 passed |
| Fixture raw rows | 346 |
| Reconciliation identities | 681 passed |
| Published control totals | 105 reproduced |
| Maximum absolute reconciliation residual | `1.1368683772161603e-13` |
| Stage-2 value | EUR 2239.30 |

Current verification commands:

```text
python -m tooling.build_contract_artifacts --check
python -m tooling.build_fixture_reconciliation --check
python -m tooling.validate_wp1
python -m tooling.validate_fixture
python -m tooling.audit_source_documents
pytest
```

The contract, fixture and source-document validators pass. Formal fixture
acceptance remains pending the outstanding CN-002 stakeholder approvals; this
snapshot records implementation readiness, not approval.

## Amendment 2 (CN-003) — 18 August 2026

WP5 design review found that `supply_contracts.pricing_method` did not describe
a leg-local business fact. Its `RECURSIVE_COST_PLUS` value disclosed a
network-level interpretation on individual internal contract rows, while the
field was unused by both the fixture reconciler and private model-data loader.
The capstone owner directed that the nested value structure remain something
the candidate discovers from the relationships rather than a row label.

CN-003 therefore removes that field and its two-value enum. The effective
configuration, data and schema versions move to `0.3.1`; the capstone and model
versions remain `0.3.0`. The same 26 raw contracts now contain 247 fields.
Boundary-price eligibility is checked more strongly through seller-node status
and external-price row coverage.

The configuration-derived schemas, dictionaries, empty contracts, release
manifests and both authored fixture copies were updated. The source-document
audit applies the single CN-003 omission to the frozen v0.3 field table and
continues to reject every other difference. Fixture values and all 105 control
totals are unchanged.

Current verification after CN-003, commercial generation and the start of
scenario-policy authoring:

| Evidence | Current count/result |
|---|---:|
| Configuration-derived contract/scaffold artefacts | 203 |
| Effective raw-data fields | 247 |
| Fixture-derived artefacts | 12 |
| Automated tests | 76 passed |
| Fixture reconciliation identities | 681 passed |
| Published fixture control totals | 105 reproduced |
| Maximum fixture residual | `1.1368683772161603e-13` |

The generated count decreases from 204 to 203 because ADR-008 is now an
independently authored decision record, like ADR-005, rather than a generated
placeholder. No schema or contract artefact was removed.

`python -m tooling.build_contract_artifacts --check`, the source audit, WP1
validator, fixture validator and full test suite all pass. WP1's original
acceptance remains valid as amended by CN-002 and CN-003.
