"""Validate the complete CAP-001 contract and repository-scaffold evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tooling.build_contract_artifacts import RELEASE_ROOT, check_artifacts, planned_artifacts
from tooling.contract_runtime import (
    CONFIG_PATH,
    ROOT,
    ContractError,
    load_config,
    resolve_data_dir,
    sha256_path,
    validate_csv_file,
    validate_json_file,
    validate_raw_data_directory,
)


def validate_wp1(data_dir: Path | None = None) -> dict[str, int]:
    config = load_config()

    # Source-document lineage is part of the controlled configuration.
    document_paths = {
        "capstone_specification": ROOT / "CAP-001_Tier-N_End-to-End_Cost_Model_Design_and_Dataset_Generation_Specification_v0.3.docx",
        "control_standard": ROOT / "Optimisation_Search_and_Decision_Intelligence_Capstone_Control_Standard_v0.2.docx",
    }
    for key, path in document_paths.items():
        if not path.is_file():
            raise ContractError(f"governing document missing: {path.name}")
        expected = config["document_control"][key]["sha256"]
        actual = sha256_path(path)
        if actual != expected:
            raise ContractError(f"governing document hash drifted: {path.name}")

    # Every generated artefact must be exactly reproducible.
    errors = check_artifacts(planned_artifacts(config))
    if errors:
        raise ContractError("; ".join(errors))

    raw_dir = resolve_data_dir(data_dir or (ROOT / RELEASE_ROOT / "data/raw"))
    row_counts = validate_raw_data_directory(raw_dir, config)

    empty_contract_root = ROOT / RELEASE_ROOT / "reference/empty_contracts"
    for name, contract in config["output_contracts"].items():
        path = empty_contract_root / contract["path"]
        if contract["format"] == "json_object":
            validate_json_file(path, contract)
        else:
            validate_csv_file(path, contract)

    fixture_root = ROOT / RELEASE_ROOT / "data/miniature_fixture"
    for name, contract in config["miniature_fixture_contracts"].items():
        path = fixture_root / name
        if contract["format"] == "json_object":
            validate_json_file(path, contract)
        else:
            validate_csv_file(path, contract)
    validate_raw_data_directory(fixture_root / "inputs", config)
    validate_csv_file(
        fixture_root / "expected_reconciliation/fixture_control_totals.csv",
        config["miniature_fixture_contracts"]["fixture_control_totals.csv"],
    )

    # Required repository and governance scaffolds must all exist.
    required = [
        ROOT / "docs/generated/CAP-001_DATA_DICTIONARY.md",
        ROOT / "docs/generated/WP1_CONFIGURATION_SUMMARY.md",
        ROOT / "schemas/decision_config.schema.json",
        ROOT / "schemas/submission_manifest.schema.json",
        ROOT / "schemas/release_manifest.schema.json",
        ROOT / "adrs/ADR_TEMPLATE.md",
        ROOT / "adrs/register.json",
        ROOT / RELEASE_ROOT / "config/default_case.yaml",
        ROOT / RELEASE_ROOT / "starter/submission.yaml",
        ROOT / "templates/student_submission/submission.yaml",
    ]
    required.extend(ROOT / "adrs" / f"ADR-{number:03d}.md" for number in range(1, 13))
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        raise ContractError(f"WP1 required artefacts missing: {missing}")

    schema_counts = {
        "raw_schemas": len(list((ROOT / "schemas/raw_data").glob("*.schema.json"))),
        "output_schemas": len(list((ROOT / "schemas/required_outputs").glob("*.schema.json"))),
        "fixture_schemas": len(list((ROOT / "schemas/miniature_fixture").glob("*.schema.json"))),
    }
    expected_schema_counts = {"raw_schemas": 25, "output_schemas": 13, "fixture_schemas": 2}
    if schema_counts != expected_schema_counts:
        raise ContractError(f"schema counts drifted: {schema_counts}")

    return {
        "raw_contracts": len(config["raw_contracts"]),
        "raw_rows": sum(row_counts.values()),
        "output_contracts": len(config["output_contracts"]),
        "fixture_contracts": len(config["miniature_fixture_contracts"]),
        "adrs": len(config["adr_register"]),
        "generated_files": len(planned_artifacts(config)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="raw data directory; defaults to CAPSTONE_DATA_DIR or the generated empty set")
    args = parser.parse_args(argv)
    try:
        summary = validate_wp1(args.data_dir)
    except (ContractError, OSError, ValueError) as exc:
        print(f"WP1 validation failed: {exc}", file=sys.stderr)
        return 1
    print("WP1 validation passed:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
