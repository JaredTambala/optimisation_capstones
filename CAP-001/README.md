# CAP-001 Private Control Project

CAP-001 defines the Tier-N end-to-end cost and resilience optimisation
capstone. This directory is the complete project boundary: source material,
authoring documentation, configuration, generators, private model evidence,
tests, generated datasets and the professional candidate release all live
here.

The portfolio-wide control standard is shared from `../standards/`.

## Structure

| Path | Purpose |
|---|---|
| `source/` | CAP-001 source specification |
| `docs/` | Current authoring contracts, data-design rationale and change notes |
| `config/`, `schemas/`, `adrs/` | Controlled machine-readable decisions |
| `generator/`, `generated/` | Dataset generators and retained generated evidence |
| `miniature_fixture/`, `reference/` | Private validation and benchmark material |
| `cap001_model/` | Bounded author-side model-viability code |
| `tooling/`, `tests/` | Build, audit, validation and regression controls |
| `evaluation/` | Private AI-agent submission-review prompt |
| `student_release/CAP-001-tier-n-release/` | Complete candidate pack |

## Documentation map

| Purpose | Current documents |
|---|---|
| Engagement | `CAP-001_CONSULTANT_ENGAGEMENT_BRIEF.md`; `CAP-001_CANDIDATE_TASK_REQUIREMENTS.md`; `CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md` |
| Assessment | `CAP-001_CANDIDATE_ASSESSMENT_RUBRIC.md`; `CAP-001_REQUIREMENT_EVIDENCE_TRACEABILITY.md` |
| Release | `CAP-001_RELEASE_CONTRACT.md` |
| Dataset design | `NETWORK_STRUCTURE_DESIGN_CONTRACT.md`; `COMMERCIAL_ECONOMIC_DESIGN_CONTRACT.md`; `PLANNING_AND_SCENARIO_DESIGN_CONTRACT.md` |
| Viability | `WHOLE_DATASET_VIABILITY_METHOD_AND_RESULTS.md` |

These documents live under `docs/`. Historical implementation plans, status
snapshots, acceptance reports and deliverable registers are retained in Git
history rather than alongside the current contracts.

## Setup

Run commands from this directory:

```bash
python -m pip install -e '.[audit]'
```

## Build and validation

Build or check the derived contracts:

```bash
python -m tooling.build_contract_artifacts
python -m tooling.build_contract_artifacts --check
```

Assemble and validate the candidate release:

```bash
python -m tooling.build_student_release
python -m tooling.validate_student_release
```

Validate the control project and retained evidence:

```bash
python -m tooling.validate_control_project
python -m tooling.assess_whole_dataset_viability --check
python -m tooling.build_base_reference_benchmark --check
python -m tooling.audit_source_documents
pytest
```

The authoritative machine-readable source is
`config/cap001_decision_config.json`. Generated schemas, documentation,
manifests and accepted data packages must be changed through their controlled
builders.
