# Optimisation Capstones Control Repository

This is the private control repository for the optimisation capstone portfolio.
The current implementation work is CAP-001, Tier-N end-to-end cost and
resilience optimisation.

## Controlled build and validation commands

Build the derived data, result and evidence contracts:

```bash
python -m tooling.build_contract_artifacts
```

Check that committed generated artefacts have not drifted:

```bash
python -m tooling.build_contract_artifacts --check
```

Assemble and validate the professional candidate release:

```bash
python -m tooling.build_student_release
python -m tooling.validate_student_release
```

Validate the complete control repository:

```bash
python -m tooling.validate_wp1
python -m tooling.assess_whole_dataset_viability --check
python -m tooling.build_base_reference_benchmark --check
```

Audit the configuration directly against the approved DOCX sources:

```bash
python -m pip install -e '.[audit]'
python -m tooling.audit_source_documents
```

Run the test suite:

```bash
pytest
```

The authoritative machine-readable contract source is
`config/cap001_decision_config.json`. Generated schemas, documentation,
manifests and accepted data packages must be changed through their controlled
builders.

Historical work-package evidence remains under `docs/`. The current candidate
pack is `student_release/CAP-001-tier-n-release/`.
