#!/usr/bin/env python3
"""Assemble complete, interchangeable CAP-001 dataset packages."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
GENERATOR_DIR = Path(__file__).resolve().parent
for location in (ROOT, GENERATOR_DIR):
    if str(location) not in sys.path:
        sys.path.insert(0, str(location))

import generate_planning_data as planning  # noqa: E402
from tooling.contract_runtime import (  # noqa: E402
    EXPECTED_RAW_FILES,
    canonical_json,
    load_config,
    sha256_bytes,
)


DEFAULT_OUTPUT_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "datasets"
DEFAULT_MASTER_SEED = planning.DEFAULT_MASTER_SEED
DATASET_IDS = ("BASE", "SCN-01", "SCN-02", "SCN-03", "SCN-04", "SCN-05")
SCENARIO_META = {
    "BASE": (
        "Reference planning dataset",
        "BASE",
        "NORMAL",
        "Normal planning and commercial conditions for the common comparison point.",
        "REOPTIMISE",
    ),
    "SCN-01": (
        "Silicon source interruption",
        "SOURCE",
        "HIGH",
        "A constrained upstream silicon source tests approved alternatives and advance positioning.",
        "REOPTIMISE",
    ),
    "SCN-02": (
        "Asia-Europe logistics delay",
        "LOGISTICS",
        "HIGH",
        "Selected standard Asia-Europe corridors become slower, dearer and capacity constrained while expedited modes remain available.",
        "REOPTIMISE",
    ),
    "SCN-03": (
        "Tier-1 site outage",
        "NODE",
        "SEVERE",
        "A Tier-1 site outage tests alternate approved production and recovery choices.",
        "REOPTIMISE",
    ),
    "SCN-04": (
        "Correlated central-European constraints",
        "REGIONAL",
        "HIGH",
        "Several central-European suppliers across tiers lose capacity at the same time.",
        "BOTH",
    ),
    "SCN-05": (
        "Combined supply, logistics and demand pressure",
        "COMBINED",
        "SEVERE",
        "Silicon and Asia-Europe logistics constraints coincide with higher critical terminal demand.",
        "REOPTIMISE",
    ),
}
ASIA_EUROPE_STANDARD_LANES = (
    "LANE-00081",
    "LANE-00093",
    "LANE-00094",
    "LANE-00095",
    "LANE-00096",
)
REGIONAL_NODE_MULTIPLIERS = {
    "NODE-0002": 0.68,
    "NODE-0005": 0.76,
    "NODE-0015": 0.60,
    "NODE-0024": 0.72,
    "NODE-0027": 0.80,
}
CRITICAL_DEMAND_STREAMS = (
    ("NODE-0035", "MAT-0029", 1.10),
    ("NODE-0035", "MAT-0031", 1.12),
    ("NODE-0035", "MAT-0032", 1.15),
    ("NODE-0036", "MAT-0029", 1.11),
    ("NODE-0036", "MAT-0030", 1.14),
    ("NODE-0037", "MAT-0030", 1.13),
    ("NODE-0037", "MAT-0031", 1.10),
    ("NODE-0038", "MAT-0032", 1.15),
)


def _csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _csv_text(rows: Iterable[Mapping[str, Any]], fieldnames: Sequence[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _csv_cell(row[field]) for field in fieldnames})
    return buffer.getvalue()


def _impact(
    scenario_id: str,
    target_type: str,
    target_id: str,
    start: str,
    end: str,
    *,
    material_id: str | None = None,
    availability: bool = True,
    capacity: float = 1.0,
    lane_capacity: float = 1.0,
    transit: float = 1.0,
    cost: float = 1.0,
    demand: float = 1.0,
    notes: str,
) -> dict[str, Any]:
    return {
        "impact_id": "",
        "scenario_id": scenario_id,
        "target_entity_type": target_type,
        "target_entity_id": target_id,
        "target_material_id": material_id,
        "target_cost_component": "FREIGHT" if cost != 1.0 else None,
        "start_period_id": start,
        "end_period_id": end,
        "availability_flag": availability,
        "capacity_multiplier": capacity,
        "lane_capacity_multiplier": lane_capacity,
        "transit_time_multiplier": transit,
        "cost_multiplier": cost,
        "demand_multiplier": demand,
        "replacement_field": None,
        "replacement_value": None,
        "impact_priority": 100,
        "notes": notes,
    }


def scenario_rows(dataset_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    name, category, severity, description, run_mode = SCENARIO_META[dataset_id]
    scenario = [
        {
            "scenario_id": dataset_id,
            "scenario_name": name,
            "scenario_category": category,
            "severity": severity,
            "description": description,
            "recommended_run_mode": run_mode,
            "active_flag": True,
        }
    ]
    impacts: list[dict[str, Any]] = []
    if dataset_id in {"SCN-01", "SCN-05"}:
        impacts.extend(
            [
                _impact(
                    dataset_id,
                    "NODE",
                    "NODE-0003",
                    "P03",
                    "P05",
                    material_id="MAT-0003",
                    capacity=0.30,
                    notes="Silicon-source capacity falls to 30 percent.",
                ),
                _impact(
                    dataset_id,
                    "NODE",
                    "NODE-0003",
                    "P06",
                    "P06",
                    material_id="MAT-0003",
                    capacity=0.60,
                    notes="Silicon-source recovery step at 60 percent.",
                ),
                _impact(
                    dataset_id,
                    "NODE",
                    "NODE-0003",
                    "P07",
                    "P12",
                    material_id="MAT-0003",
                    capacity=1.0,
                    notes="Explicit return to normal silicon-source capacity.",
                ),
            ]
        )
    if dataset_id in {"SCN-02", "SCN-05"}:
        for lane_id in ASIA_EUROPE_STANDARD_LANES:
            impacts.extend(
                [
                    _impact(
                        dataset_id,
                        "LANE",
                        lane_id,
                        "P02",
                        "P07",
                        lane_capacity=0.75,
                        transit=1.75,
                        cost=1.40,
                        notes="Standard corridor delay; paired expedited lane remains unchanged.",
                    ),
                    _impact(
                        dataset_id,
                        "LANE",
                        lane_id,
                        "P08",
                        "P12",
                        notes="Explicit standard-corridor recovery.",
                    ),
                ]
            )
    if dataset_id == "SCN-03":
        impacts.extend(
            [
                _impact(
                    dataset_id,
                    "NODE",
                    "NODE-0030",
                    "P04",
                    "P04",
                    availability=False,
                    capacity=0.0,
                    notes="Tier-1 site is unavailable.",
                ),
                _impact(
                    dataset_id,
                    "NODE",
                    "NODE-0030",
                    "P05",
                    "P05",
                    capacity=0.50,
                    notes="Tier-1 site restarts at half capacity.",
                ),
                _impact(
                    dataset_id,
                    "NODE",
                    "NODE-0030",
                    "P06",
                    "P12",
                    notes="Explicit Tier-1 site recovery.",
                ),
            ]
        )
    if dataset_id == "SCN-04":
        for node_id, multiplier in REGIONAL_NODE_MULTIPLIERS.items():
            impacts.extend(
                [
                    _impact(
                        dataset_id,
                        "NODE",
                        node_id,
                        "P03",
                        "P06",
                        capacity=multiplier,
                        notes="Correlated central-European capacity constraint.",
                    ),
                    _impact(
                        dataset_id,
                        "NODE",
                        node_id,
                        "P07",
                        "P12",
                        notes="Explicit regional recovery.",
                    ),
                ]
            )
    if dataset_id == "SCN-05":
        for plant_id, material_id, multiplier in CRITICAL_DEMAND_STREAMS:
            target = f"{plant_id}|{material_id}"
            impacts.extend(
                [
                    _impact(
                        dataset_id,
                        "TERMINAL_DEMAND",
                        target,
                        "P06",
                        "P10",
                        material_id=material_id,
                        demand=multiplier,
                        notes="Selected critical terminal demand uplift.",
                    ),
                    _impact(
                        dataset_id,
                        "TERMINAL_DEMAND",
                        target,
                        "P11",
                        "P12",
                        material_id=material_id,
                        notes="Explicit terminal-demand return to plan.",
                    ),
                ]
            )
    for number, row in enumerate(impacts, start=1):
        row["impact_id"] = f"IMP-{number:05d}"
    return scenario, impacts


def _source_files(
    network_dir: Path,
    commercial_dir: Path,
    planning_files: Mapping[str, str],
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for file_name in planning.NETWORK_FILES:
        result[file_name] = (network_dir / "data" / file_name).read_bytes()
    for file_name in planning.COMMERCIAL_FILES:
        result[file_name] = (commercial_dir / "data" / file_name).read_bytes()
    for file_name in planning.PLANNING_FILES:
        result[file_name] = planning_files[f"data/{file_name}"].encode()
    return result


def _dataset_manifest(
    dataset_id: str,
    files: Mapping[str, bytes],
    config: Mapping[str, Any],
    master_seed: int,
) -> dict[str, Any]:
    file_records = {
        name: {"sha256": sha256_bytes(content), "bytes": len(content)}
        for name, content in sorted(files.items())
    }
    aggregate = sha256_bytes(
        json.dumps(
            {name: record["sha256"] for name, record in file_records.items()},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    return {
        "capstone_id": "CAP-001",
        "capstone_version": config["versions"]["capstone"],
        "configuration_version": config["configuration_version"],
        "data_version": config["versions"]["data"],
        "schema_version": config["versions"]["schema"],
        "dataset_id": dataset_id,
        "scenario_id": dataset_id,
        "compatibility_group": "CAP-001-2027-Q1-v0.3.1",
        "generator": "generate_dataset_packages.py",
        "master_seed": master_seed,
        "required_file_count": len(EXPECTED_RAW_FILES),
        "files": file_records,
        "dataset_sha256": aggregate,
    }


def render_files(
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = planning.DEFAULT_NETWORK_DIR,
    commercial_dir: Path = planning.DEFAULT_COMMERCIAL_DIR,
) -> dict[str, bytes]:
    config = load_config()
    planning_files = planning.render_files(master_seed, network_dir, commercial_dir)
    common = _source_files(network_dir, commercial_dir, planning_files)
    rendered: dict[str, bytes] = {}
    package_hashes = {}
    for dataset_id in DATASET_IDS:
        scenario, impacts = scenario_rows(dataset_id)
        files = dict(common)
        for file_name, rows in (
            ("disruption_scenarios.csv", scenario),
            ("disruption_impacts.csv", impacts),
        ):
            fields = [
                field["name"] for field in config["raw_contracts"][file_name]["columns"]
            ]
            files[file_name] = _csv_text(rows, fields).encode()
        if set(files) != set(EXPECTED_RAW_FILES):
            raise ValueError(
                f"{dataset_id}: raw file set drifted: {sorted(set(EXPECTED_RAW_FILES) ^ set(files))}"
            )
        manifest = _dataset_manifest(dataset_id, files, config, master_seed)
        package_hashes[dataset_id] = manifest["dataset_sha256"]
        prefix = f"{dataset_id}"
        for name, content in files.items():
            rendered[f"{prefix}/data/{name}"] = content
        rendered[f"{prefix}/dataset_manifest.json"] = canonical_json(manifest).encode()
    rendered["generation_manifest.json"] = canonical_json(
        {
            "configuration_id": config["configuration_id"],
            "configuration_version": config["configuration_version"],
            "generator": "generate_dataset_packages.py",
            "master_seed": master_seed,
            "datasets": package_hashes,
        }
    ).encode()
    return rendered


def write_files(
    output_dir: Path,
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = planning.DEFAULT_NETWORK_DIR,
    commercial_dir: Path = planning.DEFAULT_COMMERCIAL_DIR,
) -> None:
    for relative, content in render_files(
        master_seed, network_dir, commercial_dir
    ).items():
        path = output_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def check_files(
    output_dir: Path,
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = planning.DEFAULT_NETWORK_DIR,
    commercial_dir: Path = planning.DEFAULT_COMMERCIAL_DIR,
) -> bool:
    expected = render_files(master_seed, network_dir, commercial_dir)
    expected_paths = set(expected)
    actual_paths = {
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file()
        and not path.relative_to(output_dir).as_posix().startswith("evidence/")
    }
    return expected_paths == actual_paths and all(
        (output_dir / relative).read_bytes() == content
        for relative, content in expected.items()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--network-dir", type=Path, default=planning.DEFAULT_NETWORK_DIR
    )
    parser.add_argument(
        "--commercial-dir", type=Path, default=planning.DEFAULT_COMMERCIAL_DIR
    )
    parser.add_argument("--master-seed", type=int, default=DEFAULT_MASTER_SEED)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not check_files(
            args.output_dir, args.master_seed, args.network_dir, args.commercial_dir
        ):
            print(
                "dataset packages differ from deterministic regeneration",
                file=sys.stderr,
            )
            return 1
        print("dataset packages are current")
        return 0
    with tempfile.TemporaryDirectory(prefix="cap001-packages-") as temporary:
        staging = Path(temporary)
        write_files(staging, args.master_seed, args.network_dir, args.commercial_dir)
        for source in staging.rglob("*"):
            if source.is_file():
                destination = args.output_dir / source.relative_to(staging)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
    print(f"wrote six complete dataset packages to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
