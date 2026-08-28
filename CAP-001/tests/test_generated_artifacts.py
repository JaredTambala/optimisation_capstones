from __future__ import annotations

import json

from tooling.build_contract_artifacts import RELEASE_ROOT, check_artifacts, planned_artifacts
from tooling.build_student_release import check_payloads, planned_payloads
from tooling.contract_runtime import ROOT, load_config


def test_generated_artifacts_are_current() -> None:
    config = load_config()
    assert check_artifacts(planned_artifacts(config)) == []


def test_generated_schema_counts_and_strict_rows() -> None:
    raw_schemas = sorted((ROOT / "schemas/raw_data").glob("*.schema.json"))
    output_schemas = sorted((ROOT / "schemas/required_outputs").glob("*.schema.json"))
    application_schemas = sorted((ROOT / "schemas/application_evidence").glob("*.schema.json"))
    fixture_schemas = sorted((ROOT / "schemas/miniature_fixture").glob("*.schema.json"))
    assert (len(raw_schemas), len(output_schemas), len(application_schemas), len(fixture_schemas)) == (25, 14, 3, 2)

    for path in raw_schemas:
        schema = json.loads(path.read_text())
        assert schema["type"] == "array"
        assert schema["items"]["additionalProperties"] is False

    for path in output_schemas + application_schemas + fixture_schemas:
        schema = json.loads(path.read_text())
        if schema["type"] == "array":
            assert schema["items"]["additionalProperties"] is False
        else:
            assert schema["additionalProperties"] is False


def test_professional_release_covers_required_paths_without_submission_scaffold() -> None:
    config = load_config()
    release = ROOT / RELEASE_ROOT
    for directory in config["required_repository_paths"]["student_release"]:
        assert (release / directory).is_dir()
    for directory in config["required_repository_paths"]["private_control"]:
        assert (ROOT / directory).is_dir()
    submission_template = ROOT / "templates/student_submission"
    assert not submission_template.exists() or not any(
        path.is_file() for path in submission_template.rglob("*")
    )
    assert not list(release.rglob("*.yaml"))
    assert not list(release.rglob("*.yml"))


def test_manifests_and_dictionary_expose_controlled_versions() -> None:
    release_manifest = json.loads((ROOT / RELEASE_ROOT / "release_manifest.json").read_text())
    assert release_manifest["release_version"] == "0.3.0"
    assert release_manifest["data_contract_version"] == "0.3.3"
    assert release_manifest["schema_version"] == "0.4.0"
    assert release_manifest["rubric_version"] == "1.1.0"
    assert set(release_manifest["dataset_packages"]) == {
        "BASE", "SCN-01", "SCN-02", "SCN-03", "SCN-04", "SCN-05"
    }
    assert all(item["file_count"] == 25 for item in release_manifest["dataset_packages"].values())

    dictionary = (ROOT / "docs/generated/CAP-001_DATA_DICTIONARY.md").read_text()
    assert dictionary.count("### `") == 42
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


def test_professional_release_is_current_and_candidate_neutral() -> None:
    config = load_config()
    assert check_payloads(planned_payloads(config)) == []
    release = ROOT / RELEASE_ROOT
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in release.rglob("*.md")
    )
    for prescriptive_default in ("config/default_case.yaml", "submission.yaml", "Streamlit"):
        assert prescriptive_default not in joined
    assert "Deterministic quality gates" not in joined
    assert "Quality-gate vocabulary" not in joined
