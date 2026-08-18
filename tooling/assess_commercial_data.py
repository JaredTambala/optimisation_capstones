"""Validate and profile commercial facts for the accepted CAP-001 network."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tooling.contract_runtime import (
    canonical_json,
    coerce_csv_value,
    load_config,
    sha256_path,
    validate_csv_file,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NETWORK_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "network"
DEFAULT_COMMERCIAL_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "commercial"
PERIODS = tuple(f"P{period:02d}" for period in range(1, 13))
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


@dataclass(frozen=True)
class Assessment:
    scorecard: dict[str, Any]
    tradeoff_witnesses: dict[str, Any]
    conditional_cost_envelopes: dict[str, Any]
    report: str

    @property
    def passed(self) -> bool:
        return self.scorecard["status"] == "PASS"


def _read(path: Path, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    validate_csv_file(path, contract)
    fields = {field["name"]: field for field in contract["columns"]}
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {name: coerce_csv_value(value, fields[name]) for name, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def load_tables(
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
    config: Mapping[str, Any] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    if config is None:
        config = load_config()
    network = {
        file_name: _read(network_dir / "data" / file_name, config["raw_contracts"][file_name])
        for file_name in NETWORK_FILES
    }
    commercial = {
        file_name: _read(commercial_dir / "data" / file_name, config["raw_contracts"][file_name])
        for file_name in COMMERCIAL_FILES
    }
    return network, commercial


def _issue(issues: list[dict[str, Any]], code: str, message: str, entities: Iterable[str] = ()) -> None:
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


def _duplicates(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> list[str]:
    values = [tuple(row[field] for field in fields) for row in rows]
    counts = Counter(values)
    return ["|".join(map(str, value)) for value, count in counts.items() if count > 1]


def _common_quantities(
    contracts: Sequence[Mapping[str, Any]],
    lanes: Sequence[Mapping[str, Any]],
) -> tuple[float, float, float] | None:
    multiples = [max(1, round(contract["order_multiple"])) for contract in contracts]
    common_multiple = math.lcm(*multiples)
    minimum = max(contract["minimum_order_quantity"] for contract in contracts)
    maximum = min(lane["weekly_capacity"] for lane in lanes)
    low = math.ceil(minimum / common_multiple) * common_multiple
    high = math.floor(maximum / common_multiple) * common_multiple
    if high < low:
        return None
    mid = math.floor(((low + high) / 2) / common_multiple) * common_multiple
    return float(low), float(max(low, mid)), float(high)


def _indexes(
    network: Mapping[str, Sequence[Mapping[str, Any]]],
    commercial: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    nodes = {row["node_id"]: row for row in network["network_nodes.csv"]}
    materials = {row["material_id"]: row for row in network["materials.csv"]}
    approvals = {row["approval_id"]: row for row in network["material_flow_approvals.csv"]}
    contracts = {row["approval_id"]: row for row in commercial["supply_contracts.csv"]}
    terms = {row["incoterm_code"]: row for row in commercial["incoterm_rules.csv"]}
    fx = {(row["currency"], row["period_id"]): row["eur_per_currency_unit"] for row in commercial["fx_rates.csv"]}
    prices = {(row["contract_id"], row["material_id"], row["period_id"]): row for row in commercial["external_source_prices.csv"]}
    duties = {
        (row["origin_country_code"], row["destination_country_code"], row["material_family"]): row
        for row in commercial["import_duty_rates.csv"]
    }
    lanes_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for lane in commercial["shipping_lanes.csv"]:
        if lane["active_flag"]:
            lanes_by_pair[(lane["origin_node_id"], lane["destination_node_id"])].append(lane)
    inputs_by_recipe: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in network["transformation_inputs.csv"]:
        inputs_by_recipe[row["recipe_id"]].append(row)
    inbound: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in approvals.values():
        inbound[(approval["buyer_node_id"], approval["material_id"])].append(approval)
    conversion = {
        (row["node_id"], row["recipe_id"], row["period_id"]): row
        for row in commercial["conversion_costs.csv"]
    }
    baseline = {
        (row["node_id"], row["material_id"], row["period_id"]): row["standard_unit_cost_eur"]
        for row in commercial["baseline_standard_costs.csv"]
    }
    return {
        "nodes": nodes,
        "materials": materials,
        "approvals": approvals,
        "contracts": contracts,
        "terms": terms,
        "fx": fx,
        "prices": prices,
        "duties": duties,
        "lanes_by_pair": lanes_by_pair,
        "inputs_by_recipe": inputs_by_recipe,
        "inbound": inbound,
        "conversion": conversion,
        "baseline": baseline,
    }


def _quantity(contract: Mapping[str, Any], lane: Mapping[str, Any], band: str) -> float:
    if band == "LOW":
        return contract["minimum_order_quantity"]
    multiple = contract["order_multiple"]
    target = contract["minimum_order_quantity"] + multiple * (5 if band == "MID" else 20)
    return min(lane["weekly_capacity"], target)


def _landed_cost(
    idx: Mapping[str, Any],
    approval: Mapping[str, Any],
    period: str,
    source_cost: float | None,
    *,
    band: str = "MID",
    lane: Mapping[str, Any] | None = None,
    quantity: float | None = None,
) -> float:
    contract = idx["contracts"][approval["approval_id"]]
    material = idx["materials"][approval["material_id"]]
    seller = idx["nodes"][approval["seller_node_id"]]
    buyer = idx["nodes"][approval["buyer_node_id"]]
    if lane is None:
        lane = next(row for row in idx["lanes_by_pair"][(seller["node_id"], buyer["node_id"])] if not row["expedited_flag"])
    if seller["external_boundary_flag"]:
        price = idx["prices"][(contract["contract_id"], material["material_id"], period)]
        goods = price["unit_price"] * idx["fx"][(price["currency"], period)]
    elif source_cost is not None:
        goods = source_cost
    else:
        raise ValueError(f"missing internal source value for {approval['approval_id']}")
    q = quantity if quantity is not None else _quantity(contract, lane, band)
    term = idx["terms"][contract["incoterm_code"]]
    result = goods + contract["fixed_order_cost"] * idx["fx"][(contract["currency"], period)] / q
    freight = 0.0
    if term["buyer_pays_main_carriage"]:
        freight = lane["variable_freight_cost_per_unit"] * idx["fx"][(lane["freight_currency"], period)]
        result += freight + lane["fixed_shipment_cost"] * idx["fx"][(lane["freight_currency"], period)] / q
    if term["buyer_pays_insurance"]:
        result += goods * lane["insurance_rate_pct_of_goods"]
    if term["buyer_pays_import_duty"]:
        duty = idx["duties"][(seller["country_code"], buyer["country_code"], material["material_family"])]
        basis = goods + (freight if duty["customs_value_basis"] == "GOODS_PLUS_FREIGHT" else 0.0)
        result += basis * duty["duty_rate"]
    return result


def _propagate(
    network: Mapping[str, Sequence[Mapping[str, Any]]],
    commercial: Mapping[str, Sequence[Mapping[str, Any]]],
    idx: Mapping[str, Any],
    period: str,
    band: str,
) -> tuple[dict[tuple[str, str], float], dict[str, float]]:
    state_cost: dict[tuple[str, str], float] = {}
    approval_cost: dict[str, float] = {}
    for tier in ("TIER_3", "TIER_2", "TIER_1"):
        outputs: dict[tuple[str, str], list[float]] = defaultdict(list)
        for recipe in network["transformation_recipes.csv"]:
            if idx["nodes"][recipe["node_id"]]["node_tier"] != tier:
                continue
            input_total = 0.0
            for input_row in idx["inputs_by_recipe"][recipe["recipe_id"]]:
                options = []
                for approval in idx["inbound"][(recipe["node_id"], input_row["input_material_id"])]:
                    source = state_cost.get((approval["seller_node_id"], approval["material_id"]))
                    landed = _landed_cost(idx, approval, period, source, band=band)
                    approval_cost[approval["approval_id"]] = landed
                    options.append(landed)
                input_total += input_row["quantity_per_output"] / recipe["yield_rate"] * (sum(options) / len(options))
            row = idx["conversion"][(recipe["node_id"], recipe["recipe_id"], period)]
            rate = idx["fx"][(row["currency"], period)]
            run_quantity = max(recipe["minimum_run_quantity"], {"LOW": 25.0, "MID": 100.0, "HIGH": 400.0}[band])
            additions = (
                row["variable_conversion_cost_per_output"]
                + row["eligible_overhead_variable"]
                + (row["fixed_setup_cost"] + row["eligible_overhead_fixed"]) / run_quantity
            ) * rate
            outputs[(recipe["node_id"], recipe["output_material_id"])].append(
                (input_total + additions) * (1 + row["markup_rate"])
            )
        for state, values in outputs.items():
            state_cost[state] = sum(values) / len(values)
    for approval in idx["approvals"].values():
        if approval["approval_id"] not in approval_cost:
            source = state_cost.get((approval["seller_node_id"], approval["material_id"]))
            approval_cost[approval["approval_id"]] = _landed_cost(idx, approval, period, source, band=band)
    return state_cost, approval_cost


def _boundary_crossover_witnesses(idx: Mapping[str, Any]) -> list[dict[str, Any]]:
    pools: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in idx["approvals"].values():
        if idx["nodes"][approval["seller_node_id"]]["external_boundary_flag"]:
            pools[(approval["buyer_node_id"], approval["material_id"])].append(approval)
    witnesses: list[dict[str, Any]] = []
    for pool, approvals in sorted(pools.items()):
        if len(approvals) < 2:
            continue
        contracts = [idx["contracts"][approval["approval_id"]] for approval in approvals]
        lanes = [
            next(row for row in idx["lanes_by_pair"][(approval["seller_node_id"], approval["buyer_node_id"])] if not row["expedited_flag"])
            for approval in approvals
        ]
        quantities = _common_quantities(contracts, lanes)
        if quantities is None:
            continue
        low, mid, high = quantities
        low_cost = [_landed_cost(idx, approval, "P06", None, quantity=low) for approval in approvals]
        high_cost = [_landed_cost(idx, approval, "P06", None, quantity=high) for approval in approvals]
        if min(range(len(approvals)), key=low_cost.__getitem__) == min(range(len(approvals)), key=high_cost.__getitem__):
            continue
        witnesses.append(
            {
                "witness_id": f"CROSSOVER-{len(witnesses) + 1:03d}",
                "category": "FIXED_VARIABLE_CROSSOVER",
                "receiving_pool": f"{pool[0]}|{pool[1]}",
                "approval_ids": [row["approval_id"] for row in approvals],
                "quantities": {"low": low, "mid": mid, "high": high},
                "unit_cost_eur": {
                    "low": dict(zip((row["approval_id"] for row in approvals), (round(value, 6) for value in low_cost), strict=True)),
                    "high": dict(zip((row["approval_id"] for row in approvals), (round(value, 6) for value in high_cost), strict=True)),
                },
            }
        )
    return witnesses


def _expedited_witnesses(idx: Mapping[str, Any]) -> list[dict[str, Any]]:
    witnesses: list[dict[str, Any]] = []
    for pair, lanes in sorted(idx["lanes_by_pair"].items()):
        standard = [lane for lane in lanes if not lane["expedited_flag"]]
        expedited = [lane for lane in lanes if lane["expedited_flag"]]
        if not standard or not expedited:
            continue
        base, premium = standard[0], expedited[0]
        q = min(base["weekly_capacity"], premium["weekly_capacity"])
        base_logistics = base["variable_freight_cost_per_unit"] + base["fixed_shipment_cost"] / q
        premium_logistics = premium["variable_freight_cost_per_unit"] + premium["fixed_shipment_cost"] / q
        if premium["base_transit_days"] >= base["base_transit_days"] or premium_logistics < base_logistics * 1.05:
            continue
        approvals = [
            approval["approval_id"]
            for approval in idx["approvals"].values()
            if (approval["seller_node_id"], approval["buyer_node_id"]) == pair
        ]
        witnesses.append(
            {
                "witness_id": f"SERVICE-{len(witnesses) + 1:03d}",
                "category": "SPEED_RELIABILITY_PREMIUM",
                "node_pair": f"{pair[0]}|{pair[1]}",
                "approval_ids": approvals,
                "standard_lane_id": base["lane_id"],
                "expedited_lane_id": premium["lane_id"],
                "standard_transit_days": base["base_transit_days"],
                "expedited_transit_days": premium["base_transit_days"],
                "logistics_premium_pct": round((premium_logistics / base_logistics - 1) * 100, 2),
            }
        )
    return witnesses


def _contrast_witnesses(idx: Mapping[str, Any]) -> list[dict[str, Any]]:
    pools: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in idx["approvals"].values():
        pools[(approval["buyer_node_id"], approval["material_id"])].append(approval)
    witnesses = []
    for pool, approvals in sorted(pools.items()):
        countries = {idx["nodes"][row["seller_node_id"]]["country_code"] for row in approvals}
        currencies = {idx["contracts"][row["approval_id"]]["currency"] for row in approvals}
        duty_rates = {
            idx["duties"][
                (
                    idx["nodes"][row["seller_node_id"]]["country_code"],
                    idx["nodes"][row["buyer_node_id"]]["country_code"],
                    idx["materials"][row["material_id"]]["material_family"],
                )
            ]["duty_rate"]
            for row in approvals
        }
        if len(approvals) >= 2 and (len(countries) >= 2 or len(currencies) >= 2 or len(duty_rates) >= 2):
            witnesses.append(
                {
                    "witness_id": f"EXPOSURE-{len(witnesses) + 1:03d}",
                    "category": "TARIFF_FX_ORIGIN_CONTRAST",
                    "receiving_pool": f"{pool[0]}|{pool[1]}",
                    "approval_ids": [row["approval_id"] for row in approvals],
                    "seller_countries": sorted(countries),
                    "contract_currencies": sorted(currencies),
                    "duty_rates": sorted(duty_rates),
                }
            )
    return witnesses


def _cost_effect_witnesses(
    idx: Mapping[str, Any],
    state_cost: Mapping[tuple[str, str], float],
    approval_cost: Mapping[str, float],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pools: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in idx["approvals"].values():
        if not idx["nodes"][approval["seller_node_id"]]["external_boundary_flag"]:
            pools[(approval["buyer_node_id"], approval["material_id"])].append(approval)
    blend_witnesses: list[dict[str, Any]] = []
    reversal_witnesses: list[dict[str, Any]] = []
    for pool, approvals in sorted(pools.items()):
        if len(approvals) < 2:
            continue
        actual = {row["approval_id"]: approval_cost[row["approval_id"]] for row in approvals}
        values = list(actual.values())
        effect = (max(values) - min(values)) / (sum(values) / len(values))
        if effect >= 0.03:
            blend_witnesses.append(
                {
                    "witness_id": f"MIX-{len(blend_witnesses) + 1:03d}",
                    "category": "WEIGHTED_AVERAGE_MIX_EFFECT",
                    "receiving_pool": f"{pool[0]}|{pool[1]}",
                    "approval_ids": [row["approval_id"] for row in approvals],
                    "landed_unit_cost_eur": {key: round(value, 6) for key, value in actual.items()},
                    "spread_pct": round(effect * 100, 2),
                }
            )
        baseline_values = {}
        for approval in approvals:
            baseline_source = idx["baseline"][(approval["seller_node_id"], approval["material_id"], "P06")]
            baseline_values[approval["approval_id"]] = _landed_cost(idx, approval, "P06", baseline_source)
        if min(actual, key=actual.get) != min(baseline_values, key=baseline_values.get):
            reversal_witnesses.append(
                {
                    "witness_id": f"RANK-{len(reversal_witnesses) + 1:03d}",
                    "category": "BASELINE_RECURSIVE_RANKING_CONFLICT",
                    "receiving_pool": f"{pool[0]}|{pool[1]}",
                    "approval_ids": [row["approval_id"] for row in approvals],
                    "recursive_unit_cost_eur": {key: round(value, 6) for key, value in actual.items()},
                    "baseline_unit_cost_eur": {key: round(value, 6) for key, value in baseline_values.items()},
                }
            )
    return blend_witnesses, reversal_witnesses


def _dominance_review(
    idx: Mapping[str, Any],
    network: Mapping[str, Sequence[Mapping[str, Any]]],
    propagated: Mapping[str, tuple[Mapping[tuple[str, str], float], Mapping[str, float]]],
) -> tuple[list[dict[str, Any]], list[str]]:
    organisations = {row["supplier_id"]: row for row in network["supplier_organisations.csv"]}

    def ultimate_group(supplier_id: str | None) -> str:
        if supplier_id is None:
            return "ASTERION"
        current = supplier_id
        seen: set[str] = set()
        while current not in seen and organisations[current]["parent_group_id"] is not None:
            seen.add(current)
            current = organisations[current]["parent_group_id"]
        return current

    def exposure(approval: Mapping[str, Any]) -> tuple[str, str, str]:
        seller = idx["nodes"][approval["seller_node_id"]]
        return seller["country_code"], seller["region_code"], ultimate_group(seller["supplier_id"])

    pools: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in idx["approvals"].values():
        pools[(approval["buyer_node_id"], approval["material_id"])].append(approval)
    exceptions: list[dict[str, Any]] = []
    failures: list[str] = []
    for pool, approvals in sorted(pools.items()):
        if len(approvals) < 2:
            continue
        for first in approvals:
            for second in approvals:
                if first["approval_id"] == second["approval_id"]:
                    continue
                first_costs = [propagated[band][1][first["approval_id"]] for band in ("LOW", "MID", "HIGH")]
                second_costs = [propagated[band][1][second["approval_id"]] for band in ("LOW", "MID", "HIGH")]
                first_lane = next(row for row in idx["lanes_by_pair"][(first["seller_node_id"], first["buyer_node_id"])] if not row["expedited_flag"])
                second_lane = next(row for row in idx["lanes_by_pair"][(second["seller_node_id"], second["buyer_node_id"])] if not row["expedited_flag"])
                first_contract = idx["contracts"][first["approval_id"]]
                second_contract = idx["contracts"][second["approval_id"]]
                no_worse = (
                    all(left <= right + 1e-9 for left, right in zip(first_costs, second_costs, strict=True))
                    and first_lane["base_transit_days"] <= second_lane["base_transit_days"] + 1e-9
                    and first_lane["reliability_score"] >= second_lane["reliability_score"] - 1e-9
                    and first_contract["minimum_order_quantity"] <= second_contract["minimum_order_quantity"] + 1e-9
                )
                strictly_better = (
                    any(left < right - 1e-9 for left, right in zip(first_costs, second_costs, strict=True))
                    or first_lane["base_transit_days"] < second_lane["base_transit_days"] - 1e-9
                    or first_lane["reliability_score"] > second_lane["reliability_score"] + 1e-9
                    or first_contract["minimum_order_quantity"] < second_contract["minimum_order_quantity"] - 1e-9
                )
                if not (no_worse and strictly_better):
                    continue
                pool_id = f"{pool[0]}|{pool[1]}"
                if exposure(first) == exposure(second):
                    failures.append(f"{pool_id}|{first['approval_id']} dominates {second['approval_id']}")
                else:
                    exceptions.append(
                        {
                            "witness_id": f"DIVERSITY-{len(exceptions) + 1:03d}",
                            "category": "DOCUMENTED_DIVERSIFICATION_EXCEPTION",
                            "receiving_pool": pool_id,
                            "approval_ids": [first["approval_id"], second["approval_id"]],
                            "dominant_approval_id": first["approval_id"],
                            "retained_approval_id": second["approval_id"],
                            "dominant_exposure": exposure(first),
                            "retained_exposure": exposure(second),
                            "rationale": "The commercially dominated option retains a distinct country, region or ultimate-parent exposure for later disruption testing.",
                        }
                    )
    return exceptions, failures


def _validate_quote_build_up(
    price_build_up: Mapping[str, Any] | None,
    idx: Mapping[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    if price_build_up is None:
        _issue(issues, "PRICE_BUILD_UP_MISSING", "Private external-price build-up evidence is missing")
        return
    rows = price_build_up.get("rows", [])
    expected = len(idx["prices"])
    if len(rows) != expected:
        _issue(issues, "PRICE_BUILD_UP_COVERAGE", f"Expected {expected} price build-up rows, found {len(rows)}")
    for row in rows:
        components = row["components_eur_per_unit"]
        total = sum(components.values())
        if abs(total - row["quoted_unit_price_eur"]) > 1e-6:
            _issue(issues, "PRICE_BUILD_UP_TOTAL", "Seller-included price components do not sum to the quote", [row["contract_id"], row["period_id"]])
        term = idx["terms"][row["incoterm_code"]]
        checks = (
            ("seller_main_carriage", term["buyer_pays_main_carriage"]),
            ("seller_insurance", term["buyer_pays_insurance"]),
            ("seller_import_duty", term["buyer_pays_import_duty"]),
        )
        for component, buyer_pays in checks:
            if buyer_pays and abs(components[component]) > 1e-12:
                _issue(issues, "SELLER_COMPONENT_DUPLICATION", "Buyer-borne component was also embedded in the seller quote", [row["contract_id"], row["period_id"], component])


def assess_tables(
    network: Mapping[str, Sequence[Mapping[str, Any]]],
    commercial: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    price_build_up: Mapping[str, Any] | None = None,
    lineage_witnesses: Mapping[str, Any] | None = None,
    data_checksums: Mapping[str, str] | None = None,
) -> Assessment:
    issues: list[dict[str, Any]] = []
    idx = _indexes(network, commercial)
    approvals = list(idx["approvals"].values())
    contracts = list(commercial["supply_contracts.csv"])

    primary_keys = {
        "supply_contracts.csv": ("contract_id",),
        "incoterm_rules.csv": ("incoterm_code",),
        "import_duty_rates.csv": ("duty_rule_id",),
        "shipping_lanes.csv": ("lane_id",),
        "external_source_prices.csv": ("contract_id", "material_id", "period_id"),
        "conversion_costs.csv": ("node_id", "recipe_id", "period_id"),
        "cost_allocation_rules.csv": ("cost_rule_id",),
        "fx_rates.csv": ("currency", "period_id"),
        "baseline_standard_costs.csv": ("node_id", "material_id", "period_id"),
    }
    for file_name, fields in primary_keys.items():
        duplicates = _duplicates(commercial[file_name], fields)
        if duplicates:
            _issue(issues, "DUPLICATE_KEY", f"{file_name} has duplicate keys", duplicates)

    contracts_by_approval: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for contract in contracts:
        contracts_by_approval[contract["approval_id"]].append(contract)
    contract_failures = [
        approval["approval_id"]
        for approval in approvals
        if len(contracts_by_approval[approval["approval_id"]]) != 1
    ]
    if contract_failures:
        _issue(issues, "CONTRACT_COVERAGE", "Each approval must have exactly one active contract", contract_failures)

    pair_approvals: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in approvals:
        pair_approvals[(approval["seller_node_id"], approval["buyer_node_id"])].append(approval)
    lane_failures = ["|".join(pair) for pair in pair_approvals if not idx["lanes_by_pair"].get(pair)]
    if lane_failures:
        _issue(issues, "LANE_COVERAGE", "Every active node pair requires a lane", lane_failures)

    for pair, pair_rows in pair_approvals.items():
        if any(row["approval_id"] not in idx["contracts"] for row in pair_rows):
            continue
        terms = {idx["contracts"][row["approval_id"]]["incoterm_code"] for row in pair_rows}
        responsibility = {
            (
                idx["terms"][term]["buyer_pays_main_carriage"],
                idx["terms"][term]["buyer_pays_insurance"],
                idx["terms"][term]["buyer_pays_import_duty"],
            )
            for term in terms
        }
        if len(responsibility) != 1:
            _issue(issues, "PAIR_INCOTERM_CONFLICT", "Contracts sharing a node pair have incompatible cost responsibility", ["|".join(pair)])
        seller_is_boundary = idx["nodes"][pair[0]]["external_boundary_flag"]
        if not seller_is_boundary and not terms <= {"EXW", "FCA"}:
            _issue(issues, "INTERNAL_SELLER_CARRIAGE", "Internal processing-node contracts must use EXW or FCA", ["|".join(pair), *terms])
        buyer_main = all(idx["terms"][term]["buyer_pays_main_carriage"] for term in terms)
        if not buyer_main and len(idx["lanes_by_pair"][pair]) != 1:
            _issue(issues, "SELLER_CARRIAGE_LANE_AMBIGUITY", "Seller-carriage pair must have one active lane", ["|".join(pair)])

    price_keys_by_contract: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in commercial["external_source_prices.csv"]:
        price_keys_by_contract[row["contract_id"]].add((row["material_id"], row["period_id"]))
    boundary_contract_ids: set[str] = set()
    boundary_price_failures: list[str] = []
    internal_price_failures: list[str] = []
    for approval in approvals:
        matching_contracts = contracts_by_approval[approval["approval_id"]]
        if len(matching_contracts) != 1:
            continue
        contract = matching_contracts[0]
        keys = price_keys_by_contract[contract["contract_id"]]
        if idx["nodes"][approval["seller_node_id"]]["external_boundary_flag"]:
            boundary_contract_ids.add(contract["contract_id"])
            expected = {(approval["material_id"], period) for period in PERIODS}
            if keys != expected:
                boundary_price_failures.append(contract["contract_id"])
        elif keys:
            internal_price_failures.append(contract["contract_id"])
    if boundary_price_failures:
        _issue(issues, "BOUNDARY_PRICE_COVERAGE", "Boundary contract price periods are incomplete", boundary_price_failures)
    if internal_price_failures:
        _issue(issues, "NONBOUNDARY_EXTERNAL_PRICE", "Non-boundary contract has an external price", internal_price_failures)

    expected_duties = {
        (
            idx["nodes"][row["seller_node_id"]]["country_code"],
            idx["nodes"][row["buyer_node_id"]]["country_code"],
            idx["materials"][row["material_id"]]["material_family"],
        )
        for row in approvals
    }
    if set(idx["duties"]) != expected_duties:
        _issue(issues, "DUTY_COVERAGE", "Duty-rule tuples differ from required approval tuples")

    currencies = {node["local_currency"] for node in idx["nodes"].values()}
    expected_fx = {(currency, period) for currency in currencies for period in PERIODS}
    if set(idx["fx"]) != expected_fx:
        _issue(issues, "FX_COVERAGE", "FX rows do not cover every node currency and period")
    for period in PERIODS:
        if idx["fx"].get(("EUR", period)) != 1.0:
            _issue(issues, "EUR_FX", "EUR must equal one in every period", [period])

    expected_conversion = {
        (recipe["node_id"], recipe["recipe_id"], period)
        for recipe in network["transformation_recipes.csv"]
        for period in PERIODS
    }
    if set(idx["conversion"]) != expected_conversion:
        _issue(issues, "CONVERSION_COVERAGE", "Conversion rows do not cover every recipe-period")

    expected_baseline = {
        (approval["seller_node_id"], approval["material_id"], period)
        for approval in approvals
        if not idx["nodes"][approval["seller_node_id"]]["external_boundary_flag"]
        for period in PERIODS
    }
    if set(idx["baseline"]) != expected_baseline:
        _issue(issues, "BASELINE_COVERAGE", "Baseline standard costs do not cover every intermediate seller state-period")
    bad_baseline = [
        f"{row['node_id']}|{row['material_id']}|{row['period_id']}"
        for row in commercial["baseline_standard_costs.csv"]
        if not row["baseline_only_flag"] or not row["prohibited_for_recursive_model_flag"]
    ]
    if bad_baseline:
        _issue(issues, "BASELINE_ISOLATION", "Baseline isolation flags must both be true", bad_baseline)

    rules = commercial["cost_allocation_rules.csv"]
    global_rules = [row for row in rules if row["scope_type"] == "GLOBAL"]
    components = set(load_config()["cost_policy"]["capitalised_components"]) | set(load_config()["cost_policy"]["noncapitalised_components"])
    global_counts = Counter(row["cost_component"] for row in global_rules)
    if set(global_counts) != components or any(count != 1 for count in global_counts.values()):
        _issue(issues, "COST_RULE_GLOBAL_COVERAGE", "Every controlled component needs exactly one global rule")
    rule_ties = _duplicates(rules, ("cost_component", "scope_type", "scope_id", "precedence"))
    if rule_ties:
        _issue(issues, "COST_RULE_PRECEDENCE_TIE", "Cost-rule scope and precedence ties are invalid", rule_ties)
    markup_components = {row["cost_component"] for row in rules if row["scope_type"] == "GLOBAL" and row["markup_eligible_flag"]}
    if markup_components != {"CONVERSION", "SETUP", "OVERHEAD"}:
        _issue(issues, "MARKUP_BASE", "Only conversion, setup and overhead may be markup-eligible", markup_components)

    p06_fx = {currency: rate for (currency, period), rate in idx["fx"].items() if period == "P06"}
    fixed_order_eur = [row["fixed_order_cost"] * p06_fx[row["currency"]] for row in contracts]
    activation_eur = [row["horizon_activation_cost"] * p06_fx[row["currency"]] for row in contracts]
    markup_rates = [row["markup_rate"] for row in commercial["conversion_costs.csv"]]
    duty_rates = [row["duty_rate"] for row in commercial["import_duty_rates.csv"]]
    insurance_rates = [row["insurance_rate_pct_of_goods"] for row in commercial["shipping_lanes.csv"]]
    reliability = [row["reliability_score"] for row in commercial["shipping_lanes.csv"]]
    external_price_eur = [
        row["unit_price"] * idx["fx"][(row["currency"], row["period_id"])]
        for row in commercial["external_source_prices.csv"]
    ]
    conversion_eur = [
        row["variable_conversion_cost_per_output"] * idx["fx"][(row["currency"], row["period_id"])]
        for row in commercial["conversion_costs.csv"]
    ]
    fx_by_currency: dict[str, list[float]] = defaultdict(list)
    for (currency, _), rate in idx["fx"].items():
        fx_by_currency[currency].append(rate)
    max_fx_movement = max(max(values) / min(values) - 1 for values in fx_by_currency.values())
    range_profile = {
        "fixed_order_cost_eur": {"minimum": min(fixed_order_eur), "maximum": max(fixed_order_eur)},
        "horizon_activation_cost_eur": {"minimum": min(activation_eur), "maximum": max(activation_eur)},
        "external_unit_price_eur": {"minimum": min(external_price_eur), "maximum": max(external_price_eur)},
        "variable_conversion_cost_eur": {"minimum": min(conversion_eur), "maximum": max(conversion_eur)},
        "markup_rate": {"minimum": min(markup_rates), "maximum": max(markup_rates)},
        "duty_rate": {"minimum": min(duty_rates), "maximum": max(duty_rates)},
        "insurance_rate": {"minimum": min(insurance_rates), "maximum": max(insurance_rates)},
        "lane_reliability": {"minimum": min(reliability), "maximum": max(reliability)},
        "maximum_twelve_period_fx_movement": max_fx_movement,
    }
    plausibility_failures: list[str] = []
    controls = (
        (0.03 <= min(markup_rates) <= max(markup_rates) <= 0.18, "markup_rate outside 3%–18%"),
        (0.0 <= min(duty_rates) <= max(duty_rates) <= 0.15, "duty_rate outside 0%–15%"),
        (0.001 <= min(insurance_rates) <= max(insurance_rates) <= 0.02, "insurance_rate outside 0.1%–2%"),
        (70.0 <= min(reliability) <= max(reliability) <= 99.0, "lane reliability outside 70–99"),
        (max(fixed_order_eur) <= 7500.0, "fixed order cost exceeds EUR 7,500"),
        (max(activation_eur) <= 5000.0, "horizon activation cost exceeds EUR 5,000"),
        (max_fx_movement <= 0.06, "twelve-period FX movement exceeds 6%"),
        (min(external_price_eur) > 0 and min(conversion_eur) >= 0, "price or conversion value is negative"),
    )
    plausibility_failures.extend(message for passed, message in controls if not passed)
    if plausibility_failures:
        _issue(issues, "PLAUSIBILITY_RANGE", "One or more synthetic business-range controls failed", plausibility_failures)

    _validate_quote_build_up(price_build_up, idx, issues)

    if issues:
        metric = _metric(
            "semantic_integrity",
            "Commercial contract and accounting integrity",
            len(issues),
            "0",
            False,
            failures=(issue["code"] for issue in issues),
        )
        scorecard = {
            "status": "FAIL",
            "configuration_version": load_config()["configuration_version"],
            "metrics": [metric],
            "issues": issues,
            "range_profile": range_profile,
            "data_checksums": dict(sorted((data_checksums or {}).items())),
        }
        report = _report(scorecard, commercial, (), (), (), (), (), ())
        return Assessment(
            scorecard,
            {"definition": "No trade-off assessment is valid until semantic integrity passes.", "witnesses": [], "terminal_witness_counts": {}},
            {"status": "NOT_ASSESSED_DUE_TO_SEMANTIC_FAILURE", "state_envelopes": {}},
            report,
        )

    envelopes: dict[str, Any] = {}
    propagated: dict[str, tuple[dict[tuple[str, str], float], dict[str, float]]] = {}
    for band in ("LOW", "MID", "HIGH"):
        propagated[band] = _propagate(network, commercial, idx, "P06", band)
    states = sorted(set(propagated["MID"][0]))
    for state in states:
        values = {band.lower(): propagated[band][0][state] for band in ("LOW", "MID", "HIGH")}
        envelopes[f"{state[0]}|{state[1]}|P06"] = {
            "unit_value_eur": {key: round(value, 6) for key, value in values.items()},
            "minimum": round(min(values.values()), 6),
            "maximum": round(max(values.values()), 6),
        }

    crossovers = _boundary_crossover_witnesses(idx)
    service = _expedited_witnesses(idx)
    contrasts = _contrast_witnesses(idx)
    blend, reversals = _cost_effect_witnesses(idx, *propagated["MID"])
    dominance_exceptions, dominance_failures = _dominance_review(idx, network, propagated)
    if dominance_failures:
        _issue(issues, "UNEXPLAINED_DOMINANCE", "An active option is strictly dominated without a distinct recorded dependency exposure", dominance_failures)
    all_witnesses = [*crossovers, *service, *contrasts, *blend, *reversals, *dominance_exceptions]

    approval_terminal_coverage: Mapping[str, Sequence[str]] = {}
    if lineage_witnesses is not None:
        approval_terminal_coverage = lineage_witnesses["participation_index"]["entities"]["approvals"]
    terminal_counts: Counter[str] = Counter()
    for witness in all_witnesses:
        terminals = sorted(
            {
                terminal
                for approval_id in witness["approval_ids"]
                for terminal in approval_terminal_coverage.get(approval_id, [])
            }
        )
        witness["supported_terminal_material_ids"] = terminals
        terminal_counts.update(terminals)
    terminal_materials = sorted(
        row["material_id"]
        for row in network["materials.csv"]
        if row["terminal_material_flag"]
    )
    undercovered_terminals = [terminal for terminal in terminal_materials if terminal_counts[terminal] < 2]

    expedited_pairs = [pair for pair, pair_lanes in idx["lanes_by_pair"].items() if any(row["expedited_flag"] for row in pair_lanes)]
    asia_europe_expedited = [
        "|".join(pair)
        for pair in expedited_pairs
        if {idx["nodes"][pair[0]]["region_code"].split("_")[0], idx["nodes"][pair[1]]["region_code"].split("_")[0]} == {"ASIA", "EUROPE"}
    ]

    metrics = [
        _metric("contract_coverage", "Approved flows with exactly one active contract", len(approvals) - len(contract_failures), f"{len(approvals)}", not contract_failures, failures=contract_failures),
        _metric("lane_coverage", "Active node pairs with a standard lane", len(pair_approvals) - len(lane_failures), f"{len(pair_approvals)}", not lane_failures, failures=lane_failures),
        _metric("boundary_price_coverage", "Boundary contracts with twelve period prices", len(boundary_contract_ids) - len(boundary_price_failures), f"{len(boundary_contract_ids)}", not boundary_price_failures, failures=boundary_price_failures),
        _metric("nonboundary_external_prices", "Intermediate contracts with external prices", len(internal_price_failures), "0", not internal_price_failures, failures=internal_price_failures),
        _metric("conversion_coverage", "Recipe-period conversion rows", len(idx["conversion"]), str(len(expected_conversion)), set(idx["conversion"]) == expected_conversion),
        _metric("fx_coverage", "Currency-period FX rows", len(idx["fx"]), str(len(expected_fx)), set(idx["fx"]) == expected_fx),
        _metric("baseline_coverage", "Intermediate state-period comparator rows", len(idx["baseline"]), str(len(expected_baseline)), set(idx["baseline"]) == expected_baseline),
        _metric("commercial_lineage_coverage", "Terminal materials retaining commercialised structural lineages", len(terminal_materials), str(len(terminal_materials)), not contract_failures and not lane_failures and not boundary_price_failures),
        _metric("tradeoff_witnesses", "Distinct retained commercial trade-off witnesses", len(all_witnesses), ">= 16", len(all_witnesses) >= 16, witnesses=(row["witness_id"] for row in all_witnesses)),
        _metric("terminal_witness_coverage", "Terminal materials supported by at least two trade-off witnesses", len(terminal_materials) - len(undercovered_terminals), str(len(terminal_materials)), not undercovered_terminals, failures=undercovered_terminals),
        _metric("fixed_variable_crossovers", "Fixed/variable ranking crossovers", len(crossovers), ">= 4", len(crossovers) >= 4, witnesses=(row["witness_id"] for row in crossovers)),
        _metric("service_premiums", "Faster options carrying a logistics premium", len(service), ">= 4", len(service) >= 4, witnesses=(row["witness_id"] for row in service)),
        _metric("exposure_contrasts", "Tariff, FX or origin contrasts", len(contrasts), ">= 4", len(contrasts) >= 4, witnesses=(row["witness_id"] for row in contrasts)),
        _metric("pool_mix_effects", "Intermediate pools with material weighted-average cost sensitivity", len(blend), ">= 4", len(blend) >= 4, witnesses=(row["witness_id"] for row in blend)),
        _metric("baseline_recursive_conflicts", "Baseline-versus-recursive ranking conflicts", len(reversals), ">= 4", len(reversals) >= 4, witnesses=(row["witness_id"] for row in reversals)),
        _metric("expedited_corridors", "Corridors with expedited alternatives", len(expedited_pairs), "8–16", 8 <= len(expedited_pairs) <= 16, witnesses=("|".join(pair) for pair in expedited_pairs)),
        _metric("asia_europe_expedited", "Asia–Europe corridors with expedited alternatives", len(asia_europe_expedited), ">= 2", len(asia_europe_expedited) >= 2, witnesses=asia_europe_expedited),
        _metric("unexplained_dominance", "Strictly dominated options without a diversification rationale", len(dominance_failures), "0", not dominance_failures, failures=dominance_failures),
        _metric("documented_dominance_exceptions", "Commercially dominated options retained for distinct dependency exposure", len(dominance_exceptions), "review", True, witnesses=(row["witness_id"] for row in dominance_exceptions)),
        _metric("plausibility_ranges", "Synthetic commercial range controls outside their review bands", len(plausibility_failures), "0", not plausibility_failures, failures=plausibility_failures),
        _metric("accounting_issues", "Cost disappearance, duplication or rule ambiguity", len(issues), "0", not issues, failures=(issue["code"] for issue in issues)),
    ]
    status = "PASS" if not issues and all(metric["passed"] for metric in metrics) else "FAIL"
    scorecard = {
        "status": status,
        "configuration_version": load_config()["configuration_version"],
        "metrics": metrics,
        "issues": issues,
        "range_profile": range_profile,
        "data_checksums": dict(sorted((data_checksums or {}).items())),
    }
    tradeoffs = {
        "definition": "Commercial witnesses identify potential decisions without selecting a network allocation.",
        "witnesses": all_witnesses,
        "terminal_witness_counts": dict(sorted(terminal_counts.items())),
    }
    envelope_output = {
        "status": "CONDITIONAL_NOT_FORMULATION_BOUNDS",
        "period_id": "P06",
        "quantity_bands": ["LOW", "MID", "HIGH"],
        "state_envelopes": envelopes,
        "wp7_handoff": "Combine these cost ranges with WP6 capacity, demand, storage and opening inventory before deriving formulation bounds.",
    }
    report = _report(scorecard, commercial, crossovers, service, contrasts, blend, reversals, undercovered_terminals)
    return Assessment(scorecard, tradeoffs, envelope_output, report)


def _report(
    scorecard: Mapping[str, Any],
    commercial: Mapping[str, Sequence[Mapping[str, Any]]],
    crossovers: Sequence[Mapping[str, Any]],
    service: Sequence[Mapping[str, Any]],
    contrasts: Sequence[Mapping[str, Any]],
    blend: Sequence[Mapping[str, Any]],
    reversals: Sequence[Mapping[str, Any]],
    undercovered_terminals: Sequence[str],
) -> str:
    lines = [
        "# CAP-001 Commercial and Economic Report",
        "",
        "## Outcome",
        "",
        f"Commercial assessment status: **{scorecard['status']}**.",
        "",
        "This report assesses dataset coverage, accounting coherence and the presence of potential commercial trade-offs. It does not contain an optimised allocation or claim BASE feasibility.",
        "",
        "## Candidate profile",
        "",
        "| Dataset | Rows |",
        "|---|---:|",
    ]
    for file_name in COMMERCIAL_FILES:
        lines.append(f"| `{file_name}` | {len(commercial[file_name])} |")
    lines.extend(
        [
            "",
            "## Decision-depth evidence",
            "",
            f"- Fixed/variable crossovers: {len(crossovers)}",
            f"- Speed or reliability premiums: {len(service)}",
            f"- Tariff, FX or origin contrasts: {len(contrasts)}",
            f"- Intermediate weighted-average mix effects: {len(blend)}",
            f"- Baseline-versus-recursive ranking conflicts: {len(reversals)}",
            f"- Terminal materials below witness coverage: {', '.join(undercovered_terminals) if undercovered_terminals else 'none'}",
            "",
            "## Plausibility range profile",
            "",
            "| Measure | Minimum | Maximum |",
            "|---|---:|---:|",
            *(
                f"| {name.replace('_', ' ')} | {values['minimum']:.6g} | {values['maximum']:.6g} |"
                for name, values in scorecard["range_profile"].items()
                if isinstance(values, dict)
            ),
            f"| Maximum twelve-period FX movement | — | {scorecard['range_profile']['maximum_twelve_period_fx_movement']:.2%} |",
            "",
            "## Interpretation",
            "",
            "The witnesses establish that the commercial facts are not decorative and that reasonable alternatives can trade cost against lot size, transport service or exposure. They are calibration evidence only. WP6 must add demand, capacity, inventory and disruptions; WP7 must then test feasibility, scenario materiality and solved decision differences.",
            "",
            "## Gate results",
            "",
            "| Gate | Value | Threshold | Result |",
            "|---|---:|---:|---|",
        ]
    )
    for metric in scorecard["metrics"]:
        lines.append(f"| {metric['label']} | {metric['value']} | {metric['threshold']} | {'PASS' if metric['passed'] else 'FAIL'} |")
    if scorecard["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in scorecard["issues"]:
            lines.append(f"- `{issue['code']}` — {issue['message']}")
    return "\n".join(lines).rstrip() + "\n"


def assess_paths(
    network_dir: Path = DEFAULT_NETWORK_DIR,
    commercial_dir: Path = DEFAULT_COMMERCIAL_DIR,
) -> Assessment:
    config = load_config()
    network, commercial = load_tables(network_dir, commercial_dir, config)
    price_path = commercial_dir / "evidence" / "external_price_build_up.json"
    lineage_path = network_dir / "evidence" / "lineage_witnesses.json"
    price_build_up = json.loads(price_path.read_text()) if price_path.is_file() else None
    lineage = json.loads(lineage_path.read_text()) if lineage_path.is_file() else None
    checksums = {
        f"network/{file_name}": sha256_path(network_dir / "data" / file_name)
        for file_name in NETWORK_FILES
    }
    checksums.update(
        {
            f"commercial/{file_name}": sha256_path(commercial_dir / "data" / file_name)
            for file_name in COMMERCIAL_FILES
        }
    )
    return assess_tables(
        network,
        commercial,
        price_build_up=price_build_up,
        lineage_witnesses=lineage,
        data_checksums=checksums,
    )


def render_evidence(assessment: Assessment) -> dict[str, str]:
    return {
        "commercial_depth_scorecard.json": canonical_json(assessment.scorecard),
        "tradeoff_witnesses.json": canonical_json(assessment.tradeoff_witnesses),
        "conditional_cost_envelopes.json": canonical_json(assessment.conditional_cost_envelopes),
        "COMMERCIAL_ECONOMIC_REPORT.md": assessment.report,
    }


def write_evidence(commercial_dir: Path, assessment: Assessment) -> None:
    evidence_dir = commercial_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for file_name, content in render_evidence(assessment).items():
        (evidence_dir / file_name).write_text(content, encoding="utf-8", newline="")


def check_evidence(commercial_dir: Path, assessment: Assessment) -> list[str]:
    return [
        file_name
        for file_name, content in render_evidence(assessment).items()
        if not (commercial_dir / "evidence" / file_name).is_file()
        or (commercial_dir / "evidence" / file_name).read_text(encoding="utf-8") != content
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network-dir", type=Path, default=DEFAULT_NETWORK_DIR)
    parser.add_argument("--commercial-dir", type=Path, default=DEFAULT_COMMERCIAL_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    assessment = assess_paths(args.network_dir.resolve(), args.commercial_dir.resolve())
    if args.check:
        drift = check_evidence(args.commercial_dir.resolve(), assessment)
        if drift:
            print("Commercial evidence drift: " + ", ".join(drift), file=sys.stderr)
            return 1
    else:
        write_evidence(args.commercial_dir.resolve(), assessment)
    if not assessment.passed:
        print("Commercial assessment failed.", file=sys.stderr)
        for metric in assessment.scorecard["metrics"]:
            if not metric["passed"]:
                print(f"  {metric['metric_id']}: {metric['value']} (requires {metric['threshold']})", file=sys.stderr)
        for issue in assessment.scorecard["issues"]:
            print(f"  {issue['code']}: {issue['message']}", file=sys.stderr)
        return 1
    print(f"Commercial assessment passed ({len(assessment.scorecard['metrics'])} gates).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
