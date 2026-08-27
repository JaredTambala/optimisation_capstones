from __future__ import annotations

import json

from tooling.build_contract_artifacts import RELEASE_ROOT, check_artifacts, planned_artifacts
from tooling.contract_runtime import ROOT, load_config


def test_generated_artifacts_are_current() -> None:
    config = load_config()
    assert check_artifacts(planned_artifacts(config)) == []


def test_generated_schema_counts_and_strict_rows() -> None:
    raw_schemas = sorted((ROOT / "schemas/raw_data").glob("*.schema.json"))
    output_schemas = sorted((ROOT / "schemas/required_outputs").glob("*.schema.json"))
    fixture_schemas = sorted((ROOT / "schemas/miniature_fixture").glob("*.schema.json"))
    assert (len(raw_schemas), len(output_schemas), len(fixture_schemas)) == (25, 13, 2)

    for path in raw_schemas:
        schema = json.loads(path.read_text())
        assert schema["type"] == "array"
        assert schema["items"]["additionalProperties"] is False

    for path in output_schemas + fixture_schemas:
        schema = json.loads(path.read_text())
        if schema["type"] == "array":
            assert schema["items"]["additionalProperties"] is False
        else:
            assert schema["additionalProperties"] is False


def test_release_and_submission_skeletons_cover_required_paths() -> None:
    config = load_config()
    release = ROOT / RELEASE_ROOT
    for directory in config["required_repository_paths"]["student_release"]:
        assert (release / directory).is_dir()
    for directory in config["required_repository_paths"]["submission_template"]:
        assert (ROOT / "templates/student_submission" / directory).is_dir()
    for directory in config["required_repository_paths"]["private_control"]:
        assert (ROOT / directory).is_dir()


def test_manifests_and_dictionary_expose_controlled_versions() -> None:
    release_manifest = json.loads((ROOT / RELEASE_ROOT / "release_manifest.template.json").read_text())
    assert release_manifest["capstone_version"] == "0.3.0"
    assert release_manifest["data_version"] == "0.3.2"
    assert release_manifest["rubric_version"] == "0.2.0"
    assert len(release_manifest["required_outputs"]) == 13

    dictionary = (ROOT / "docs/generated/CAP-001_DATA_DICTIONARY.md").read_text()
    assert dictionary.count("### `") == 38
    assert "`baseline_standard_costs.csv`" not in dictionary
    assert "`baseline_comparison.csv`" not in dictionary
    assert "`recursive_cost_reconciliation.csv`" not in dictionary


def test_adrs_have_every_required_section() -> None:
    headings = {
        "## Context",
        "## Decision",
        "## Alternatives considered",
        "## Mathematical and accounting consequences",
        "## Data consequences",
        "## Assessment consequences",
        "## Affected artefacts",
    }
    for number in range(1, 13):
        path = ROOT / "adrs" / f"ADR-{number:03d}.md"
        content = path.read_text()
        assert headings.issubset(set(content.splitlines()))
        if number == 8:
            assert "| Status | ACCEPTED |" in content
            assert "| Approval date | 19 August 2026 |" in content
        else:
            assert "| Status | PROPOSED |" in content


def test_submission_yaml_declares_all_five_commands() -> None:
    text = (ROOT / "templates/student_submission/submission.yaml").read_text()
    for command in ("setup:", "test:", "reproduce_reference:", "solve_default:", "run_app:"):
        assert command in text
    for script in ("setup.sh", "run_tests.sh", "reproduce_reference.sh", "run_model.sh", "run_app.sh"):
        mode = (ROOT / "templates/student_submission/scripts" / script).stat().st_mode
        assert mode & 0o111
