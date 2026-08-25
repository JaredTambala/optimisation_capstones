#!/usr/bin/env python3
"""Generate deterministic planning facts for the CAP-001 network."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.contract_runtime import (  # noqa: E402
    canonical_json,
    coerce_csv_value,
    load_config,
    sha256_bytes,
    validate_csv_file,
)


DEFAULT_NETWORK_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "network"
DEFAULT_COMMERCIAL_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "commercial"
DEFAULT_OUTPUT_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "planning"
DEFAULT_MASTER_SEED = 9042027
PERIODS = tuple(f"P{number:02d}" for number in range(1, 13))
UPSTREAM_OPENING_COVERAGE_BUFFER = 1.32
MONTHS = tuple(
    date(year, month, 1)
    for year, month in (
        (year, month) for year in (2024, 2025, 2026) for month in range(1, 13)
    )
    if date(year, month, 1) >= date(2024, 7, 1)
)
NETWORK_FILES = (
    "supplier_organisations.csv",
    "network_nodes.csv",
    "plants.csv",
    "materials.csv",
    "transformation_recipes.csv",
    "transformation_inputs.csv",
    "material_flow_approvals.csv",
)
COMMERCIAL_FILES = (
    "supply_contracts.csv",
    "incoterm_rules.csv",
    "import_duty_rates.csv",
    "shipping_lanes.csv",
    "external_source_prices.csv",
    "conversion_costs.csv",
    "cost_allocation_rules.csv",
    "fx_rates.csv",
    "baseline_standard_costs.csv",
)
PLANNING_FILES = (
    "planning_calendar.csv",
    "source_capacity.csv",
    "transformation_capacity.csv",
    "inventory_policies.csv",
    "opening_inventory.csv",
    "terminal_demand.csv",
    "supplier_performance_history.csv",
    "incident_history.csv",
)


@dataclass(frozen=True)
class PlanningCandidate:
    tables: dict[str, list[dict[str, Any]]]
    evidence: dict[str, Any]


def stable_fraction(master_seed: int, namespace: str, key: str) -> float:
    digest = hashlib.sha256(f"{master_seed}:{namespace}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def _between(
    master_seed: int, namespace: str, key: str, lower: float, upper: float
) -> float:
    return lower + stable_fraction(master_seed, namespace, key) * (upper - lower)


def _read_typed_csv(path: Path, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    validate_csv_file(path, contract)
    fields = {field["name"]: field for field in contract["columns"]}
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {name: coerce_csv_value(value, fields[name]) for name, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def load_frozen_inputs(
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
) -> dict[str, list[dict[str, Any]]]:
    config = load_config()
    roots = {
        **{name: network_dir / "data" / name for name in NETWORK_FILES},
        **{name: commercial_dir / "data" / name for name in COMMERCIAL_FILES},
    }
    return {
        name: _read_typed_csv(path, config["raw_contracts"][name])
        for name, path in roots.items()
    }


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


def _calendar() -> list[dict[str, Any]]:
    start = date(2027, 1, 4)
    rows = []
    for offset, period in enumerate(PERIODS):
        week_start = start + timedelta(weeks=offset)
        week_end = week_start + timedelta(days=6)
        cutoff = datetime.combine(
            week_start - timedelta(days=3), time(12), tzinfo=timezone.utc
        )
        rows.append(
            {
                "period_id": period,
                "period_number": offset + 1,
                "week_start_date": week_start.isoformat(),
                "week_end_date": week_end.isoformat(),
                "order_cutoff_timestamp": cutoff.isoformat().replace("+00:00", "Z"),
                "is_terminal_period": period == "P12",
            }
        )
    return rows


def _network_indexes(
    inputs: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    nodes = {row["node_id"]: row for row in inputs["network_nodes.csv"]}
    materials = {row["material_id"]: row for row in inputs["materials.csv"]}
    recipes = {row["recipe_id"]: row for row in inputs["transformation_recipes.csv"]}
    approvals = list(inputs["material_flow_approvals.csv"])
    pools = {(row["seller_node_id"], row["material_id"]) for row in approvals} | {
        (row["buyer_node_id"], row["material_id"]) for row in approvals
    }
    pools |= {(row["node_id"], row["output_material_id"]) for row in recipes.values()}
    pools |= {
        (recipes[row["recipe_id"]]["node_id"], row["input_material_id"])
        for row in inputs["transformation_inputs.csv"]
    }
    source_states = sorted(
        {
            (row["seller_node_id"], row["material_id"])
            for row in approvals
            if nodes[row["seller_node_id"]]["external_boundary_flag"]
        }
    )
    terminal_pairs = sorted(
        {
            (row["buyer_node_id"], row["material_id"])
            for row in approvals
            if nodes[row["buyer_node_id"]]["node_tier"] == "PLANT"
        }
    )
    seller_states = sorted(
        {(row["seller_node_id"], row["material_id"]) for row in approvals}
    )
    return {
        "nodes": nodes,
        "materials": materials,
        "recipes": recipes,
        "approvals": approvals,
        "pools": sorted(pools),
        "source_states": source_states,
        "terminal_pairs": terminal_pairs,
        "seller_states": seller_states,
    }


def _source_premiums(
    inputs: Mapping[str, Sequence[Mapping[str, Any]]], indexes: Mapping[str, Any]
) -> dict[tuple[str, str, str], float]:
    approvals = {row["approval_id"]: row for row in indexes["approvals"]}
    contracts = {row["contract_id"]: row for row in inputs["supply_contracts.csv"]}
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in inputs["fx_rates.csv"]
    }
    prices: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in inputs["external_source_prices.csv"]:
        contract = contracts[row["contract_id"]]
        approval = approvals[contract["approval_id"]]
        prices[
            (approval["seller_node_id"], row["material_id"], row["period_id"])
        ].append(row["unit_price"] * fx[(row["currency"], row["period_id"])])
    return {
        key: round(sum(values) / len(values) * 0.18, 4)
        for key, values in prices.items()
    }


def _source_capacity(
    master_seed: int,
    inputs: Mapping[str, Sequence[Mapping[str, Any]]],
    indexes: Mapping[str, Any],
) -> list[dict[str, Any]]:
    premiums = _source_premiums(inputs, indexes)
    rows = []
    for node_id, material_id in indexes["source_states"]:
        uom = indexes["materials"][material_id]["uom"]
        base = 4400.0 if uom == "KG" else 900.0
        profile = _between(
            master_seed,
            "source-capacity-profile",
            f"{node_id}|{material_id}",
            0.82,
            1.18,
        )
        for number, period in enumerate(PERIODS, start=1):
            seasonal = 1 + 0.08 * math.sin(
                number / 2
                + stable_fraction(
                    master_seed, "source-capacity-phase", f"{node_id}|{material_id}"
                )
                * math.pi
            )
            downtime = 0.0
            if (
                stable_fraction(master_seed, "source-downtime", f"{node_id}|{period}")
                > 0.91
            ):
                downtime = 0.12
            regular = base * profile * seasonal
            rows.append(
                {
                    "node_id": node_id,
                    "material_id": material_id,
                    "period_id": period,
                    "regular_capacity": round(regular, 2),
                    "surge_capacity": round(regular * 0.28, 2),
                    "surge_unit_premium": premiums[(node_id, material_id, period)],
                    "planned_downtime_fraction": downtime,
                    "minimum_supply_quantity": 0.0,
                }
            )
    return rows


def _transformation_capacity(
    master_seed: int,
    inputs: Mapping[str, Sequence[Mapping[str, Any]]],
    indexes: Mapping[str, Any],
) -> list[dict[str, Any]]:
    recipes_by_node: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for recipe in indexes["recipes"].values():
        recipes_by_node[recipe["node_id"]].append(recipe)
    conversion = {
        (row["recipe_id"], row["period_id"]): row
        for row in inputs["conversion_costs.csv"]
    }
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in inputs["fx_rates.csv"]
    }
    rows = []
    for recipe in sorted(indexes["recipes"].values(), key=lambda row: row["recipe_id"]):
        uom = indexes["materials"][recipe["output_material_id"]]["uom"]
        base = 2700.0 if uom == "KG" else 720.0
        group = (
            f"SHR-{recipe['node_id']}"
            if len(recipes_by_node[recipe["node_id"]]) >= 2
            else None
        )
        capacity_key = recipe["node_id"] if group else recipe["recipe_id"]
        profile = _between(
            master_seed,
            "shared-capacity-profile" if group else "recipe-capacity-profile",
            capacity_key,
            0.78,
            1.16,
        )
        coefficient = (
            round(
                _between(
                    master_seed, "shared-coefficient", recipe["recipe_id"], 0.82, 1.18
                ),
                4,
            )
            if group
            else None
        )
        for number, period in enumerate(PERIODS, start=1):
            movement = 1 + 0.07 * math.sin(
                number / 2.2
                + stable_fraction(
                    master_seed,
                    "shared-capacity-phase" if group else "recipe-capacity-phase",
                    capacity_key,
                )
                * math.pi
            )
            downtime = 0.0
            if (
                stable_fraction(
                    master_seed,
                    "shared-downtime" if group else "recipe-downtime",
                    f"{capacity_key}|{period}",
                )
                > 0.94
            ):
                downtime = 0.15
            regular = base * profile * movement
            cost = conversion[(recipe["recipe_id"], period)]
            premium = (
                cost["variable_conversion_cost_per_output"]
                * fx[(cost["currency"], period)]
                * 0.35
            )
            rows.append(
                {
                    "node_id": recipe["node_id"],
                    "recipe_id": recipe["recipe_id"],
                    "period_id": period,
                    "regular_output_capacity": round(regular, 2),
                    "surge_output_capacity": round(regular * 0.25, 2),
                    "surge_conversion_premium": round(premium, 4),
                    "planned_downtime_fraction": downtime,
                    "shared_capacity_group_id": group,
                    "shared_capacity_coefficient": coefficient,
                }
            )
    return rows


def _terminal_lead_times(
    inputs: Mapping[str, Sequence[Mapping[str, Any]]], indexes: Mapping[str, Any]
) -> dict[tuple[str, str], int]:
    contracts = {row["approval_id"]: row for row in inputs["supply_contracts.csv"]}
    lanes_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in inputs["shipping_lanes.csv"]:
        if row["active_flag"]:
            lanes_by_pair[(row["origin_node_id"], row["destination_node_id"])].append(
                row
            )
    leads: dict[tuple[str, str], list[int]] = defaultdict(list)
    terminal_set = set(indexes["terminal_pairs"])
    for approval in indexes["approvals"]:
        key = (approval["buyer_node_id"], approval["material_id"])
        if key not in terminal_set:
            continue
        handling = contracts[approval["approval_id"]]["contract_handling_days"]
        for lane in lanes_by_pair[
            (approval["seller_node_id"], approval["buyer_node_id"])
        ]:
            leads[key].append(math.ceil((handling + lane["base_transit_days"]) / 7))
    return {key: min(values) for key, values in leads.items()}


def _plant_opening_states(
    indexes: Mapping[str, Any], lead_times: Mapping[tuple[str, str], int]
) -> tuple[tuple[str, str], ...]:
    ranked = sorted(
        indexes["terminal_pairs"],
        key=lambda state: (
            -lead_times[state],
            indexes["materials"][state[1]]["criticality_class"] != "CRITICAL",
            state,
        ),
    )
    return tuple(sorted(ranked[:8]))


def _inventory_policies(
    master_seed: int, indexes: Mapping[str, Any]
) -> list[dict[str, Any]]:
    tier_storage = {
        "TIER_4": 9000.0,
        "TIER_3": 6500.0,
        "TIER_2": 3600.0,
        "TIER_1": 1800.0,
        "PLANT": 900.0,
    }
    rows = []
    seller_states = set(indexes["seller_states"])
    for node_id, material_id in indexes["pools"]:
        node = indexes["nodes"][node_id]
        material = indexes["materials"][material_id]
        marker = stable_fraction(
            master_seed, "inventory-permission", f"{node_id}|{material_id}"
        )
        allowed = (
            node["node_tier"] == "PLANT"
            or (node_id, material_id) in seller_states
            or marker > 0.11
        )
        maximum = tier_storage[node["node_tier"]] * (
            0.65 if material["uom"] == "EA" else 1.0
        )
        if not allowed:
            maximum = 0.0
        safety = 0.0
        treatment = "REPORT_ONLY"
        if allowed and marker > 0.72:
            safety = round(maximum * (0.025 + 0.025 * marker), 2)
            treatment = "SOFT" if marker < 0.94 else "HARD"
        holding_base = 0.06 if material["uom"] == "KG" else 0.38
        rows.append(
            {
                "node_id": node_id,
                "material_id": material_id,
                "allow_inventory_flag": allowed,
                "safety_stock_quantity": safety,
                "safety_stock_treatment": treatment,
                "maximum_storage_quantity": round(maximum, 2),
                "holding_cost_eur_per_unit_week": round(
                    holding_base
                    * _between(
                        master_seed,
                        "holding-cost",
                        f"{node_id}|{material_id}",
                        0.7,
                        1.4,
                    ),
                    4,
                ),
                "minimum_meaningful_pool_quantity": 0.01,
                "terminal_target_quantity": None,
            }
        )
    return rows


def _selected_opening_states(
    indexes: Mapping[str, Any],
    policies: Sequence[Mapping[str, Any]],
    plant_opening_states: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    policy = {(row["node_id"], row["material_id"]): row for row in policies}
    selected = list(plant_opening_states)
    for tier, count in (("TIER_1", 16), ("TIER_2", 16), ("TIER_3", 8)):
        candidates = [
            state
            for state in indexes["seller_states"]
            if indexes["nodes"][state[0]]["node_tier"] == tier
            and policy[state]["allow_inventory_flag"]
        ]
        selected.extend(candidates[:count])
    expected_states = len(plant_opening_states) + 40
    if len(selected) != expected_states:
        raise ValueError(
            "opening inventory selection drifted: "
            f"expected {expected_states}, got {len(selected)}"
        )
    return tuple(selected)


def _align_hard_safety_with_startup_stock(
    policies: Sequence[Mapping[str, Any]],
    opening_states: Sequence[tuple[str, str]],
) -> list[dict[str, Any]]:
    opened = set(opening_states)
    aligned = []
    for original in policies:
        row = dict(original)
        state = (row["node_id"], row["material_id"])
        if row["safety_stock_treatment"] == "HARD" and state not in opened:
            row["safety_stock_treatment"] = "SOFT"
        aligned.append(row)
    return aligned


def _terminal_demand(
    master_seed: int,
    indexes: Mapping[str, Any],
    lead_times: Mapping[tuple[str, str], int],
    plant_opening_states: Sequence[tuple[str, str]],
) -> list[dict[str, Any]]:
    rows = []
    opening_set = set(plant_opening_states)
    for stream_number, (plant_id, material_id) in enumerate(indexes["terminal_pairs"]):
        material = indexes["materials"][material_id]
        base = _between(
            master_seed, "demand-base", f"{plant_id}|{material_id}", 18.0, 42.0
        )
        peak_period = 5 + stream_number % 6
        priority = (
            "CRITICAL"
            if material["criticality_class"] == "CRITICAL"
            else ("HIGH" if stream_number % 3 else "STANDARD")
        )
        service_weight = {"STANDARD": 1.0, "HIGH": 2.5, "CRITICAL": 6.0}[priority]
        quantities = []
        for number in range(1, len(PERIODS) + 1):
            pattern = 1 + 0.11 * math.sin(
                number * 0.8
                + stable_fraction(
                    master_seed, "demand-phase", f"{plant_id}|{material_id}"
                )
                * math.pi
            )
            if number == peak_period:
                pattern *= 1.42
            elif number == peak_period + 1:
                pattern *= 1.18
            quantities.append(round(base * pattern, 2))
        if (plant_id, material_id) not in opening_set:
            deferred_periods = min(
                lead_times[(plant_id, material_id)] + 3,
                len(PERIODS) - 1,
            )
            original_total = sum(quantities)
            deferred = sum(quantities[:deferred_periods])
            quantities[:deferred_periods] = [0.0] * deferred_periods
            recipients = len(PERIODS) - deferred_periods
            increment = deferred / recipients
            for position in range(deferred_periods, len(PERIODS)):
                quantities[position] = round(quantities[position] + increment, 2)
            quantities[-1] = round(
                quantities[-1] + original_total - sum(quantities), 2
            )
        for period, quantity in zip(PERIODS, quantities, strict=True):
            rows.append(
                {
                    "plant_id": plant_id,
                    "material_id": material_id,
                    "period_id": period,
                    "demand_quantity": quantity,
                    "priority_class": priority,
                    "service_weight": service_weight,
                    "shortage_penalty_eur_per_unit": {
                        "STANDARD": 900.0,
                        "HIGH": 2400.0,
                        "CRITICAL": 6000.0,
                    }[priority],
                }
            )
    return rows


def _opening_costs(
    inputs: Mapping[str, Sequence[Mapping[str, Any]]], indexes: Mapping[str, Any]
) -> dict[tuple[str, str], float]:
    standard: dict[tuple[str, str], float] = {}
    for row in inputs["baseline_standard_costs.csv"]:
        if row["period_id"] == "P01":
            standard[(row["node_id"], row["material_id"])] = row[
                "standard_unit_cost_eur"
            ]
    approvals_by_buyer: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for row in indexes["approvals"]:
        approvals_by_buyer[(row["buyer_node_id"], row["material_id"])].append(row)
    costs = dict(standard)
    for state in indexes["pools"]:
        if state in costs:
            continue
        upstream = [
            standard.get((row["seller_node_id"], row["material_id"]))
            for row in approvals_by_buyer.get(state, [])
        ]
        upstream = [value for value in upstream if value is not None]
        costs[state] = sum(upstream) / len(upstream) if upstream else 25.0
    return costs


def _propagated_output_requirements(
    inputs: Mapping[str, Sequence[Mapping[str, Any]]],
    indexes: Mapping[str, Any],
    demand: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], float]:
    """Estimate upstream demand for startup-stock sizing using neutral shares."""

    requirements: dict[tuple[str, str], float] = defaultdict(float)
    for row in demand:
        requirements[(row["plant_id"], row["material_id"])] += row[
            "demand_quantity"
        ]
    approvals_by_buyer: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for row in indexes["approvals"]:
        approvals_by_buyer[(row["buyer_node_id"], row["material_id"])].append(row)
    recipes_by_output: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for recipe in indexes["recipes"].values():
        recipes_by_output[(recipe["node_id"], recipe["output_material_id"])].append(
            recipe
        )
    recipe_inputs: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in inputs["transformation_inputs.csv"]:
        recipe_inputs[row["recipe_id"]].append(row)

    for buyer_tier, seller_tier in (
        ("PLANT", "TIER_1"),
        ("TIER_1", "TIER_2"),
        ("TIER_2", "TIER_3"),
        ("TIER_3", "TIER_4"),
    ):
        buyer_states = sorted(
            state
            for state in requirements
            if indexes["nodes"][state[0]]["node_tier"] == buyer_tier
        )
        for state in buyer_states:
            approvals = approvals_by_buyer.get(state, [])
            if not approvals:
                continue
            equal_share = requirements[state] / len(approvals)
            for approval in approvals:
                requirements[
                    (approval["seller_node_id"], approval["material_id"])
                ] += equal_share
        if seller_tier == "TIER_4":
            continue
        output_states = sorted(
            state
            for state in requirements
            if indexes["nodes"][state[0]]["node_tier"] == seller_tier
            and state in recipes_by_output
        )
        for state in output_states:
            recipes = recipes_by_output[state]
            output_per_recipe = requirements[state] / len(recipes)
            for recipe in recipes:
                for input_row in recipe_inputs[recipe["recipe_id"]]:
                    requirements[(state[0], input_row["input_material_id"])] += (
                        output_per_recipe
                        * input_row["quantity_per_output"]
                        / recipe["yield_rate"]
                    )
    return dict(requirements)


def _output_startup_coverage(
    inputs: Mapping[str, Sequence[Mapping[str, Any]]],
    indexes: Mapping[str, Any],
) -> dict[tuple[str, str], int]:
    """Calculate periods of output needed before all recipe inputs can arrive."""

    contracts = {row["approval_id"]: row for row in inputs["supply_contracts.csv"]}
    approvals_by_buyer: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for row in indexes["approvals"]:
        approvals_by_buyer[(row["buyer_node_id"], row["material_id"])].append(row)
    lanes_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in inputs["shipping_lanes.csv"]:
        if row["active_flag"]:
            lanes_by_pair[(row["origin_node_id"], row["destination_node_id"])].append(
                row
            )
    recipe_inputs: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in inputs["transformation_inputs.csv"]:
        recipe_inputs[row["recipe_id"]].append(row)
    recipes_by_output: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for recipe in indexes["recipes"].values():
        recipes_by_output[(recipe["node_id"], recipe["output_material_id"])].append(
            recipe
        )

    coverage: dict[tuple[str, str], int] = {}
    for state, recipes in recipes_by_output.items():
        node_id, _ = state
        input_leads = []
        for recipe in recipes:
            for input_row in recipe_inputs[recipe["recipe_id"]]:
                approvals = approvals_by_buyer[
                    (node_id, input_row["input_material_id"])
                ]
                lead_options = [
                    math.ceil(
                        (
                            contracts[approval["approval_id"]][
                                "contract_handling_days"
                            ]
                            + lane["base_transit_days"]
                        )
                        / 7
                    )
                    for approval in approvals
                    for lane in lanes_by_pair[
                        (approval["seller_node_id"], approval["buyer_node_id"])
                    ]
                ]
                if not lead_options:
                    raise ValueError(
                        f"no active input route for {node_id}/{input_row['input_material_id']}"
                    )
                input_leads.append(min(lead_options))
        coverage[state] = max(input_leads, default=0) + 1
    return coverage


def _opening_inventory(
    master_seed: int,
    inputs: Mapping[str, Sequence[Mapping[str, Any]]],
    indexes: Mapping[str, Any],
    policies: Sequence[Mapping[str, Any]],
    demand: Sequence[Mapping[str, Any]],
    opening_states: Sequence[tuple[str, str]],
    lead_times: Mapping[tuple[str, str], int],
) -> list[dict[str, Any]]:
    policy = {(row["node_id"], row["material_id"]): row for row in policies}
    demand_by_stream: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in demand:
        demand_by_stream[(row["plant_id"], row["material_id"])].append(
            row["demand_quantity"]
        )
    costs = _opening_costs(inputs, indexes)
    output_requirements = _propagated_output_requirements(inputs, indexes, demand)
    startup_coverage = _output_startup_coverage(inputs, indexes)
    rows = []
    for node_id, material_id in opening_states:
        if indexes["nodes"][node_id]["node_tier"] == "PLANT":
            coverage = max(4, lead_times[(node_id, material_id)] + 2)
            usable = sum(demand_by_stream[(node_id, material_id)][:coverage]) * 1.08
        else:
            usable = (
                output_requirements[(node_id, material_id)]
                / len(PERIODS)
                * startup_coverage[(node_id, material_id)]
                * UPSTREAM_OPENING_COVERAGE_BUFFER
            )
        if policy[(node_id, material_id)]["safety_stock_treatment"] == "HARD":
            usable += policy[(node_id, material_id)]["safety_stock_quantity"]
        usable = min(
            usable, policy[(node_id, material_id)]["maximum_storage_quantity"] * 0.72
        )
        usable = round(usable, 2)
        reserved = round(
            usable
            * _between(
                master_seed, "opening-reserved", f"{node_id}|{material_id}", 0.02, 0.08
            ),
            2,
        )
        on_hand = round(usable + reserved, 2)
        unit_cost = round(
            costs[(node_id, material_id)]
            * _between(
                master_seed,
                "opening-book-value",
                f"{node_id}|{material_id}",
                0.92,
                1.08,
            ),
            6,
        )
        rows.append(
            {
                "node_id": node_id,
                "material_id": material_id,
                "on_hand_quantity": on_hand,
                "reserved_quantity": reserved,
                "usable_quantity": usable,
                "opening_unit_cost_eur": unit_cost,
                "opening_total_value_eur": round(usable * unit_cost, 6),
                "cost_basis_source": "SYNTHETIC_BOOK_VALUE",
                "valuation_date": "2027-01-03",
            }
        )
    return rows


def _performance_history(
    master_seed: int, indexes: Mapping[str, Any]
) -> list[dict[str, Any]]:
    partial_states = set(indexes["seller_states"][::9][:8])
    rows = []
    for node_id, material_id in indexes["seller_states"]:
        uom = indexes["materials"][material_id]["uom"]
        base = 1200.0 if uom == "KG" else 240.0
        reliability = _between(
            master_seed, "history-reliability", f"{node_id}|{material_id}", 0.78, 0.98
        )
        quality = _between(
            master_seed, "history-quality", f"{node_id}|{material_id}", 0.94, 0.998
        )
        lead = _between(
            master_seed, "history-lead", f"{node_id}|{material_id}", 4.0, 24.0
        )
        for offset, month in enumerate(MONTHS):
            ordered = base * (0.84 + 0.22 * math.sin(offset / 3 + reliability))
            received = ordered * min(
                1.0, reliability + 0.045 * math.sin(offset + reliability)
            )
            on_time = received * max(
                0.0, min(1.0, reliability - 0.03 + 0.04 * math.cos(offset / 2))
            )
            accepted = received * max(0.0, min(1.0, quality - 0.006 * math.sin(offset)))
            partial = (node_id, material_id) in partial_states and 8 <= offset < 18
            rows.append(
                {
                    "node_id": node_id,
                    "material_id": material_id,
                    "month": month.isoformat(),
                    "ordered_quantity": round(ordered, 2),
                    "received_quantity": round(received, 2),
                    "on_time_quantity": round(on_time, 2),
                    "accepted_quantity": round(accepted, 2),
                    "average_actual_lead_time_days": round(
                        lead * (1.02 + 0.09 * math.sin(offset / 2)), 2
                    ),
                    "lead_time_std_days": round(
                        lead * (0.08 + (1 - reliability) * 0.35), 2
                    ),
                    "quality_incident_count": 1 if accepted < received * 0.965 else 0,
                    "source_completeness_flag": "PARTIAL" if partial else "COMPLETE",
                }
            )
    return rows


def _incident_history(
    master_seed: int, indexes: Mapping[str, Any]
) -> list[dict[str, Any]]:
    nodes = indexes["nodes"]
    lane_targets = (
        "LANE-00081",
        "LANE-00093",
        "LANE-00094",
        "LANE-00095",
        "LANE-00096",
    )
    definitions: list[tuple[str, str, str]] = [
        ("NODE", node_id, ("OUTAGE", "ENERGY", "QUALITY", "CYBER")[index % 4])
        for index, node_id in enumerate(sorted(nodes)[::2][:18])
    ]
    definitions.extend(("LANE", lane, "PORT") for lane in lane_targets)
    definitions.extend(
        ("REGION", region, "WEATHER")
        for region in sorted({row["region_code"] for row in nodes.values()})[:7]
    )
    rows = []
    for index, (target_type, target_id, event_type) in enumerate(definitions, start=1):
        start = date(2024, 8, 5) + timedelta(days=index * 27)
        duration = 2 + index % 12
        severity = ("LOW", "MEDIUM", "HIGH", "SEVERE")[index % 4]
        rows.append(
            {
                "incident_id": f"INC-{index:05d}",
                "target_entity_type": target_type,
                "target_entity_id": target_id,
                "event_type": event_type,
                "start_date": start.isoformat(),
                "end_date": (start + timedelta(days=duration)).isoformat(),
                "severity": severity,
                "capacity_multiplier": round(
                    _between(master_seed, "incident-capacity", str(index), 0.45, 0.9), 3
                )
                if target_type != "LANE"
                else None,
                "transit_multiplier": round(
                    _between(master_seed, "incident-transit", str(index), 1.15, 1.8), 3
                )
                if target_type in {"LANE", "REGION"}
                else None,
                "cost_multiplier": round(
                    _between(master_seed, "incident-cost", str(index), 1.05, 1.35), 3
                ),
                "description": f"Synthetic {event_type.lower()} event affecting {target_id}; retained as exploratory evidence.",
            }
        )
    return rows


def build_candidate(
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
) -> PlanningCandidate:
    inputs = load_frozen_inputs(network_dir, commercial_dir)
    indexes = _network_indexes(inputs)
    lead_times = _terminal_lead_times(inputs, indexes)
    plant_opening_states = _plant_opening_states(indexes, lead_times)
    demand = _terminal_demand(master_seed, indexes, lead_times, plant_opening_states)
    initial_policies = _inventory_policies(master_seed, indexes)
    opening_states = _selected_opening_states(
        indexes, initial_policies, plant_opening_states
    )
    policies = _align_hard_safety_with_startup_stock(
        initial_policies, opening_states
    )
    tables = {
        "planning_calendar.csv": _calendar(),
        "source_capacity.csv": _source_capacity(master_seed, inputs, indexes),
        "transformation_capacity.csv": _transformation_capacity(
            master_seed, inputs, indexes
        ),
        "inventory_policies.csv": policies,
        "opening_inventory.csv": _opening_inventory(
            master_seed,
            inputs,
            indexes,
            policies,
            demand,
            opening_states,
            lead_times,
        ),
        "terminal_demand.csv": demand,
        "supplier_performance_history.csv": _performance_history(master_seed, indexes),
        "incident_history.csv": _incident_history(master_seed, indexes),
    }
    peak_streams = 0
    by_stream: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in demand:
        by_stream[(row["plant_id"], row["material_id"])].append(row["demand_quantity"])
    for values in by_stream.values():
        middle = sorted(values)[len(values) // 2]
        peak_streams += max(values) >= middle * 1.25
    evidence = {
        "derived_dimensions": {
            "pool_states": len(indexes["pools"]),
            "source_states": len(indexes["source_states"]),
            "seller_states": len(indexes["seller_states"]),
            "terminal_streams": len(indexes["terminal_pairs"]),
        },
        "opening_inventory_by_tier": dict(
            sorted(
                (
                    tier,
                    sum(
                        indexes["nodes"][row["node_id"]]["node_tier"] == tier
                        for row in tables["opening_inventory.csv"]
                    ),
                )
                for tier in {row["node_tier"] for row in indexes["nodes"].values()}
            )
        ),
        "demand_streams_with_material_peaks": peak_streams,
        "plant_opening_states": ["|".join(state) for state in plant_opening_states],
        "shared_capacity_groups": len(
            {
                row["shared_capacity_group_id"]
                for row in tables["transformation_capacity.csv"]
                if row["shared_capacity_group_id"] is not None
            }
        ),
    }
    return PlanningCandidate(tables=tables, evidence=evidence)


def render_files(
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
) -> dict[str, str]:
    config = load_config()
    candidate = build_candidate(master_seed, network_dir, commercial_dir)
    rendered = {}
    for file_name in PLANNING_FILES:
        fields = [
            field["name"] for field in config["raw_contracts"][file_name]["columns"]
        ]
        rendered[f"data/{file_name}"] = _csv_text(candidate.tables[file_name], fields)
    rendered["evidence/planning_profile.json"] = canonical_json(candidate.evidence)
    manifest = {
        "configuration_id": config["configuration_id"],
        "configuration_version": config["configuration_version"],
        "generator": "generate_planning_data.py",
        "master_seed": master_seed,
        "network_manifest_sha256": hashlib.sha256(
            (network_dir / "generation_manifest.json").read_bytes()
        ).hexdigest(),
        "commercial_manifest_sha256": hashlib.sha256(
            (commercial_dir / "generation_manifest.json").read_bytes()
        ).hexdigest(),
        "files": {
            path: {
                "rows": len(candidate.tables[path.removeprefix("data/")]),
                "sha256": sha256_bytes(content.encode()),
            }
            for path, content in rendered.items()
            if path.startswith("data/")
        },
    }
    rendered["generation_manifest.json"] = canonical_json(manifest)
    return rendered


def write_files(
    output_dir: Path,
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
) -> None:
    for relative, content in render_files(
        master_seed, network_dir, commercial_dir
    ).items():
        path = output_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")


def check_files(
    output_dir: Path,
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
) -> bool:
    expected = render_files(master_seed, network_dir, commercial_dir)
    return all(
        (output_dir / relative).is_file()
        and (output_dir / relative).read_text(encoding="utf-8") == content
        for relative, content in expected.items()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--network-dir", type=Path, default=DEFAULT_NETWORK_DIR)
    parser.add_argument("--commercial-dir", type=Path, default=DEFAULT_COMMERCIAL_DIR)
    parser.add_argument("--master-seed", type=int, default=DEFAULT_MASTER_SEED)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not check_files(
            args.output_dir, args.master_seed, args.network_dir, args.commercial_dir
        ):
            print(
                "planning candidate differs from deterministic regeneration",
                file=sys.stderr,
            )
            return 1
        print("planning candidate is current")
        return 0
    with tempfile.TemporaryDirectory(prefix="cap001-planning-") as temporary:
        staging = Path(temporary)
        write_files(staging, args.master_seed, args.network_dir, args.commercial_dir)
        for source in staging.rglob("*"):
            if source.is_file():
                destination = args.output_dir / source.relative_to(staging)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
    print(f"wrote deterministic planning candidate to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
