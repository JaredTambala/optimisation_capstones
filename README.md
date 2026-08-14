# Optimisation Capstones Control Repository

This is the private control repository for the optimisation capstone portfolio.
The current implementation work is CAP-001, Tier-N end-to-end cost and
resilience optimisation.

## Contract-generation commands

Build the derived WP1 contracts:

```bash
python -m tooling.build_contract_artifacts
```

Check that committed generated artefacts have not drifted:

```bash
python -m tooling.build_contract_artifacts --check
```

Validate the configuration and generated empty contracts:

```bash
python -m tooling.validate_wp1
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

The authoritative machine-readable source is
`config/cap001_decision_config.json`. Generated schemas, documentation,
examples, ADRs and repository skeletons must not be edited directly.

The completed WP1 evidence is recorded in `docs/WP1_ACCEPTANCE_REPORT.md`.
