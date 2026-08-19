"""Tests for planning generation and complete dataset packages."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

from cap001_model.baseline import build_baseline_model
from cap001_model.data import load_model_data
from tooling.assess_dataset_packages import assess_paths
from tooling.contract_runtime import (
    EXPECTED_RAW_FILES,
    canonical_json,
    sha256_bytes,
    sha256_path,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_DIR = ROOT / "capstones" / "CAP-001" / "generator"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PLANNING = _load_module(
    "cap001_planning_generator", GENERATOR_DIR / "generate_planning_data.py"
)
PACKAGES = _load_module(
    "cap001_package_generator", GENERATOR_DIR / "generate_dataset_packages.py"
)


def _refresh_manifest(package_root: Path) -> None:
    manifest_path = package_root / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hashes = {}
    for file_name in EXPECTED_RAW_FILES:
        path = package_root / "data" / file_name
        hashes[file_name] = sha256_path(path)
        manifest["files"][file_name] = {
            "sha256": hashes[file_name],
            "bytes": path.stat().st_size,
        }
    manifest["dataset_sha256"] = sha256_bytes(
        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    )
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8", newline="")


def _issue_codes(assessment) -> set[str]:
    return {issue["code"] for issue in assessment.scorecard["issues"]}


def test_planning_candidate_has_relationship_derived_grains() -> None:
    candidate = PLANNING.build_candidate()
    assert {name: len(rows) for name, rows in candidate.tables.items()} == {
        "planning_calendar.csv": 12,
        "source_capacity.csv": 264,
        "transformation_capacity.csv": 624,
        "inventory_policies.csv": 159,
        "opening_inventory.csv": 48,
        "terminal_demand.csv": 288,
        "supplier_performance_history.csv": 2100,
        "incident_history.csv": 30,
    }
    assert candidate.evidence["derived_dimensions"] == {
        "pool_states": 159,
        "source_states": 22,
        "seller_states": 70,
        "terminal_streams": 24,
    }
    assert set(candidate.evidence["opening_inventory_by_tier"]) == {
        "PLANT",
        "TIER_1",
        "TIER_2",
        "TIER_3",
        "TIER_4",
    }
    assert candidate.evidence["opening_inventory_by_tier"]["TIER_4"] == 0


def test_planning_and_package_generation_are_reproducible_and_seed_sensitive() -> None:
    first = PLANNING.render_files(9042027)
    second = PLANNING.render_files(9042027)
    changed = PLANNING.render_files(9042028)
    assert first == second
    assert first["data/planning_calendar.csv"] == changed["data/planning_calendar.csv"]
    assert first["data/terminal_demand.csv"] != changed["data/terminal_demand.csv"]

    package_first = PACKAGES.render_files(9042027)
    package_second = PACKAGES.render_files(9042027)
    assert package_first == package_second
    assert (
        package_first["BASE/data/disruption_impacts.csv"]
        != package_first["SCN-01/data/disruption_impacts.csv"]
    )


def test_six_packages_are_complete_and_pass_all_depth_gates(tmp_path: Path) -> None:
    PACKAGES.write_files(tmp_path)
    assessment = assess_paths(tmp_path, solve_base=True)
    assert assessment.passed
    assert assessment.scorecard["issues"] == []
    assert all(metric["passed"] for metric in assessment.scorecard["metrics"])
    assert assessment.feasibility_summary["status"] == "PASS"
    assert assessment.feasibility_summary["unweighted_shortage"] < 1e-6
    assert not assessment.feasibility_summary["allocation_retained"]


def test_each_package_is_self_contained_and_has_one_scenario(tmp_path: Path) -> None:
    PACKAGES.write_files(tmp_path)
    for dataset_id in PACKAGES.DATASET_IDS:
        package = tmp_path / dataset_id
        assert {path.name for path in (package / "data").iterdir()} == set(
            EXPECTED_RAW_FILES
        )
        manifest = json.loads((package / "dataset_manifest.json").read_text())
        assert manifest["dataset_id"] == dataset_id
        assert manifest["scenario_id"] == dataset_id
        assert manifest["required_file_count"] == 26
        assert set(manifest["files"]) == set(EXPECTED_RAW_FILES)
        with (package / "data" / "disruption_scenarios.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 1
        assert rows[0]["scenario_id"] == dataset_id


def test_common_loader_resets_state_and_resolves_package_local_impacts(
    tmp_path: Path,
) -> None:
    PACKAGES.write_files(tmp_path)
    base = load_model_data(tmp_path / "BASE" / "data")
    source = load_model_data(tmp_path / "SCN-01" / "data")
    logistics = load_model_data(tmp_path / "SCN-02" / "data")
    combined = load_model_data(tmp_path / "SCN-05" / "data")
    source_key = ("NODE-0003", "MAT-0003", "P03")
    assert source.source_capacity[source_key]["regular_capacity"] == (
        base.source_capacity[source_key]["regular_capacity"] * 0.30
    )
    lane_base = next(
        route
        for route in base.shipment_routes.values()
        if route.lane_id == "LANE-00081" and route.dispatch_period_id == "P02"
    )
    lane_stress = next(
        route
        for route in logistics.shipment_routes.values()
        if route.lane_id == "LANE-00081" and route.dispatch_period_id == "P02"
    )
    assert lane_stress.capacity == lane_base.capacity * 0.75
    assert lane_stress.arrival_period_id > lane_base.arrival_period_id
    demand_key = ("NODE-0035", "MAT-0029", "P06")
    assert combined.demand[demand_key]["demand_quantity"] == (
        base.demand[demand_key]["demand_quantity"] * 1.10
    )
    reloaded = load_model_data(tmp_path / "BASE" / "data")
    assert reloaded.source_capacity[source_key] == base.source_capacity[source_key]
    assert reloaded.demand[demand_key] == base.demand[demand_key]


def test_missing_unchanged_file_is_not_loaded_from_another_package(
    tmp_path: Path,
) -> None:
    PACKAGES.write_files(tmp_path)
    (tmp_path / "SCN-03" / "data" / "fx_rates.csv").unlink()
    assessment = assess_paths(tmp_path, solve_base=False)
    assert not assessment.passed
    assert "PACKAGE_FILE_SET" in _issue_codes(assessment)
    assert (
        assessment.completeness_matrix["datasets"]["SCN-03"]["raw_files_present"] == 25
    )


def test_manifest_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    PACKAGES.write_files(tmp_path)
    path = tmp_path / "SCN-02" / "data" / "incident_history.csv"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assessment = assess_paths(tmp_path, solve_base=False)
    assert not assessment.passed
    assert {"MANIFEST_HASH", "DATASET_HASH"} <= _issue_codes(assessment)


def test_unknown_scenario_target_is_rejected_independently_of_manifest(
    tmp_path: Path,
) -> None:
    PACKAGES.write_files(tmp_path)
    package = tmp_path / "SCN-01"
    path = package / "data" / "disruption_impacts.csv"
    text = path.read_text(encoding="utf-8").replace("NODE-0003", "NODE-9999")
    path.write_text(text, encoding="utf-8", newline="")
    _refresh_manifest(package)
    assessment = assess_paths(tmp_path, solve_base=False)
    assert not assessment.passed
    assert "UNKNOWN_IMPACT_TARGET" in _issue_codes(assessment)


def test_missing_recovery_is_rejected(tmp_path: Path) -> None:
    PACKAGES.write_files(tmp_path)
    package = tmp_path / "SCN-03"
    path = package / "data" / "disruption_impacts.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    rows = [row for row in rows if row["start_period_id"] != "P06"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _refresh_manifest(package)
    assessment = assess_paths(tmp_path, solve_base=False)
    assert not assessment.passed
    assert "MISSING_RECOVERY" in _issue_codes(assessment)


def test_approval_share_cap_aggregates_transport_modes(tmp_path: Path) -> None:
    PACKAGES.write_files(tmp_path)
    data = load_model_data(tmp_path / "BASE" / "data")
    baseline = build_baseline_model(data)
    expected = {
        (route.approval_id, route.dispatch_period_id)
        for route in data.shipment_routes.values()
        if route.maximum_approved_share is not None
    }
    assert len(baseline.model.maximum_approved_share) == len(expected)
    paired = [
        route
        for route in data.shipment_routes.values()
        if route.lane_id in {"LANE-00081", "LANE-00111"}
        and route.dispatch_period_id == "P01"
    ]
    assert len({route.lane_id for route in paired}) == 2
    assert len({route.approval_id for route in paired}) >= 1
