"""Validate the CAP-001 professional release as a self-contained candidate pack."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from tooling.build_student_release import RELEASE_ROOT, check_payloads, planned_payloads
from tooling.contract_runtime import (
    EXPECTED_RAW_FILES,
    ContractError,
    load_config,
    sha256_path,
    validate_csv_file,
    validate_json_file,
    validate_raw_data_directory,
)


FORBIDDEN_PATH_FRAGMENTS = (
    "data/raw",
    "empty_contracts",
    "starter",
    "submission.yaml",
    "default_case.yaml",
    "recursive_cost_reconciliation",
    "baseline_standard_costs",
    "cap001_model",
    "/generator/",
    "/viability/",
    "/evaluator/",
    "/hidden/",
)
REQUIRED_GUIDANCE = {
    "README.md",
    "CAPSTONE_BRIEF.md",
    "TASK_REQUIREMENTS.md",
    "APPLICATION_AND_EVIDENCE_GUIDE.md",
    "ASSESSMENT_RUBRIC.md",
    "DATA_DICTIONARY.md",
    "COST_POLICY.md",
    "DATASET_GUIDE.md",
    "AI_NATIVE_WORKING_GUIDE.md",
    "PRODUCTION_READINESS_GUIDE.md",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _manifest_file_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = manifest.get("files")
    _require(isinstance(records, list), "release manifest files must be a list")
    result = {record["path"]: record for record in records}
    _require(len(result) == len(records), "release manifest contains duplicate paths")
    return result


def validate_release(release_dir: Path) -> dict[str, int]:
    release_dir = release_dir.resolve()
    config = load_config()
    _require(release_dir.is_dir(), f"release directory does not exist: {release_dir}")

    paths = [path for path in release_dir.rglob("*") if path.is_file()]
    relative_paths = {path.relative_to(release_dir).as_posix() for path in paths}
    _require(not any(path.is_symlink() for path in release_dir.rglob("*")), "release contains a symlink")
    _require(
        not any(path.lower().endswith((".yaml", ".yml")) for path in relative_paths),
        "release contains student-facing YAML",
    )
    _require(
        not any(path.lower().endswith((".py", ".sh")) for path in relative_paths),
        "release contains author implementation code or executable scaffolding",
    )
    _require(
        not any(fragment in path.lower() for path in relative_paths for fragment in FORBIDDEN_PATH_FRAGMENTS),
        "release contains retired or prescriptive scaffold material",
    )
    _require(REQUIRED_GUIDANCE <= relative_paths, "release guidance set is incomplete")
    _require(
        "ASSESSMENT_AND_DEFENCE_GUIDE.md" not in relative_paths,
        "release contains superseded evaluator mechanics",
    )

    for relative in relative_paths:
        if relative.endswith(".md"):
            content = (release_dir / relative).read_text(encoding="utf-8")
            _require(
                re.search(r"\bWP(?:8|9|10)\b", content) is None,
                f"internal work-package language leaked into {relative}",
            )
            _require(
                "deterministic quality gate" not in content.lower()
                and "quality-gate vocabulary" not in content.lower(),
                f"candidate-facing evaluator mechanics leaked into {relative}",
            )

    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    manifest_files = _manifest_file_map(manifest)
    expected_manifest_paths = relative_paths - {"release_manifest.json", "CHECKSUMS.sha256"}
    _require(set(manifest_files) == expected_manifest_paths, "release manifest file set differs")
    for relative, record in manifest_files.items():
        path = release_dir / relative
        _require(path.stat().st_size == record["bytes"], f"release byte count differs: {relative}")
        _require(sha256_path(path) == record["sha256"], f"release hash differs: {relative}")

    checksum_rows = (release_dir / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    checksum_map = {row[66:]: row[:64] for row in checksum_rows}
    expected_checksum_paths = relative_paths - {"CHECKSUMS.sha256"}
    _require(set(checksum_map) == expected_checksum_paths, "checksum file set differs")
    for relative, expected in checksum_map.items():
        _require(sha256_path(release_dir / relative) == expected, f"checksum differs: {relative}")

    package_ids = tuple(config["professional_release"]["dataset_package_ids"])
    _require(tuple(manifest["dataset_package_ids"]) == package_ids, "release package identity drifted")
    _require(manifest["rubric_version"] == config["versions"]["rubric"], "release rubric version drifted")
    package_rows = 0
    for package_id in package_ids:
        package_root = release_dir / "data" / "datasets" / package_id
        data_dir = package_root / "data"
        counts = validate_raw_data_directory(data_dir, config)
        package_rows += sum(counts.values())
        package_manifest = json.loads((package_root / "dataset_manifest.json").read_text(encoding="utf-8"))
        _require(package_manifest["dataset_id"] == package_id, f"{package_id}: dataset identity differs")
        _require(package_manifest["source_package_id"] == package_id, f"{package_id}: source identity differs")
        _require(package_manifest["package_semantics"] == "COMPLETE_DATASET", f"{package_id}: not a complete dataset")
        _require(package_manifest["complete_horizon_known_at_p01"] is True, f"{package_id}: horizon knowledge differs")
        for file_name in EXPECTED_RAW_FILES:
            _require(
                sha256_path(data_dir / file_name) == package_manifest["files"][file_name]["sha256"],
                f"{package_id}/{file_name}: package hash differs",
            )

    fixture_root = release_dir / "data" / "miniature_fixture"
    validate_raw_data_directory(fixture_root / "inputs", config)
    for name, contract in config["miniature_fixture_contracts"].items():
        path = fixture_root / name
        if contract["format"] == "json_object":
            validate_json_file(path, contract)
        else:
            validate_csv_file(path, contract)

    benchmark_root = release_dir / "reference" / "base_benchmark"
    benchmark_manifest = json.loads((benchmark_root / "benchmark_manifest.json").read_text(encoding="utf-8"))
    for name, record in benchmark_manifest["files"].items():
        _require(sha256_path(benchmark_root / name) == record["sha256"], f"benchmark hash differs: {name}")
    benchmark_contract = json.loads((benchmark_root / "benchmark_contract.json").read_text(encoding="utf-8"))
    base_manifest = json.loads(
        (release_dir / "data/datasets/BASE/dataset_manifest.json").read_text(encoding="utf-8")
    )
    _require(
        benchmark_contract["dataset_sha256"] == base_manifest["dataset_sha256"],
        "BASE benchmark is not pinned to the released BASE dataset",
    )

    _require(len(list((release_dir / "schemas/raw_data").glob("*.schema.json"))) == 25, "raw schema count differs")
    _require(len(list((release_dir / "schemas/required_outputs").glob("*.schema.json"))) == 14, "output schema count differs")
    _require(len(list((release_dir / "schemas/application_evidence").glob("*.schema.json"))) == 3, "application schema count differs")

    return {
        "files": len(relative_paths),
        "dataset_packages": len(package_ids),
        "dataset_csv_files": len(package_ids) * len(EXPECTED_RAW_FILES),
        "dataset_rows": package_rows,
        "required_outputs": len(config["output_contracts"]),
        "application_evidence_contracts": len(config["application_evidence_contracts"]),
    }


def validate_clean_room() -> dict[str, int]:
    config = load_config()
    drift = check_payloads(planned_payloads(config))
    _require(not drift, "; ".join(drift))
    with tempfile.TemporaryDirectory(prefix="cap001-release-check-") as temporary:
        isolated = Path(temporary) / "candidate-pack"
        shutil.copytree(RELEASE_ROOT, isolated)
        return validate_release(isolated)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, help="validate this release directory instead of an isolated copy")
    args = parser.parse_args(argv)
    try:
        summary = validate_release(args.release_dir) if args.release_dir else validate_clean_room()
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Professional release validation failed: {exc}", file=sys.stderr)
        return 1
    print("Professional release validation passed:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
