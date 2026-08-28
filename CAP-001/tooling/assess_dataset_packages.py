#!/usr/bin/env python3
"""Validate CAP-001 planning depth and complete dataset packages."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pyomo.environ as pyo  # noqa: E402

from cap001_model.physical_seed import build_physical_seed_model  # noqa: E402
from cap001_model.data import load_model_data  # noqa: E402
from cap001_model.solvers import HighsSolverAdapter  # noqa: E402
from tooling.contract_runtime import (  # noqa: E402
    EXPECTED_RAW_FILES,
    ContractError,
    canonical_json,
    coerce_csv_value,
    load_config,
    sha256_bytes,
    sha256_path,
    validate_csv_file,
)


DEFAULT_DATASET_DIR = ROOT / "generated" / "datasets"
DATASET_IDS = ("BASE", "SCN-01", "SCN-02", "SCN-03", "SCN-04", "SCN-05")


@dataclass(frozen=True)
class Assessment:
    scorecard: dict[str, Any]
    completeness_matrix: dict[str, Any]
    planning_witnesses: dict[str, Any]
    scenario_witnesses: dict[str, Any]
    feasibility_summary: dict[str, Any]
    report: str

    @property
    def passed(self) -> bool:
        return self.scorecard["status"] == "PASS"


def _issue(
    issues: list[dict[str, Any]],
    code: str,
    message: str,
    entities: Iterable[str] = (),
) -> None:
    issues.append({"code": code, "message": message, "entities": sorted(set(entities))})


def _metric(
    metric_id: str,
    label: str,
    value: int | float,
    threshold: str,
    passed: bool,
    *,
    witnesses: Iterable[str] = (),
    failures: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "label": label,
        "value": value,
        "threshold": threshold,
        "passed": passed,
        "witnesses": sorted(set(witnesses)),
        "failures": sorted(set(failures)),
    }


def _read_table(path: Path, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    validate_csv_file(path, contract)
    fields = {field["name"]: field for field in contract["columns"]}
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {name: coerce_csv_value(value, fields[name]) for name, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def _load_package(
    package_root: Path,
    config: Mapping[str, Any],
    issues: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    dataset_id = package_root.name
    data_dir = package_root / "data"
    manifest_path = package_root / "dataset_manifest.json"
    if package_root.is_symlink() or data_dir.is_symlink():
        _issue(
            issues,
            "PACKAGE_SYMLINK",
            "Dataset roots and data roots must be real directories",
            [dataset_id],
        )
        return {}, {}
    if not data_dir.is_dir() or not manifest_path.is_file():
        _issue(
            issues,
            "PACKAGE_LAYOUT",
            "Dataset package is missing its data directory or manifest",
            [dataset_id],
        )
        return {}, {}
    symlinks = [path.name for path in data_dir.iterdir() if path.is_symlink()]
    if symlinks:
        _issue(
            issues,
            "PACKAGE_SYMLINK",
            "Raw files must not be symlinks",
            [f"{dataset_id}/{name}" for name in symlinks],
        )
    actual = {path.name for path in data_dir.iterdir() if path.is_file()}
    expected = set(EXPECTED_RAW_FILES)
    if actual != expected:
        _issue(
            issues,
            "PACKAGE_FILE_SET",
            "Dataset package must contain exactly the 25 raw CSV files",
            [f"{dataset_id}/{name}" for name in sorted(actual ^ expected)],
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _issue(issues, "MANIFEST_INVALID", str(exc), [dataset_id])
        return {}, {}
    if (
        manifest.get("dataset_id") != dataset_id
        or manifest.get("source_package_id") != dataset_id
        or manifest.get("package_semantics") != "COMPLETE_DATASET"
        or manifest.get("information_available_at_period") != "P01"
        or manifest.get("complete_horizon_known_at_p01") is not True
    ):
        _issue(
            issues,
            "MANIFEST_IDENTITY",
            "Manifest identity and complete-horizon package semantics must match its package directory",
            [dataset_id],
        )
    if manifest.get("required_file_count") != len(EXPECTED_RAW_FILES):
        _issue(
            issues,
            "MANIFEST_FILE_COUNT",
            "Manifest required-file count drifted",
            [dataset_id],
        )
    manifest_files = manifest.get("files", {})
    if set(manifest_files) != expected:
        _issue(
            issues,
            "MANIFEST_FILE_SET",
            "Manifest must enumerate every raw file",
            [dataset_id],
        )
    hashes: dict[str, str] = {}
    tables: dict[str, list[dict[str, Any]]] = {}
    for file_name in EXPECTED_RAW_FILES:
        path = data_dir / file_name
        if not path.is_file() or path.is_symlink():
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(data_dir.resolve())
        except ValueError:
            _issue(
                issues,
                "PACKAGE_ESCAPE",
                "Raw file resolves outside its package data root",
                [f"{dataset_id}/{file_name}"],
            )
            continue
        actual_hash = sha256_path(path)
        hashes[file_name] = actual_hash
        if manifest_files.get(file_name, {}).get("sha256") != actual_hash:
            _issue(
                issues,
                "MANIFEST_HASH",
                "Raw file hash does not match the manifest",
                [f"{dataset_id}/{file_name}"],
            )
        try:
            tables[file_name] = _read_table(path, config["raw_contracts"][file_name])
        except (ContractError, ValueError) as exc:
            _issue(issues, "SCHEMA_VALIDATION", str(exc), [f"{dataset_id}/{file_name}"])
    if len(hashes) == len(EXPECTED_RAW_FILES):
        aggregate = sha256_bytes(
            json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
        )
        if manifest.get("dataset_sha256") != aggregate:
            _issue(
                issues,
                "DATASET_HASH",
                "Aggregate dataset hash does not match file hashes",
                [dataset_id],
            )
    return tables, manifest


def _duplicates(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> list[str]:
    counts = Counter(tuple(row[field] for field in fields) for row in rows)
    return [
        "/".join(str(value) for value in key)
        for key, count in counts.items()
        if count > 1
    ]


def _validate_relations(
    dataset_id: str,
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    config: Mapping[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    if set(tables) != set(EXPECTED_RAW_FILES):
        return
    for file_name, contract in config["raw_contracts"].items():
        primary_key = contract.get("primary_key", [])
        if primary_key:
            duplicates = _duplicates(tables[file_name], primary_key)
            if duplicates:
                _issue(
                    issues,
                    "DUPLICATE_PRIMARY_KEY",
                    f"{file_name} contains duplicate primary keys",
                    [f"{dataset_id}/{value}" for value in duplicates],
                )
        for unique_key in contract.get("unique_keys", []):
            duplicates = _duplicates(tables[file_name], unique_key)
            if duplicates:
                _issue(
                    issues,
                    "DUPLICATE_UNIQUE_KEY",
                    f"{file_name} contains duplicate unique keys",
                    [f"{dataset_id}/{value}" for value in duplicates],
                )
        for foreign_key in contract.get("foreign_keys", []):
            target_file, target_column = foreign_key["references"].rsplit(".", 1)
            allowed = {row[target_column] for row in tables[target_file]}
            column = foreign_key["column"]
            unknown = {
                str(row[column])
                for row in tables[file_name]
                if row[column] is not None and row[column] not in allowed
            }
            if unknown:
                _issue(
                    issues,
                    "FOREIGN_KEY",
                    f"{file_name}.{column} references unknown values",
                    [f"{dataset_id}/{value}" for value in unknown],
                )


def _derived_sets(tables: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    nodes = {row["node_id"]: row for row in tables["network_nodes.csv"]}
    recipes = {
        row["recipe_id"]: row
        for row in tables["transformation_recipes.csv"]
        if row["active_flag"]
    }
    approvals = [
        row
        for row in tables["material_flow_approvals.csv"]
        if row["approval_status"] == "APPROVED"
    ]
    pools = {(row["seller_node_id"], row["material_id"]) for row in approvals} | {
        (row["buyer_node_id"], row["material_id"]) for row in approvals
    }
    pools |= {(row["node_id"], row["output_material_id"]) for row in recipes.values()}
    pools |= {
        (recipes[row["recipe_id"]]["node_id"], row["input_material_id"])
        for row in tables["transformation_inputs.csv"]
    }
    sources = {
        (row["seller_node_id"], row["material_id"])
        for row in approvals
        if nodes[row["seller_node_id"]]["external_boundary_flag"]
    }
    terminals = {
        (row["buyer_node_id"], row["material_id"])
        for row in approvals
        if nodes[row["buyer_node_id"]]["node_tier"] == "PLANT"
    }
    sellers = {(row["seller_node_id"], row["material_id"]) for row in approvals}
    return {
        "nodes": nodes,
        "recipes": recipes,
        "approvals": approvals,
        "pools": pools,
        "sources": sources,
        "terminals": terminals,
        "sellers": sellers,
    }


def _validate_calendar(
    dataset_id: str,
    rows: Sequence[Mapping[str, Any]],
    issues: list[dict[str, Any]],
) -> bool:
    ordered = sorted(rows, key=lambda row: row["period_number"])
    expected_start = date(2027, 1, 4)
    valid = len(ordered) == 12
    for offset, row in enumerate(ordered):
        start = date.fromisoformat(row["week_start_date"])
        end = date.fromisoformat(row["week_end_date"])
        valid &= row["period_id"] == f"P{offset + 1:02d}"
        valid &= row["period_number"] == offset + 1
        valid &= start == expected_start + timedelta(weeks=offset)
        valid &= end == start + timedelta(days=6)
        valid &= row["is_terminal_period"] == (offset == 11)
    if not valid:
        _issue(
            issues,
            "CALENDAR_SEQUENCE",
            "Planning calendar is not the controlled contiguous twelve-week horizon",
            [dataset_id],
        )
    return valid


def _validate_planning_facts(
    dataset_id: str,
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    sets = _derived_sets(tables)
    periods = {row["period_id"] for row in tables["planning_calendar.csv"]}
    source_keys = {
        (row["node_id"], row["material_id"], row["period_id"])
        for row in tables["source_capacity.csv"]
    }
    expected_source = {
        (*state, period) for state in sets["sources"] for period in periods
    }
    recipe_keys = {
        (row["recipe_id"], row["period_id"])
        for row in tables["transformation_capacity.csv"]
    }
    expected_recipe = {
        (recipe, period) for recipe in sets["recipes"] for period in periods
    }
    policy_keys = {
        (row["node_id"], row["material_id"]) for row in tables["inventory_policies.csv"]
    }
    demand_keys = {
        (row["plant_id"], row["material_id"], row["period_id"])
        for row in tables["terminal_demand.csv"]
    }
    expected_demand = {
        (*state, period) for state in sets["terminals"] for period in periods
    }
    history_months = {
        row["month"] for row in tables["supplier_performance_history.csv"]
    }
    history_keys = {
        (row["node_id"], row["material_id"], row["month"])
        for row in tables["supplier_performance_history.csv"]
    }
    expected_history = {
        (*state, month) for state in sets["sellers"] for month in history_months
    }
    coverage = {
        "calendar": _validate_calendar(
            dataset_id, tables["planning_calendar.csv"], issues
        ),
        "source": source_keys == expected_source,
        "transformation": recipe_keys == expected_recipe,
        "inventory": policy_keys == sets["pools"],
        "demand": demand_keys == expected_demand,
        "history": len(history_months) == 30 and history_keys == expected_history,
    }
    for name, passed in coverage.items():
        if not passed:
            _issue(
                issues,
                f"{name.upper()}_COVERAGE",
                f"{name} facts do not cover their derived grain",
                [dataset_id],
            )
    policies = {
        (row["node_id"], row["material_id"]): row
        for row in tables["inventory_policies.csv"]
    }
    for row in policies.values():
        if row["safety_stock_quantity"] > row["maximum_storage_quantity"]:
            _issue(
                issues,
                "SAFETY_ABOVE_STORAGE",
                "Safety stock exceeds maximum storage",
                [f"{dataset_id}/{row['node_id']}|{row['material_id']}"],
            )
        if not row["allow_inventory_flag"] and row["maximum_storage_quantity"] != 0:
            _issue(
                issues,
                "DISALLOWED_STORAGE",
                "A no-inventory state has positive storage",
                [f"{dataset_id}/{row['node_id']}|{row['material_id']}"],
            )
    for row in tables["opening_inventory.csv"]:
        key = (row["node_id"], row["material_id"])
        if not math.isclose(
            row["usable_quantity"],
            row["on_hand_quantity"] - row["reserved_quantity"],
            abs_tol=1e-7,
        ):
            _issue(
                issues,
                "OPENING_QUANTITY_IDENTITY",
                "Opening usable quantity identity failed",
                [f"{dataset_id}/{key[0]}|{key[1]}"],
            )
        if not math.isclose(
            row["opening_total_value_eur"],
            row["usable_quantity"] * row["opening_unit_cost_eur"],
            abs_tol=1e-5,
        ):
            _issue(
                issues,
                "OPENING_VALUE_IDENTITY",
                "Opening inventory value identity failed",
                [f"{dataset_id}/{key[0]}|{key[1]}"],
            )
        if key not in policies or not policies[key]["allow_inventory_flag"]:
            _issue(
                issues,
                "OPENING_STORAGE_POLICY",
                "Opening inventory is not permitted by its pool policy",
                [f"{dataset_id}/{key[0]}|{key[1]}"],
            )
    for row in tables["supplier_performance_history.csv"]:
        if not (
            row["accepted_quantity"]
            <= row["received_quantity"] + 1e-7
            <= row["ordered_quantity"] + 1e-7
        ):
            _issue(
                issues,
                "HISTORY_QUANTITY_IDENTITY",
                "Historical accepted/received/ordered quantities are inconsistent",
                [f"{dataset_id}/{row['node_id']}|{row['material_id']}|{row['month']}"],
            )
        if row["on_time_quantity"] > row["received_quantity"] + 1e-7:
            _issue(
                issues,
                "HISTORY_ONTIME_IDENTITY",
                "Historical on-time quantity exceeds receipts",
                [f"{dataset_id}/{row['node_id']}|{row['material_id']}|{row['month']}"],
            )
    shared_rows: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in tables["transformation_capacity.csv"]:
        group_id = row["shared_capacity_group_id"]
        coefficient = row["shared_capacity_coefficient"]
        if (group_id is None) != (coefficient is None):
            _issue(
                issues,
                "SHARED_CAPACITY_FIELDS",
                "Shared capacity group and coefficient must be populated together",
                [f"{dataset_id}/{row['recipe_id']}|{row['period_id']}"],
            )
        if group_id is not None:
            shared_rows[(group_id, row["period_id"])].append(row)
    for (group_id, period_id), rows in shared_rows.items():
        signatures = {
            (
                row["regular_output_capacity"],
                row["surge_output_capacity"],
                row["planned_downtime_fraction"],
            )
            for row in rows
        }
        if len(rows) < 2 or len(signatures) != 1:
            _issue(
                issues,
                "SHARED_CAPACITY_LIMIT",
                "A shared group-period must repeat one common limit across multiple recipes",
                [f"{dataset_id}/{group_id}|{period_id}"],
            )
    return {**coverage, "sets": sets}


def _validate_scenario(
    dataset_id: str,
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    scenarios = list(tables["disruption_scenarios.csv"])
    impacts = list(tables["disruption_impacts.csv"])
    if (
        len(scenarios) != 1
        or scenarios[0]["scenario_id"] != dataset_id
        or not scenarios[0]["active_flag"]
    ):
        _issue(
            issues,
            "SCENARIO_IDENTITY",
            "Package must contain one active scenario row matching its directory",
            [dataset_id],
        )
    if dataset_id == "BASE" and impacts:
        _issue(
            issues,
            "BASE_IMPACTS",
            "BASE disruption impacts must be header-only",
            [dataset_id],
        )
    if any(row["scenario_id"] != dataset_id for row in impacts):
        _issue(
            issues,
            "IMPACT_OWNERSHIP",
            "Every impact must belong to its package scenario",
            [dataset_id],
        )
    periods = {row["period_id"] for row in tables["planning_calendar.csv"]}
    nodes = {row["node_id"] for row in tables["network_nodes.csv"]}
    organisations = {row["supplier_id"] for row in tables["supplier_organisations.csv"]}
    parents = {
        row["parent_group_id"]
        for row in tables["supplier_organisations.csv"]
        if row["parent_group_id"]
    }
    regions = {row["region_code"] for row in tables["network_nodes.csv"]}
    lanes = {row["lane_id"] for row in tables["shipping_lanes.csv"]}
    recipes = {row["recipe_id"] for row in tables["transformation_recipes.csv"]}
    materials = {row["material_id"] for row in tables["materials.csv"]}
    terminal_keys = {
        f"{row['plant_id']}|{row['material_id']}"
        for row in tables["terminal_demand.csv"]
    }
    domains = {
        "NODE": nodes,
        "ORGANISATION": organisations,
        "PARENT_GROUP": parents,
        "REGION": regions,
        "LANE": lanes,
        "RECIPE": recipes,
        "MATERIAL": materials,
        "TERMINAL_DEMAND": terminal_keys,
    }
    period_number = {
        row["period_id"]: row["period_number"]
        for row in tables["planning_calendar.csv"]
    }
    affected: set[str] = set()
    disruptive_targets: set[tuple[str, str]] = set()
    recovery_targets: set[tuple[str, str]] = set()
    replacements: dict[tuple[str, str, str, str, int], int] = Counter()
    for row in impacts:
        entity_type = row["target_entity_type"]
        target_id = row["target_entity_id"]
        if entity_type in domains and target_id not in domains[entity_type]:
            _issue(
                issues,
                "UNKNOWN_IMPACT_TARGET",
                "Impact target does not resolve within its package",
                [f"{dataset_id}/{entity_type}/{target_id}"],
            )
        if (
            row["start_period_id"] not in periods
            or row["end_period_id"] not in periods
            or period_number.get(row["start_period_id"], 99)
            > period_number.get(row["end_period_id"], -1)
        ):
            _issue(
                issues,
                "IMPACT_PERIOD",
                "Impact period window is invalid",
                [f"{dataset_id}/{row['impact_id']}"],
            )
        if not row["availability_flag"] and (
            row["capacity_multiplier"] != 0 or row["lane_capacity_multiplier"] != 1
        ):
            _issue(
                issues,
                "AVAILABILITY_PRECEDENCE",
                "Unavailable targets must use zero capacity and neutral lane multiplier",
                [f"{dataset_id}/{row['impact_id']}"],
            )
        changed = (
            not row["availability_flag"]
            or row["capacity_multiplier"] != 1
            or row["lane_capacity_multiplier"] != 1
            or row["transit_time_multiplier"] != 1
            or row["cost_multiplier"] != 1
            or row["demand_multiplier"] != 1
            or row["replacement_field"] is not None
        )
        key = (entity_type, target_id)
        (disruptive_targets if changed else recovery_targets).add(key)
        if changed:
            affected.add(f"{entity_type}:{target_id}")
        if row["replacement_field"] is not None:
            replacement_key = (
                entity_type,
                target_id,
                row["start_period_id"],
                row["replacement_field"],
                row["impact_priority"],
            )
            replacements[replacement_key] += 1
    ties = ["|".join(map(str, key)) for key, count in replacements.items() if count > 1]
    if ties:
        _issue(
            issues,
            "REPLACEMENT_PRIORITY_TIE",
            "Replacement impacts tie at the winning priority",
            [f"{dataset_id}/{tie}" for tie in ties],
        )
    missing_recovery = disruptive_targets - recovery_targets
    if missing_recovery:
        _issue(
            issues,
            "MISSING_RECOVERY",
            "Every controlled disruptive target requires an explicit recovery row",
            [f"{dataset_id}/{kind}:{target}" for kind, target in missing_recovery],
        )
    changed_rows = [
        row
        for row in impacts
        if (
            not row["availability_flag"]
            or row["capacity_multiplier"] != 1
            or row["lane_capacity_multiplier"] != 1
            or row["transit_time_multiplier"] != 1
            or row["cost_multiplier"] != 1
            or row["demand_multiplier"] != 1
        )
    ]
    exact = True
    if dataset_id in {"SCN-01", "SCN-05"}:
        source_rows = [
            row
            for row in impacts
            if row["target_entity_type"] == "NODE"
            and row["target_entity_id"] == "NODE-0005"
            and row["target_material_id"] == "MAT-0005"
            and (
                not row["availability_flag"]
                or row["capacity_multiplier"] != 1
            )
        ]
        exact &= {
            (
                row["start_period_id"],
                row["end_period_id"],
                row["availability_flag"],
                row["capacity_multiplier"],
            )
            for row in source_rows
        } == {
            ("P01", "P03", True, 0.07),
            ("P04", "P05", True, 0.50),
        }
    if dataset_id in {"SCN-02", "SCN-05"}:
        lane_rows = [row for row in changed_rows if row["target_entity_type"] == "LANE"]
        exact &= len(lane_rows) == 5 and all(
            row["start_period_id"] == "P02"
            and row["end_period_id"] == "P07"
            and row["lane_capacity_multiplier"] == 0.75
            and row["transit_time_multiplier"] == 1.75
            and row["cost_multiplier"] == 1.40
            for row in lane_rows
        )
    if dataset_id == "SCN-03":
        node_rows = [
            row
            for row in impacts
            if row["target_entity_type"] == "NODE"
            and row["target_entity_id"] == "NODE-0030"
        ]
        exact &= any(
            row["start_period_id"] == "P04"
            and row["end_period_id"] == "P04"
            and not row["availability_flag"]
            and row["capacity_multiplier"] == 0
            for row in node_rows
        ) and any(
            row["start_period_id"] == "P05"
            and row["end_period_id"] == "P05"
            and row["capacity_multiplier"] == 0.50
            for row in node_rows
        )
    if dataset_id == "SCN-04":
        regional_rows = [
            row for row in changed_rows if row["target_entity_type"] == "NODE"
        ]
        exact &= len(regional_rows) == 5 and {
            row["target_entity_id"] for row in regional_rows
        } == {"NODE-0002", "NODE-0005", "NODE-0015", "NODE-0024", "NODE-0027"}
        exact &= sum(
            row["target_entity_id"] == "NODE-0027"
            and row["capacity_multiplier"] == 0.10
            for row in regional_rows
        ) == 1
        exact &= all(
            0.35 <= row["capacity_multiplier"] <= 0.50
            for row in regional_rows
            if row["target_entity_id"] != "NODE-0027"
        )
    if dataset_id == "SCN-05":
        uplift_rows = [
            row
            for row in changed_rows
            if row["target_entity_type"] == "TERMINAL_DEMAND"
        ]
        exact &= len(uplift_rows) == 8 and all(
            row["start_period_id"] == "P06"
            and row["end_period_id"] == "P10"
            and 1.10 <= row["demand_multiplier"] <= 1.15
            for row in uplift_rows
        )
    if dataset_id == "BASE":
        exact &= not impacts
    if not exact:
        _issue(
            issues,
            "SCENARIO_PROFILE",
            "Controlled scenario periods, targets or multipliers drifted",
            [dataset_id],
        )
    return {
        "impact_rows": len(impacts),
        "affected_targets": sorted(affected),
        "recovery_targets": len(recovery_targets),
        "controlled_profile_matches": exact,
    }


def _planning_depth(
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    sets = _derived_sets(tables)
    demand_by_stream: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in sorted(tables["terminal_demand.csv"], key=lambda row: row["period_id"]):
        demand_by_stream[(row["plant_id"], row["material_id"])].append(
            row["demand_quantity"]
        )
    varying = [
        "|".join(key)
        for key, values in demand_by_stream.items()
        if len(set(values)) > 1
    ]
    peaks = [
        "|".join(key)
        for key, values in demand_by_stream.items()
        if max(values) >= statistics.median(values) * 1.25
    ]
    nodes = sets["nodes"]
    opening_tiers = Counter(
        nodes[row["node_id"]]["node_tier"]
        for row in tables["opening_inventory.csv"]
        if row["usable_quantity"] > 0
    )
    groups: dict[str, set[str]] = defaultdict(set)
    for row in tables["transformation_capacity.csv"]:
        if row["shared_capacity_group_id"]:
            groups[row["shared_capacity_group_id"]].add(row["recipe_id"])
    multi_groups = {
        group: recipes for group, recipes in groups.items() if len(recipes) >= 2
    }
    partial = sum(
        row["source_completeness_flag"] == "PARTIAL"
        for row in tables["supplier_performance_history.csv"]
    )
    history_count = len(tables["supplier_performance_history.csv"])
    history_by_state: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in tables["supplier_performance_history.csv"]:
        history_by_state[(row["node_id"], row["material_id"])].append(row)
    pools: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for row in sets["approvals"]:
        pools[(row["buyer_node_id"], row["material_id"])].append(
            (row["seller_node_id"], row["material_id"])
        )
    contrasts = []
    for pool, seller_states in pools.items():
        if len(set(seller_states)) < 2:
            continue
        rates = []
        for state in set(seller_states):
            rows = history_by_state[state]
            received = sum(row["received_quantity"] for row in rows)
            rates.append(sum(row["on_time_quantity"] for row in rows) / received)
        if max(rates) - min(rates) >= 0.03:
            contrasts.append("|".join(pool))
    pressure = []
    pressure.extend(
        f"SOURCE:{row['node_id']}|{row['material_id']}|{row['period_id']}"
        for row in tables["source_capacity.csv"]
        if row["planned_downtime_fraction"] > 0
    )
    pressure.extend(f"SHARED:{group}" for group in multi_groups)
    pressure.extend(f"DEMAND:{stream}" for stream in peaks)
    contracts = {row["approval_id"]: row for row in tables["supply_contracts.csv"]}
    standard_lanes: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in tables["shipping_lanes.csv"]:
        if row["active_flag"] and not row["expedited_flag"]:
            standard_lanes[(row["origin_node_id"], row["destination_node_id"])].append(
                row
            )
    advance_dispatch_streams = set()
    for approval in sets["approvals"]:
        stream = (approval["buyer_node_id"], approval["material_id"])
        if stream not in sets["terminals"]:
            continue
        contract = contracts[approval["approval_id"]]
        for lane in standard_lanes[
            (approval["seller_node_id"], approval["buyer_node_id"])
        ]:
            lead = math.ceil(
                (contract["contract_handling_days"] + lane["base_transit_days"]) / 7
            )
            if lead >= 2:
                advance_dispatch_streams.add("|".join(stream))
    return {
        "varying_demand_streams": varying,
        "peak_demand_streams": peaks,
        "positive_opening_states": len(tables["opening_inventory.csv"]),
        "opening_states_by_tier": dict(sorted(opening_tiers.items())),
        "shared_capacity_groups": {
            key: sorted(value) for key, value in sorted(multi_groups.items())
        },
        "partial_history_rows": partial,
        "partial_history_fraction": partial / history_count,
        "historical_contrast_pools": contrasts,
        "pressure_witnesses": pressure[:80],
        "advance_standard_dispatch_streams": sorted(advance_dispatch_streams),
    }


def _scenario_depth(
    package_tables: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
) -> dict[str, Any]:
    base = package_tables["BASE"]
    nodes = {row["node_id"]: row for row in base["network_nodes.csv"]}
    recipes = {row["recipe_id"]: row for row in base["transformation_recipes.csv"]}
    state_graph: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for approval in base["material_flow_approvals.csv"]:
        state_graph[(approval["seller_node_id"], approval["material_id"])].add(
            (approval["buyer_node_id"], approval["material_id"])
        )
    for recipe_input in base["transformation_inputs.csv"]:
        recipe = recipes[recipe_input["recipe_id"]]
        state_graph[(recipe["node_id"], recipe_input["input_material_id"])].add(
            (recipe["node_id"], recipe["output_material_id"])
        )
    start = ("NODE-0005", "MAT-0005")
    frontier = [start]
    reachable = {start}
    while frontier:
        state = frontier.pop()
        for downstream in state_graph.get(state, set()):
            if downstream not in reachable:
                reachable.add(downstream)
                frontier.append(downstream)
    scn01_terminals = {
        material_id
        for node_id, material_id in reachable
        if nodes[node_id]["node_tier"] == "PLANT"
    }
    lanes = {row["lane_id"]: row for row in base["shipping_lanes.csv"]}
    pairs = defaultdict(list)
    for lane in lanes.values():
        pairs[(lane["origin_node_id"], lane["destination_node_id"])].append(lane)
    scn2_lanes = {
        row["target_entity_id"]
        for row in package_tables["SCN-02"]["disruption_impacts.csv"]
        if row["target_entity_type"] == "LANE"
        and (
            row["lane_capacity_multiplier"] != 1
            or row["transit_time_multiplier"] != 1
            or row["cost_multiplier"] != 1
        )
    }
    retained_expedited = []
    for lane_id in scn2_lanes:
        lane = lanes[lane_id]
        alternatives = pairs[(lane["origin_node_id"], lane["destination_node_id"])]
        if any(
            candidate["expedited_flag"] and candidate["active_flag"]
            for candidate in alternatives
        ):
            retained_expedited.append(lane_id)
    approvals = base["material_flow_approvals.csv"]
    node30_streams = {
        (row["buyer_node_id"], row["material_id"])
        for row in approvals
        if row["seller_node_id"] == "NODE-0030"
        and nodes[row["buyer_node_id"]]["node_tier"] == "PLANT"
    }
    node30_alternates = {
        stream
        for stream in node30_streams
        if any(
            row["buyer_node_id"] == stream[0]
            and row["material_id"] == stream[1]
            and row["seller_node_id"] != "NODE-0030"
            for row in approvals
        )
    }
    regional_nodes = {
        row["target_entity_id"]
        for row in package_tables["SCN-04"]["disruption_impacts.csv"]
        if row["target_entity_type"] == "NODE" and row["capacity_multiplier"] != 1
    }
    uplift = [
        row
        for row in package_tables["SCN-05"]["disruption_impacts.csv"]
        if row["target_entity_type"] == "TERMINAL_DEMAND"
        and row["demand_multiplier"] != 1
    ]
    return {
        "scn01_terminal_materials": sorted(scn01_terminals),
        "scn02_standard_lanes_with_expedited_alternative": sorted(retained_expedited),
        "scn03_streams_with_alternate": sorted(
            "|".join(stream) for stream in node30_alternates
        ),
        "scn04_nodes": sorted(regional_nodes),
        "scn04_tiers": sorted(
            {nodes[node_id]["node_tier"] for node_id in regional_nodes}
        ),
        "scn05_demand_uplifts": [
            {
                "stream": row["target_entity_id"],
                "multiplier": row["demand_multiplier"],
                "periods": f"{row['start_period_id']}..{row['end_period_id']}",
            }
            for row in uplift
        ],
    }


def _model_checks(
    dataset_dir: Path,
    issues: list[dict[str, Any]],
    *,
    solve_base: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    constructions = {}
    base_data = None
    base_model = None
    for dataset_id in DATASET_IDS:
        try:
            data = load_model_data(dataset_dir / dataset_id / "data")
            model = build_physical_seed_model(data)
            constructions[dataset_id] = {
                "pools": len(data.pool_keys),
                "routes": len(data.shipment_routes),
                "variables": model.model.nvariables(),
                "constraints": model.model.nconstraints(),
                "scenario_id": next(
                    row["scenario_id"]
                    for row in data.rows("disruption_scenarios.csv")
                    if row["active_flag"]
                ),
            }
            if dataset_id == "BASE":
                base_data, base_model = data, model
        except Exception as exc:  # controlled assessment evidence
            _issue(issues, "COMMON_MODEL_CONSTRUCTION", str(exc), [dataset_id])
    feasibility = {
        "status": "NOT_RUN" if not solve_base else "FAIL",
        "weighted_shortage": None,
        "unweighted_shortage": None,
        "solver": None,
        "termination": None,
        "runtime_budget_seconds": 45,
        "completed_within_budget": None,
        "allocation_retained": False,
        "boundary_source_dependency": {
            "status": "NOT_RUN" if not solve_base else "FAIL",
            "solver": None,
            "termination": None,
            "runtime_budget_seconds": 15,
            "completed_within_budget": None,
            "zero_shortage_without_boundary_source": None,
        },
    }
    if solve_base and base_data is not None and base_model is not None:
        evidence = HighsSolverAdapter().solve(
            base_model.model,
            time_limit_seconds=45,
            options={"mip_rel_gap": 0.0, "time_limit": 45},
        )
        feasibility.update(
            {
                "status": "PASS" if evidence.has_solution else "FAIL",
                "solver": evidence.solver_name,
                "solver_version": evidence.solver_version,
                "termination": evidence.raw_termination_condition,
                "completed_within_budget": evidence.runtime_seconds <= 45,
            }
        )
        if evidence.has_solution:
            weighted = float(pyo.value(base_model.model.stage_1_objective.expr))
            shortage = sum(
                float(pyo.value(base_model.model.shortage[key]))
                for key in base_model.model.DEMAND
            )
            if abs(weighted) <= 1e-6:
                weighted = 0.0
            if abs(shortage) <= 1e-6:
                shortage = 0.0
            feasibility["weighted_shortage"] = weighted
            feasibility["unweighted_shortage"] = shortage
            feasibility["status"] = "PASS" if shortage <= 1e-6 else "FAIL"
        if feasibility["status"] != "PASS":
            _issue(
                issues,
                "BASE_FEASIBILITY",
                "BASE did not produce a zero-shortage physical MILP witness",
                [str(feasibility)],
            )
        dependency_model = build_physical_seed_model(base_data).model
        for objective in dependency_model.component_objects(pyo.Objective, active=True):
            objective.deactivate()
        dependency_model.zero_shortage = pyo.Constraint(
            expr=sum(
                dependency_model.shortage[key] for key in dependency_model.DEMAND
            )
            <= 1e-6
        )
        dependency_model.no_boundary_source = pyo.Constraint(
            expr=sum(
                dependency_model.source_supply[key] for key in dependency_model.SOURCE
            )
            == 0
        )
        dependency_model.feasibility_objective = pyo.Objective(expr=0.0)
        dependency_evidence = HighsSolverAdapter().solve(
            dependency_model,
            time_limit_seconds=15,
            options={"mip_rel_gap": 0.0, "time_limit": 15},
        )
        source_dependency = feasibility["boundary_source_dependency"]
        source_dependency.update(
            {
                "status": (
                    "PASS"
                    if dependency_evidence.status.value == "infeasible"
                    else "FAIL"
                ),
                "solver": dependency_evidence.solver_name,
                "solver_version": dependency_evidence.solver_version,
                "termination": dependency_evidence.raw_termination_condition,
                "completed_within_budget": dependency_evidence.runtime_seconds <= 15,
                "zero_shortage_without_boundary_source": (
                    False
                    if dependency_evidence.status.value == "infeasible"
                    else dependency_evidence.has_solution
                ),
            }
        )
        if source_dependency["status"] != "PASS":
            _issue(
                issues,
                "BOUNDARY_SOURCE_DEPENDENCY",
                "BASE did not prove that zero shortage requires boundary sourcing",
                [str(source_dependency)],
            )
    return constructions, feasibility


def assess_paths(
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    *,
    solve_base: bool = True,
) -> Assessment:
    config = load_config()
    issues: list[dict[str, Any]] = []
    package_tables: dict[str, dict[str, list[dict[str, Any]]]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    completeness = {"datasets": {}}
    for dataset_id in DATASET_IDS:
        package_root = dataset_dir / dataset_id
        tables, manifest = _load_package(package_root, config, issues)
        package_tables[dataset_id] = tables
        manifests[dataset_id] = manifest
        completeness["datasets"][dataset_id] = {
            "raw_files_present": len(tables),
            "required_raw_files": len(EXPECTED_RAW_FILES),
            "dataset_sha256": manifest.get("dataset_sha256"),
            "complete": len(tables) == len(EXPECTED_RAW_FILES),
        }
        _validate_relations(dataset_id, tables, config, issues)
    coverage = {}
    scenario_profiles = {}
    for dataset_id, tables in package_tables.items():
        if set(tables) != set(EXPECTED_RAW_FILES):
            continue
        coverage[dataset_id] = _validate_planning_facts(dataset_id, tables, issues)
        scenario_profiles[dataset_id] = _validate_scenario(dataset_id, tables, issues)
    base_tables = package_tables.get("BASE", {})
    planning_depth = (
        _planning_depth(base_tables)
        if set(base_tables) == set(EXPECTED_RAW_FILES)
        else {}
    )
    scenario_depth = (
        _scenario_depth(package_tables)
        if all(
            set(tables) == set(EXPECTED_RAW_FILES) for tables in package_tables.values()
        )
        else {}
    )
    constructions, feasibility = _model_checks(
        dataset_dir, issues, solve_base=solve_base
    )
    complete_count = sum(
        record["complete"] for record in completeness["datasets"].values()
    )
    valid_coverage = sum(
        all(value for key, value in record.items() if key != "sets")
        for record in coverage.values()
    )
    manifest_count = sum(
        manifest.get("dataset_id") == dataset_id
        and len(manifest.get("files", {})) == len(EXPECTED_RAW_FILES)
        for dataset_id, manifest in manifests.items()
    )
    scenario_participation = sum(
        bool(scenario_profiles.get(dataset_id, {}).get("affected_targets"))
        for dataset_id in DATASET_IDS[1:]
    )
    fallback_count = sum(
        issue["code"] in {"PACKAGE_SYMLINK", "PACKAGE_ESCAPE"} for issue in issues
    )
    exact_scenario_profiles = sum(
        profile.get("controlled_profile_matches", False)
        for profile in scenario_profiles.values()
    )
    planning_metrics = [
        _metric(
            "complete_packages",
            "Complete dataset packages",
            complete_count,
            "6",
            complete_count == 6,
        ),
        _metric(
            "schema_valid_files",
            "Required schema-valid raw files",
            sum(len(tables) for tables in package_tables.values()),
            str(len(DATASET_IDS) * len(EXPECTED_RAW_FILES)),
            sum(len(tables) for tables in package_tables.values())
            == len(DATASET_IDS) * len(EXPECTED_RAW_FILES),
        ),
        _metric(
            "matching_manifests",
            "Complete manifests with matching identity",
            manifest_count,
            "6",
            manifest_count == 6,
        ),
        _metric(
            "external_fallbacks",
            "Files resolving outside their selected package",
            fallback_count,
            "0",
            fallback_count == 0,
        ),
        _metric(
            "derived_coverage",
            "Packages with complete derived-grain coverage",
            valid_coverage,
            "6",
            valid_coverage == 6,
        ),
        _metric(
            "common_construction",
            "Packages accepted by one loader and model constructor",
            len(constructions),
            "6",
            len(constructions) == 6,
        ),
        _metric(
            "base_feasibility",
            "BASE zero-shortage physical MILP witness",
            1 if feasibility["status"] == "PASS" else 0,
            "1",
            feasibility["status"] == "PASS",
        ),
        _metric(
            "boundary_source_dependency",
            "BASE zero-shortage dependence on boundary sourcing",
            (
                1
                if feasibility["boundary_source_dependency"]["status"] == "PASS"
                else 0
            ),
            "1",
            feasibility["boundary_source_dependency"]["status"] == "PASS",
        ),
        _metric(
            "varying_demand",
            "Terminal streams with planned variation",
            len(planning_depth.get("varying_demand_streams", [])),
            "24",
            len(planning_depth.get("varying_demand_streams", [])) == 24,
        ),
        _metric(
            "demand_peaks",
            "Terminal streams with material planned peaks",
            len(planning_depth.get("peak_demand_streams", [])),
            ">=8",
            len(planning_depth.get("peak_demand_streams", [])) >= 8,
        ),
        _metric(
            "advance_dispatches",
            "Terminal streams supported by standard dispatch at least two periods earlier",
            len(planning_depth.get("advance_standard_dispatch_streams", [])),
            ">=8",
            len(planning_depth.get("advance_standard_dispatch_streams", [])) >= 8,
        ),
        _metric(
            "opening_inventory",
            "Positive opening-stock states",
            planning_depth.get("positive_opening_states", 0),
            "32..56",
            32 <= planning_depth.get("positive_opening_states", 0) <= 56,
        ),
        _metric(
            "opening_tier_span",
            "Opening-stock location classes",
            len(planning_depth.get("opening_states_by_tier", {})),
            ">=4 including plants",
            len(planning_depth.get("opening_states_by_tier", {})) >= 4
            and "PLANT" in planning_depth.get("opening_states_by_tier", {}),
        ),
        _metric(
            "shared_capacity",
            "Multi-recipe shared-capacity groups",
            len(planning_depth.get("shared_capacity_groups", {})),
            ">=6",
            len(planning_depth.get("shared_capacity_groups", {})) >= 6,
        ),
        _metric(
            "pressure_witnesses",
            "Temporal pressure witnesses",
            len(planning_depth.get("pressure_witnesses", [])),
            ">=16",
            len(planning_depth.get("pressure_witnesses", [])) >= 16,
        ),
        _metric(
            "historical_contrasts",
            "Multi-source pools with service contrast",
            len(planning_depth.get("historical_contrast_pools", [])),
            ">=8",
            len(planning_depth.get("historical_contrast_pools", [])) >= 8,
        ),
        _metric(
            "partial_history",
            "Partial historical rows",
            round(planning_depth.get("partial_history_fraction", 0), 4),
            "3%..10%",
            0.03 <= planning_depth.get("partial_history_fraction", 0) <= 0.10,
        ),
        _metric(
            "scenario_participation",
            "Stress packages with active targets",
            scenario_participation,
            "5",
            scenario_participation == 5,
        ),
        _metric(
            "controlled_scenario_profiles",
            "Packages matching controlled scenario targets and magnitudes",
            exact_scenario_profiles,
            "6",
            exact_scenario_profiles == 6,
        ),
        _metric(
            "scn01_lineage",
            "SCN-01 affected terminal materials",
            len(scenario_depth.get("scn01_terminal_materials", [])),
            ">=2",
            len(scenario_depth.get("scn01_terminal_materials", [])) >= 2,
        ),
        _metric(
            "scn02_recourse",
            "SCN-02 standard lanes retaining expedited alternatives",
            len(
                scenario_depth.get(
                    "scn02_standard_lanes_with_expedited_alternative", []
                )
            ),
            ">=4",
            len(
                scenario_depth.get(
                    "scn02_standard_lanes_with_expedited_alternative", []
                )
            )
            >= 4,
        ),
        _metric(
            "scn03_recourse",
            "SCN-03 terminal streams with approved alternate",
            len(scenario_depth.get("scn03_streams_with_alternate", [])),
            ">=3",
            len(scenario_depth.get("scn03_streams_with_alternate", [])) >= 3,
        ),
        _metric(
            "scn04_span",
            "SCN-04 affected nodes across supplier tiers",
            len(scenario_depth.get("scn04_nodes", [])),
            ">=5 nodes, >=3 tiers",
            len(scenario_depth.get("scn04_nodes", [])) >= 5
            and len(scenario_depth.get("scn04_tiers", [])) >= 3,
        ),
        _metric(
            "scn05_uplift",
            "SCN-05 critical-demand uplift streams",
            len(scenario_depth.get("scn05_demand_uplifts", [])),
            ">=1 at 10%..15%",
            bool(scenario_depth.get("scn05_demand_uplifts"))
            and all(
                1.10 <= row["multiplier"] <= 1.15
                for row in scenario_depth.get("scn05_demand_uplifts", [])
            ),
        ),
    ]
    for metric in planning_metrics:
        if not metric["passed"]:
            _issue(
                issues,
                "GATE_FAILED",
                f"{metric['label']} failed its threshold",
                [metric["metric_id"]],
            )
    scorecard = {
        "status": "PASS" if not issues else "FAIL",
        "dataset_count": len(package_tables),
        "raw_file_count": sum(len(tables) for tables in package_tables.values()),
        "metrics": planning_metrics,
        "issues": issues,
        "model_constructions": constructions,
    }
    completeness["status"] = (
        "PASS" if complete_count == 6 and manifest_count == 6 else "FAIL"
    )
    planning_witnesses = {
        "profile": planning_depth,
        "coverage": {
            key: {name: value for name, value in record.items() if name != "sets"}
            for key, record in coverage.items()
        },
    }
    scenario_witnesses = {"profiles": scenario_profiles, "depth": scenario_depth}
    report = _report(scorecard, planning_depth, scenario_depth, feasibility)
    return Assessment(
        scorecard,
        completeness,
        planning_witnesses,
        scenario_witnesses,
        feasibility,
        report,
    )


def _report(
    scorecard: Mapping[str, Any],
    planning: Mapping[str, Any],
    scenarios: Mapping[str, Any],
    feasibility: Mapping[str, Any],
) -> str:
    lines = [
        "# CAP-001 Planning and Dataset-Package Assessment",
        "",
        "## Outcome",
        "",
        f"Assessment status: **{scorecard['status']}**.",
        "",
        "The evidence concerns dataset completeness, planning depth, package interchangeability and a bounded physical-feasibility smoke check. It does not publish or endorse an allocation.",
        "",
        "## Candidate profile",
        "",
        f"- Complete dataset roots: {scorecard['dataset_count']}",
        f"- Raw CSV files validated: {scorecard['raw_file_count']}",
        f"- Positive opening-stock states: {planning.get('positive_opening_states', 0)}",
        f"- Shared capacity groups: {len(planning.get('shared_capacity_groups', {}))}",
        f"- Historical contrast pools: {len(planning.get('historical_contrast_pools', []))}",
        f"- BASE feasibility: {feasibility['status']} ({feasibility.get('termination')})",
        "- BASE boundary-source dependency: "
        f"{feasibility['boundary_source_dependency']['status']} "
        f"({feasibility['boundary_source_dependency'].get('termination')})",
        "",
        "## Scenario profile",
        "",
        f"- SCN-01 downstream terminal materials: {len(scenarios.get('scn01_terminal_materials', []))}",
        f"- SCN-02 standard corridors retaining expedited alternatives: {len(scenarios.get('scn02_standard_lanes_with_expedited_alternative', []))}",
        f"- SCN-03 terminal streams retaining an alternate: {len(scenarios.get('scn03_streams_with_alternate', []))}",
        f"- SCN-04 affected nodes/tiers: {len(scenarios.get('scn04_nodes', []))}/{len(scenarios.get('scn04_tiers', []))}",
        f"- SCN-05 demand-uplift streams: {len(scenarios.get('scn05_demand_uplifts', []))}",
        "",
        "## Gate results",
        "",
        "| Gate | Value | Threshold | Result |",
        "|---|---:|---:|---|",
    ]
    for metric in scorecard["metrics"]:
        lines.append(
            f"| {metric['label']} | {metric['value']} | {metric['threshold']} | {'PASS' if metric['passed'] else 'FAIL'} |"
        )
    if scorecard["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in scorecard["issues"]:
            lines.append(f"- `{issue['code']}` — {issue['message']}")
    return "\n".join(lines).rstrip() + "\n"


def render_evidence(assessment: Assessment) -> dict[str, str]:
    return {
        "dataset_package_scorecard.json": canonical_json(assessment.scorecard),
        "package_completeness_matrix.json": canonical_json(
            assessment.completeness_matrix
        ),
        "planning_depth_witnesses.json": canonical_json(assessment.planning_witnesses),
        "scenario_materiality_witnesses.json": canonical_json(
            assessment.scenario_witnesses
        ),
        "base_feasibility_summary.json": canonical_json(assessment.feasibility_summary),
        "PLANNING_AND_DATASET_PACKAGE_REPORT.md": assessment.report,
    }


def write_evidence(dataset_dir: Path, assessment: Assessment) -> None:
    evidence_dir = dataset_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, content in render_evidence(assessment).items():
        (evidence_dir / name).write_text(content, encoding="utf-8", newline="")


def check_evidence(dataset_dir: Path, assessment: Assessment) -> list[str]:
    return [
        name
        for name, content in render_evidence(assessment).items()
        if not (dataset_dir / "evidence" / name).is_file()
        or (dataset_dir / "evidence" / name).read_text(encoding="utf-8") != content
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--skip-solver", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    assessment = assess_paths(
        args.dataset_dir.resolve(), solve_base=not args.skip_solver
    )
    if args.check:
        drift = check_evidence(args.dataset_dir.resolve(), assessment)
        if drift:
            print(
                "Dataset-package evidence drift: " + ", ".join(drift), file=sys.stderr
            )
            return 1
    else:
        write_evidence(args.dataset_dir.resolve(), assessment)
    if not assessment.passed:
        print("Dataset-package assessment failed.", file=sys.stderr)
        for issue in assessment.scorecard["issues"]:
            print(f"  {issue['code']}: {issue['message']}", file=sys.stderr)
        return 1
    print(
        f"Dataset-package assessment passed ({len(assessment.scorecard['metrics'])} gates)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
