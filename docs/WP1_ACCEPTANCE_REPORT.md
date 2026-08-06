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
| Generated artefacts agree with source configuration | `generated/WP1_ARTIFACT_MANIFEST.json` and SHA-256 lineage file | `python -m tooling.build_wp1_artifacts --check` | Passed |
| Unsupported fields and semantic drift fail | Strict schemas, field fingerprints and runtime validator | Extra-field, renamed-field, wrong-constant, bad-enum, bad-header and file-set negative tests | Passed |
| Raw data supports read-only mount | `CAPSTONE_DATA_DIR` resolver and read-only validator | `tests/test_read_only_data.py` hashes all files before and after validation | Passed |

## Acceptance totals

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

## Executed acceptance commands

```text
python -m tooling.build_wp1_artifacts --check
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

## Deliberate remaining controls

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
