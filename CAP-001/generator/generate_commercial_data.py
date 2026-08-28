#!/usr/bin/env python3
"""Generate deterministic commercial facts for the accepted CAP-001 network."""

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
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.contract_runtime import (  # noqa: E402
    canonical_json,
    coerce_csv_value,
    load_config,
    sha256_bytes,
    validate_csv_file,
)


DEFAULT_NETWORK_DIR = ROOT / "generated" / "network"
DEFAULT_OUTPUT_DIR = ROOT / "generated" / "commercial"
DEFAULT_MASTER_SEED = 26022027
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
)


FX_BASE_EUR = {
    "BRL": 0.17,
    "CAD": 0.68,
    "CZK": 0.040,
    "EUR": 1.0,
    "GBP": 1.17,
    "INR": 0.011,
    "JPY": 0.0061,
    "KRW": 0.00068,
    "MAD": 0.091,
    "MXN": 0.054,
    "MYR": 0.196,
    "PLN": 0.23,
    "RON": 0.20,
    "SEK": 0.089,
    "TRY": 0.028,
    "USD": 0.92,
    "VND": 0.000036,
    "ZAR": 0.049,
}
FAMILY_GOODS_EUR = {
    "CONDUCTOR": 8.5,
    "MAGNETIC": 13.0,
    "POWER_ELECTRONICS": 48.0,
    "MOTION": 10.0,
    "INSULATION": 5.5,
    "HOUSING": 7.0,
    "SENSING": 30.0,
    "CONTROL": 22.0,
}
EU_COUNTRIES = {"DE", "PL", "ES", "FR", "CZ", "IT", "NL", "SE", "RO"}
NORTH_AMERICA = {"US", "CA", "MX"}


@dataclass(frozen=True)
class Candidate:
    tables: dict[str, list[dict[str, Any]]]
    external_price_build_up: list[dict[str, Any]]
    generation_targets: dict[str, Any]


def namespace_seed(master_seed: int, namespace: str) -> int:
    digest = hashlib.sha256(f"{master_seed}:{namespace}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def stable_fraction(master_seed: int, namespace: str, key: str) -> float:
    digest = hashlib.sha256(f"{master_seed}:{namespace}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def _between(master_seed: int, namespace: str, key: str, lower: float, upper: float) -> float:
    return lower + stable_fraction(master_seed, namespace, key) * (upper - lower)


def _read_typed_csv(path: Path, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    validate_csv_file(path, contract)
    fields = {field["name"]: field for field in contract["columns"]}
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {name: coerce_csv_value(value, fields[name]) for name, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def load_network(network_dir: Path = DEFAULT_NETWORK_DIR) -> dict[str, list[dict[str, Any]]]:
    config = load_config()
    data_dir = network_dir / "data"
    return {
        file_name: _read_typed_csv(data_dir / file_name, config["raw_contracts"][file_name])
        for file_name in NETWORK_FILES
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


def _haversine_km(origin: Mapping[str, Any], destination: Mapping[str, Any]) -> float:
    radius = 6371.0088
    lat1, lon1 = math.radians(origin["latitude"]), math.radians(origin["longitude"])
    lat2, lon2 = math.radians(destination["latitude"]), math.radians(destination["longitude"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _incoterms() -> list[dict[str, Any]]:
    disclaimer = "This capstone Incoterm abstraction is not legal guidance."
    definitions = (
        ("EXW", "Buyer controls collection and onward movement.", True, True, True, True, "SELLER_SITE"),
        ("FCA", "Seller completes simplified origin handover; buyer controls main carriage.", False, True, True, True, "ORIGIN_HANDOVER"),
        ("CPT", "Seller pays main carriage; buyer bears insurance and import duty.", False, False, True, True, "ORIGIN_CARRIER"),
        ("CIP", "Seller pays main carriage and insurance; buyer bears import duty.", False, False, False, True, "ORIGIN_CARRIER"),
        ("DAP", "Seller pays carriage and insurance to destination; buyer bears import duty.", False, False, False, True, "DESTINATION_BEFORE_IMPORT"),
        ("DDP", "Seller pays carriage, insurance and import duty to destination.", False, False, False, False, "DESTINATION_DUTY_PAID"),
    )
    return [
        {
            "incoterm_code": code,
            "description": description,
            "buyer_pays_origin_transport": origin,
            "buyer_pays_main_carriage": carriage,
            "buyer_pays_insurance": insurance,
            "buyer_pays_import_duty": duty,
            "risk_transfer_stage": risk,
            "active_flag": True,
            "legal_disclaimer": disclaimer,
        }
        for code, description, origin, carriage, insurance, duty, risk in definitions
    ]


def _fx_rates(master_seed: int, nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    currencies = sorted({node["local_currency"] for node in nodes})
    missing = set(currencies) - set(FX_BASE_EUR)
    if missing:
        raise ValueError(f"missing controlled FX bases: {sorted(missing)}")
    rows: list[dict[str, Any]] = []
    for currency in currencies:
        slope = _between(master_seed, "fx-slope", currency, -0.018, 0.018)
        curve = _between(master_seed, "fx-curve", currency, -0.006, 0.006)
        for period_number, period in enumerate(PERIODS, start=1):
            centered = (period_number - 6.5) / 5.5
            rate = 1.0 if currency == "EUR" else FX_BASE_EUR[currency] * (1 + slope * centered + curve * math.sin(period_number / 2))
            rows.append(
                {
                    "currency": currency,
                    "period_id": period,
                    "eur_per_currency_unit": round(rate, 9),
                    "rate_source": "SYNTHETIC_FIXED",
                    "scenario_sensitive_flag": currency != "EUR",
                }
            )
    return rows


def _contract_terms(
    master_seed: int,
    approvals: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
    fx: Mapping[tuple[str, str], float],
) -> tuple[list[dict[str, Any]], list[str]]:
    boundary_pairs = sorted(
        {
            (row["seller_node_id"], row["buyer_node_id"])
            for row in approvals
            if nodes[row["seller_node_id"]]["external_boundary_flag"]
        }
    )
    boundary_codes = ("EXW", "FCA", "CPT", "CIP", "DAP", "DDP")
    pair_code = {pair: boundary_codes[index % len(boundary_codes)] for index, pair in enumerate(boundary_pairs)}
    for pair in sorted({(row["seller_node_id"], row["buyer_node_id"]) for row in approvals} - set(boundary_pairs)):
        pair_code[pair] = "EXW" if stable_fraction(master_seed, "internal-incoterm", "|".join(pair)) < 0.5 else "FCA"

    pools: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in approvals:
        if nodes[approval["seller_node_id"]]["external_boundary_flag"]:
            pools[(approval["buyer_node_id"], approval["material_id"])].append(approval)
    for pool_rows in pools.values():
        if len(pool_rows) < 2:
            continue
        for option_index, approval in enumerate(sorted(pool_rows, key=lambda row: row["approval_id"])):
            pair_code[(approval["seller_node_id"], approval["buyer_node_id"])] = "EXW" if option_index % 2 == 0 else "FCA"
    crossover_pools = [
        f"{buyer}|{material}"
        for (buyer, material), rows in sorted(
            pools.items(),
            key=lambda item: (FAMILY_GOODS_EUR[materials[item[0][1]]["material_family"]], item[0]),
        )
        if len(rows) >= 2
    ][:4]
    crossover_set = set(crossover_pools)

    rows: list[dict[str, Any]] = []
    for index, approval in enumerate(sorted(approvals, key=lambda row: row["approval_id"]), start=1):
        seller = nodes[approval["seller_node_id"]]
        material = materials[approval["material_id"]]
        currency = seller["local_currency"]
        key = f"{approval['buyer_node_id']}|{approval['material_id']}"
        if material["uom"] == "KG":
            multiple = (100.0, 200.0, 250.0)[int(stable_fraction(master_seed, "lot", approval["approval_id"]) * 3) % 3]
            moq = multiple * (1 + int(stable_fraction(master_seed, "moq", approval["approval_id"]) * 3))
        else:
            multiple = (5.0, 10.0, 20.0)[int(stable_fraction(master_seed, "lot", approval["approval_id"]) * 3) % 3]
            moq = multiple * (2 + int(stable_fraction(master_seed, "moq", approval["approval_id"]) * 4))
        fixed_eur = _between(master_seed, "fixed-order", approval["approval_id"], 100.0, 650.0)
        if key in crossover_set:
            fixed_eur = 90.0
        activation_eur = _between(master_seed, "activation", approval["approval_id"], 500.0, 2800.0)
        rows.append(
            {
                "contract_id": f"CTR-{index:05d}",
                "approval_id": approval["approval_id"],
                "currency": currency,
                "incoterm_code": pair_code[(approval["seller_node_id"], approval["buyer_node_id"])],
                "contract_handling_days": int(_between(master_seed, "handling", approval["approval_id"], 1, 6)),
                "minimum_order_quantity": moq,
                "order_multiple": multiple,
                "fixed_order_cost": round(fixed_eur / fx[(currency, "P06")], 4),
                "horizon_activation_cost": round(activation_eur / fx[(currency, "P06")], 4),
                "payment_terms_days": (30, 45, 60)[int(stable_fraction(master_seed, "payment", approval["approval_id"]) * 3) % 3],
                "effective_from_period": "P01",
                "effective_to_period": "P12",
                "active_flag": True,
            }
        )
    return rows, crossover_pools


def _mode(origin: Mapping[str, Any], destination: Mapping[str, Any], distance: float) -> str:
    origin_region = origin["region_code"].split("_")[0]
    destination_region = destination["region_code"].split("_")[0]
    if origin_region == destination_region == "EUROPE":
        return "ROAD" if distance < 1400 else "RAIL"
    if origin_region == destination_region and distance < 3500:
        return "ROAD" if distance < 1800 else "RAIL"
    return "SEA"


def _lane_values(mode: str, distance: float, uom: str) -> tuple[float, float, float]:
    rate = {
        "KG": {"ROAD": 0.00070, "RAIL": 0.00045, "SEA": 0.00016, "AIR": 0.0040},
        "EA": {"ROAD": 0.00250, "RAIL": 0.00180, "SEA": 0.00075, "AIR": 0.0150},
    }[uom][mode]
    base = {"KG": 0.04, "EA": 0.80}[uom]
    variable = base + rate * distance
    fixed = {"ROAD": 160.0, "RAIL": 330.0, "SEA": 700.0, "AIR": 480.0}[mode] + distance * 0.035
    transit = {
        "ROAD": 1.0 + distance / 650,
        "RAIL": 2.0 + distance / 500,
        "SEA": 8.0 + distance / 500,
        "AIR": 1.5 + distance / 5500,
    }[mode]
    return variable, fixed, transit


def _lanes(
    master_seed: int,
    approvals: Sequence[Mapping[str, Any]],
    contracts: Sequence[Mapping[str, Any]],
    incoterms: Mapping[str, Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    contract_by_approval = {row["approval_id"]: row for row in contracts}
    approvals_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in approvals:
        approvals_by_pair[(approval["seller_node_id"], approval["buyer_node_id"])].append(approval)

    standard: list[dict[str, Any]] = []
    pair_score: list[tuple[float, int, tuple[str, str]]] = []
    for index, (pair, pair_approvals) in enumerate(sorted(approvals_by_pair.items()), start=1):
        origin, destination = nodes[pair[0]], nodes[pair[1]]
        distance = max(25.0, _haversine_km(origin, destination) * 1.12)
        mode = _mode(origin, destination, distance)
        uom = materials[pair_approvals[0]["material_id"]]["uom"]
        variable, fixed, transit = _lane_values(mode, distance, uom)
        capacity_base = 4200.0 if uom == "KG" else 650.0
        capacity = capacity_base * _between(master_seed, "lane-capacity", "|".join(pair), 0.75, 1.25)
        reliability = _between(master_seed, "lane-reliability", "|".join(pair), 78.0, 94.0)
        standard.append(
            {
                "lane_id": f"LANE-{index:05d}",
                "origin_node_id": pair[0],
                "destination_node_id": pair[1],
                "transport_mode": mode,
                "distance_km": round(distance, 1),
                "base_transit_days": round(transit, 2),
                "transit_std_days": round(transit * _between(master_seed, "lane-variability", "|".join(pair), 0.08, 0.24), 2),
                "weekly_capacity": round(capacity, 2),
                "freight_currency": "EUR",
                "variable_freight_cost_per_unit": round(variable, 4),
                "fixed_shipment_cost": round(fixed, 2),
                "insurance_rate_pct_of_goods": round(_between(master_seed, "insurance", "|".join(pair), 0.002, 0.009), 5),
                "reliability_score": round(reliability, 1),
                "expedited_flag": False,
                "active_flag": True,
            }
        )
        terms = {contract_by_approval[row["approval_id"]]["incoterm_code"] for row in pair_approvals}
        buyer_carriage = all(incoterms[term]["buyer_pays_main_carriage"] for term in terms)
        criticality = max(
            {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}[materials[row["material_id"]]["criticality_class"]]
            for row in pair_approvals
        )
        if buyer_carriage:
            pair_score.append((distance, criticality, pair))

    expedited_pairs = [pair for _, _, pair in sorted(pair_score, reverse=True)[:6]]
    for _, _, pair in sorted(pair_score, key=lambda item: (item[1], item[0], item[2]), reverse=True):
        if pair not in expedited_pairs:
            expedited_pairs.append(pair)
        if len(expedited_pairs) == 12:
            break
    standard_by_pair = {(row["origin_node_id"], row["destination_node_id"]): row for row in standard}
    expedited: list[dict[str, Any]] = []
    for offset, pair in enumerate(sorted(expedited_pairs), start=len(standard) + 1):
        base = standard_by_pair[pair]
        mode = "AIR" if base["transport_mode"] != "AIR" else "ROAD"
        variable, fixed, transit = _lane_values(mode, base["distance_km"], materials[approvals_by_pair[pair][0]["material_id"]]["uom"])
        expedited.append(
            {
                "lane_id": f"LANE-{offset:05d}",
                "origin_node_id": pair[0],
                "destination_node_id": pair[1],
                "transport_mode": mode,
                "distance_km": base["distance_km"],
                "base_transit_days": round(min(transit, base["base_transit_days"] * 0.48), 2),
                "transit_std_days": round(max(0.1, base["transit_std_days"] * 0.55), 2),
                "weekly_capacity": round(base["weekly_capacity"] * 0.48, 2),
                "freight_currency": "EUR",
                "variable_freight_cost_per_unit": round(max(variable, base["variable_freight_cost_per_unit"] * 2.4), 4),
                "fixed_shipment_cost": round(max(fixed, base["fixed_shipment_cost"] * 1.5), 2),
                "insurance_rate_pct_of_goods": round(base["insurance_rate_pct_of_goods"] * 1.08, 5),
                "reliability_score": round(min(99.0, base["reliability_score"] + 3.5), 1),
                "expedited_flag": True,
                "active_flag": True,
            }
        )
    return [*standard, *expedited], ["|".join(pair) for pair in sorted(expedited_pairs)]


def _duties(
    approvals: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    tuples = sorted(
        {
            (
                nodes[row["seller_node_id"]]["country_code"],
                nodes[row["buyer_node_id"]]["country_code"],
                materials[row["material_id"]]["material_family"],
            )
            for row in approvals
        }
    )
    family_rate = {
        "CONDUCTOR": 0.035,
        "MAGNETIC": 0.045,
        "POWER_ELECTRONICS": 0.025,
        "MOTION": 0.055,
        "INSULATION": 0.065,
        "HOUSING": 0.075,
        "SENSING": 0.030,
        "CONTROL": 0.040,
    }
    rows: list[dict[str, Any]] = []
    for index, (origin, destination, family) in enumerate(tuples, start=1):
        zero_rate = origin == destination or {origin, destination} <= EU_COUNTRIES or {origin, destination} <= NORTH_AMERICA
        rows.append(
            {
                "duty_rule_id": f"DUTY-{index:05d}",
                "origin_country_code": origin,
                "destination_country_code": destination,
                "material_family": family,
                "duty_rate": 0.0 if zero_rate else family_rate[family],
                "customs_value_basis": "GOODS_PLUS_FREIGHT" if family in {"CONDUCTOR", "MAGNETIC", "HOUSING"} else "GOODS",
                "effective_from_period": "P01",
                "effective_to_period": "P12",
            }
        )
    return rows


def _cost_rules(boundary_contracts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    definitions = (
        ("EXTERNAL_PURCHASE", True, "SOURCE", "QUANTITY", False, None),
        ("FREIGHT", True, "RECEIPT", "QUANTITY", False, None),
        ("DUTY", True, "RECEIPT", "GOODS_VALUE", False, None),
        ("INSURANCE", True, "RECEIPT", "GOODS_VALUE", False, None),
        ("FIXED_ORDER", True, "RECEIPT", "ACTIVATION", False, None),
        ("FIXED_SHIPMENT", True, "RECEIPT", "ACTIVATION", False, None),
        ("CONVERSION", True, "TRANSFORMATION", "QUANTITY", True, None),
        ("SETUP", True, "TRANSFORMATION", "ACTIVATION", True, None),
        ("OVERHEAD", True, "TRANSFORMATION", "DIRECT", True, None),
        ("SURGE", True, "TRANSFORMATION", "QUANTITY", False, None),
        ("MARKUP", True, "TRANSFORMATION", "GOODS_VALUE", False, None),
        ("HOLDING", False, "NONE", "QUANTITY", False, "PERIOD_HOLDING"),
        ("ACTIVATION", False, "NONE", "ACTIVATION", False, "RELATIONSHIP_ACTIVATION"),
        ("SHORTAGE", False, "NONE", "QUANTITY", False, "SERVICE_SHORTAGE_STAGE_1"),
    )
    rows = [
        {
            "cost_rule_id": f"COST-{index:04d}",
            "cost_component": component,
            "scope_type": "GLOBAL",
            "scope_id": None,
            "capitalised_flag": capitalised,
            "capitalisation_stage": stage,
            "allocation_basis": basis,
            "markup_eligible_flag": markup,
            "noncapitalised_ledger_category": category,
            "precedence": 0,
        }
        for index, (component, capitalised, stage, basis, markup, category) in enumerate(definitions, start=1)
    ]
    for contract in sorted(boundary_contracts, key=lambda row: row["contract_id"]):
        rows.append(
            {
                "cost_rule_id": f"COST-{len(rows) + 1:04d}",
                "cost_component": "SURGE",
                "scope_type": "CONTRACT",
                "scope_id": contract["contract_id"],
                "capitalised_flag": True,
                "capitalisation_stage": "SOURCE",
                "allocation_basis": "QUANTITY",
                "markup_eligible_flag": False,
                "noncapitalised_ledger_category": None,
                "precedence": 100,
            }
        )
    return rows


def _conversion_costs(
    master_seed: int,
    recipes: Sequence[Mapping[str, Any]],
    inputs: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
    fx: Mapping[tuple[str, str], float],
) -> list[dict[str, Any]]:
    input_count: dict[str, int] = defaultdict(int)
    for row in inputs:
        input_count[row["recipe_id"]] += 1
    tier_base = {"TIER_3": 7.0, "TIER_2": 17.0, "TIER_1": 32.0}
    rows: list[dict[str, Any]] = []
    for recipe in sorted(recipes, key=lambda row: row["recipe_id"]):
        node = nodes[recipe["node_id"]]
        currency = node["local_currency"]
        complexity = 1 + 0.22 * (input_count[recipe["recipe_id"]] - 1)
        profile = _between(master_seed, "conversion-profile", recipe["recipe_id"], 0.84, 1.18)
        for period_number, period in enumerate(PERIODS, start=1):
            movement = 1 + 0.012 * math.sin(period_number / 2 + stable_fraction(master_seed, "conversion-phase", recipe["recipe_id"]) * math.pi)
            variable_eur = tier_base[node["node_tier"]] * complexity * profile * movement
            setup_eur = (380.0 + tier_base[node["node_tier"]] * 42) * complexity * profile
            overhead_fixed_eur = setup_eur * 0.32
            overhead_variable_eur = variable_eur * 0.18
            rate = fx[(currency, period)]
            rows.append(
                {
                    "node_id": recipe["node_id"],
                    "recipe_id": recipe["recipe_id"],
                    "period_id": period,
                    "currency": currency,
                    "variable_conversion_cost_per_output": round(variable_eur / rate, 4),
                    "fixed_setup_cost": round(setup_eur / rate, 4),
                    "eligible_overhead_fixed": round(overhead_fixed_eur / rate, 4),
                    "eligible_overhead_variable": round(overhead_variable_eur / rate, 4),
                    "markup_rate": round(_between(master_seed, "markup", recipe["recipe_id"], 0.05, 0.14), 4),
                    "markup_base_rule_id": "COST-0011",
                    "scenario_sensitive_flag": True,
                }
            )
    return rows


def _duty_map(duties: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    return {
        (row["origin_country_code"], row["destination_country_code"], row["material_family"]): row
        for row in duties
    }


def _external_prices(
    master_seed: int,
    approvals: Sequence[Mapping[str, Any]],
    contracts: Sequence[Mapping[str, Any]],
    lanes: Sequence[Mapping[str, Any]],
    incoterms: Mapping[str, Mapping[str, Any]],
    duties: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
    fx: Mapping[tuple[str, str], float],
    crossover_pools: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    approvals_by_id = {row["approval_id"]: row for row in approvals}
    standard_lane = {
        (row["origin_node_id"], row["destination_node_id"]): row
        for row in lanes
        if not row["expedited_flag"]
    }
    duties_by_key = _duty_map(duties)
    boundary_contracts = [
        row
        for row in contracts
        if nodes[approvals_by_id[row["approval_id"]]["seller_node_id"]]["external_boundary_flag"]
    ]
    contracts_by_pool: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for contract in boundary_contracts:
        approval = approvals_by_id[contract["approval_id"]]
        contracts_by_pool[f"{approval['buyer_node_id']}|{approval['material_id']}"] .append(contract)
    crossover_set = set(crossover_pools)

    rows: list[dict[str, Any]] = []
    build_up: list[dict[str, Any]] = []
    for contract in sorted(boundary_contracts, key=lambda row: row["contract_id"]):
        approval = approvals_by_id[contract["approval_id"]]
        seller, buyer = nodes[approval["seller_node_id"]], nodes[approval["buyer_node_id"]]
        material = materials[approval["material_id"]]
        lane = standard_lane[(seller["node_id"], buyer["node_id"])]
        term = incoterms[contract["incoterm_code"]]
        duty = duties_by_key[(seller["country_code"], buyer["country_code"], material["material_family"])]
        pool_key = f"{buyer['node_id']}|{material['material_id']}"
        profile = _between(master_seed, "source-profile", f"{seller['node_id']}|{material['material_id']}", 0.87, 1.15)
        if pool_key in crossover_set:
            siblings = sorted(contracts_by_pool[pool_key], key=lambda row: row["contract_id"])
            profile = 0.88 if contract["contract_id"] == siblings[0]["contract_id"] else 1.10
        for period_number, period in enumerate(PERIODS, start=1):
            season = 1 + 0.018 * math.sin(period_number / 2 + stable_fraction(master_seed, "price-phase", contract["contract_id"]) * math.pi)
            goods = FAMILY_GOODS_EUR[material["material_family"]] * profile * season
            seller_origin = 0.0 if term["buyer_pays_origin_transport"] else goods * 0.012
            seller_freight = 0.0
            seller_fixed = 0.0
            if not term["buyer_pays_main_carriage"]:
                seller_freight = lane["variable_freight_cost_per_unit"]
                seller_fixed = lane["fixed_shipment_cost"] / contract["minimum_order_quantity"]
            seller_insurance = 0.0 if term["buyer_pays_insurance"] else goods * lane["insurance_rate_pct_of_goods"]
            customs_value = goods + (seller_freight if duty["customs_value_basis"] == "GOODS_PLUS_FREIGHT" else 0.0)
            seller_duty = 0.0 if term["buyer_pays_import_duty"] else customs_value * duty["duty_rate"]
            quote_eur = goods + seller_origin + seller_freight + seller_fixed + seller_insurance + seller_duty
            released = quote_eur / fx[(contract["currency"], period)]
            rows.append(
                {
                    "contract_id": contract["contract_id"],
                    "material_id": material["material_id"],
                    "period_id": period,
                    "unit_price": round(released, 6),
                    "currency": contract["currency"],
                    "price_source": "SYNTHETIC_FIXED",
                    "scenario_sensitive_flag": True,
                }
            )
            build_up.append(
                {
                    "contract_id": contract["contract_id"],
                    "approval_id": approval["approval_id"],
                    "material_id": material["material_id"],
                    "period_id": period,
                    "incoterm_code": contract["incoterm_code"],
                    "components_eur_per_unit": {
                        "goods": round(goods, 9),
                        "seller_origin_transport": round(seller_origin, 9),
                        "seller_main_carriage": round(seller_freight, 9),
                        "seller_fixed_shipment_amortisation": round(seller_fixed, 9),
                        "seller_insurance": round(seller_insurance, 9),
                        "seller_import_duty": round(seller_duty, 9),
                    },
                    "quoted_unit_price_eur": round(quote_eur, 9),
                    "released_unit_price": round(released, 6),
                    "released_currency": contract["currency"],
                }
            )
    return rows, build_up


def _calibrate_crossover_fixed_costs(
    crossover_pools: Sequence[str],
    approvals: Sequence[Mapping[str, Any]],
    contracts: Sequence[dict[str, Any]],
    lanes: Sequence[Mapping[str, Any]],
    prices: Sequence[Mapping[str, Any]],
    incoterms: Mapping[str, Mapping[str, Any]],
    duties: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
    fx: Mapping[tuple[str, str], float],
) -> None:
    approvals_by_pool: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for approval in approvals:
        approvals_by_pool[f"{approval['buyer_node_id']}|{approval['material_id']}"] .append(approval)
    contract_by_approval = {row["approval_id"]: row for row in contracts}
    standard_lane = {
        (row["origin_node_id"], row["destination_node_id"]): row
        for row in lanes
        if not row["expedited_flag"]
    }
    price_by_key = {(row["contract_id"], row["material_id"], row["period_id"]): row for row in prices}
    duty_by_key = _duty_map(duties)

    def without_order_cost(approval: Mapping[str, Any], quantity: float) -> float:
        contract = contract_by_approval[approval["approval_id"]]
        seller, buyer = nodes[approval["seller_node_id"]], nodes[approval["buyer_node_id"]]
        material = materials[approval["material_id"]]
        lane = standard_lane[(seller["node_id"], buyer["node_id"])]
        price = price_by_key[(contract["contract_id"], material["material_id"], "P06")]
        goods = price["unit_price"] * fx[(price["currency"], "P06")]
        term = incoterms[contract["incoterm_code"]]
        result = goods
        freight = 0.0
        if term["buyer_pays_main_carriage"]:
            freight = lane["variable_freight_cost_per_unit"]
            result += freight + lane["fixed_shipment_cost"] / quantity
        if term["buyer_pays_insurance"]:
            result += goods * lane["insurance_rate_pct_of_goods"]
        if term["buyer_pays_import_duty"]:
            duty = duty_by_key[(seller["country_code"], buyer["country_code"], material["material_family"])]
            basis = goods + (freight if duty["customs_value_basis"] == "GOODS_PLUS_FREIGHT" else 0.0)
            result += basis * duty["duty_rate"]
        return result

    for pool in crossover_pools:
        pool_approvals = sorted(approvals_by_pool[pool], key=lambda row: row["approval_id"])
        if len(pool_approvals) < 2:
            continue
        pool_contracts = [contract_by_approval[row["approval_id"]] for row in pool_approvals]
        pool_lanes = [standard_lane[(row["seller_node_id"], row["buyer_node_id"])] for row in pool_approvals]
        common_multiple = math.lcm(*(max(1, round(row["order_multiple"])) for row in pool_contracts))
        low = math.ceil(max(row["minimum_order_quantity"] for row in pool_contracts) / common_multiple) * common_multiple
        high = math.floor(min(row["weekly_capacity"] for row in pool_lanes) / common_multiple) * common_multiple
        base = [without_order_cost(row, math.sqrt(low * high)) for row in pool_approvals]
        cheaper_index = min(range(len(base)), key=base.__getitem__)
        expensive_index = max(range(len(base)), key=base.__getitem__)
        difference = base[expensive_index] - base[cheaper_index]
        if difference <= 0 or high <= low:
            continue
        cheap_contract = pool_contracts[cheaper_index]
        expensive_contract = pool_contracts[expensive_index]
        expensive_fixed_eur = 90.0
        cheap_fixed_eur = expensive_fixed_eur + difference * math.sqrt(low * high)
        expensive_contract["fixed_order_cost"] = round(expensive_fixed_eur / fx[(expensive_contract["currency"], "P06")], 4)
        cheap_contract["fixed_order_cost"] = round(cheap_fixed_eur / fx[(cheap_contract["currency"], "P06")], 4)


def _central_state_costs(
    period: str,
    network: Mapping[str, Sequence[Mapping[str, Any]]],
    commercial: Mapping[str, Sequence[Mapping[str, Any]]],
) -> tuple[dict[tuple[str, str], float], dict[str, float]]:
    nodes = {row["node_id"]: row for row in network["network_nodes.csv"]}
    materials = {row["material_id"]: row for row in network["materials.csv"]}
    approvals = {row["approval_id"]: row for row in network["material_flow_approvals.csv"]}
    contracts = {row["approval_id"]: row for row in commercial["supply_contracts.csv"]}
    terms = {row["incoterm_code"]: row for row in commercial["incoterm_rules.csv"]}
    fx = {(row["currency"], row["period_id"]): row["eur_per_currency_unit"] for row in commercial["fx_rates.csv"]}
    prices = {(row["contract_id"], row["material_id"], row["period_id"]): row for row in commercial["external_source_prices.csv"]}
    duties = _duty_map(commercial["import_duty_rates.csv"])
    lanes = {
        (row["origin_node_id"], row["destination_node_id"]): row
        for row in commercial["shipping_lanes.csv"]
        if not row["expedited_flag"]
    }
    conversion = {(row["node_id"], row["recipe_id"], row["period_id"]): row for row in commercial["conversion_costs.csv"]}
    inputs_by_recipe: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in network["transformation_inputs.csv"]:
        inputs_by_recipe[row["recipe_id"]].append(row)
    inbound: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in approvals.values():
        inbound[(approval["buyer_node_id"], approval["material_id"])].append(approval)

    state_cost: dict[tuple[str, str], float] = {}
    approval_cost: dict[str, float] = {}

    def landed(approval: Mapping[str, Any], source_cost: float | None) -> float:
        contract = contracts[approval["approval_id"]]
        material = materials[approval["material_id"]]
        seller, buyer = nodes[approval["seller_node_id"]], nodes[approval["buyer_node_id"]]
        if seller["external_boundary_flag"]:
            price = prices[(contract["contract_id"], material["material_id"], period)]
            goods = price["unit_price"] * fx[(price["currency"], period)]
        elif source_cost is not None:
            goods = source_cost
        else:
            raise ValueError(f"missing source cost for {approval['approval_id']}")
        lane = lanes[(seller["node_id"], buyer["node_id"])]
        term = terms[contract["incoterm_code"]]
        quantity = max(contract["minimum_order_quantity"], contract["order_multiple"] * 5)
        result = goods + contract["fixed_order_cost"] * fx[(contract["currency"], period)] / quantity
        freight = 0.0
        if term["buyer_pays_main_carriage"]:
            freight = lane["variable_freight_cost_per_unit"] * fx[(lane["freight_currency"], period)]
            result += freight + lane["fixed_shipment_cost"] * fx[(lane["freight_currency"], period)] / quantity
        if term["buyer_pays_insurance"]:
            result += goods * lane["insurance_rate_pct_of_goods"]
        if term["buyer_pays_import_duty"]:
            duty = duties[(seller["country_code"], buyer["country_code"], material["material_family"])]
            basis = goods + (freight if duty["customs_value_basis"] == "GOODS_PLUS_FREIGHT" else 0.0)
            result += basis * duty["duty_rate"]
        return result

    tier_order = ("TIER_3", "TIER_2", "TIER_1")
    for tier in tier_order:
        recipe_costs: dict[tuple[str, str], list[float]] = defaultdict(list)
        recipes = [row for row in network["transformation_recipes.csv"] if nodes[row["node_id"]]["node_tier"] == tier]
        for recipe in recipes:
            input_total = 0.0
            for input_row in inputs_by_recipe[recipe["recipe_id"]]:
                options = []
                for approval in inbound[(recipe["node_id"], input_row["input_material_id"])]:
                    source = state_cost.get((approval["seller_node_id"], approval["material_id"]))
                    cost = landed(approval, source)
                    approval_cost[approval["approval_id"]] = cost
                    options.append(cost)
                input_total += (input_row["quantity_per_output"] / recipe["yield_rate"]) * (sum(options) / len(options))
            cost_row = conversion[(recipe["node_id"], recipe["recipe_id"], period)]
            rate = fx[(cost_row["currency"], period)]
            run_quantity = max(50.0, recipe["minimum_run_quantity"])
            additions = (
                cost_row["variable_conversion_cost_per_output"]
                + cost_row["eligible_overhead_variable"]
                + (cost_row["fixed_setup_cost"] + cost_row["eligible_overhead_fixed"]) / run_quantity
            ) * rate
            output_cost = (input_total + additions) * (1 + cost_row["markup_rate"])
            recipe_costs[(recipe["node_id"], recipe["output_material_id"])].append(output_cost)
        for state, costs in recipe_costs.items():
            state_cost[state] = sum(costs) / len(costs)

    for approval in approvals.values():
        if approval["approval_id"] not in approval_cost:
            source = state_cost.get((approval["seller_node_id"], approval["material_id"]))
            approval_cost[approval["approval_id"]] = landed(approval, source)
    return state_cost, approval_cost


def build_candidate(
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
) -> Candidate:
    network = load_network(network_dir)
    nodes = {row["node_id"]: row for row in network["network_nodes.csv"]}
    materials = {row["material_id"]: row for row in network["materials.csv"]}
    approvals = list(network["material_flow_approvals.csv"])
    incoterm_rows = _incoterms()
    incoterms = {row["incoterm_code"]: row for row in incoterm_rows}
    fx_rows = _fx_rates(master_seed, list(nodes.values()))
    fx = {(row["currency"], row["period_id"]): row["eur_per_currency_unit"] for row in fx_rows}
    contracts, crossover_pools = _contract_terms(master_seed, approvals, nodes, materials, fx)
    lanes, expedited_pairs = _lanes(master_seed, approvals, contracts, incoterms, nodes, materials)
    duties = _duties(approvals, nodes, materials)
    prices, price_build_up = _external_prices(
        master_seed,
        approvals,
        contracts,
        lanes,
        incoterms,
        duties,
        nodes,
        materials,
        fx,
        crossover_pools,
    )
    _calibrate_crossover_fixed_costs(
        crossover_pools,
        approvals,
        contracts,
        lanes,
        prices,
        incoterms,
        duties,
        nodes,
        materials,
        fx,
    )
    boundary_contracts = [
        contract
        for contract in contracts
        if nodes[next(row for row in approvals if row["approval_id"] == contract["approval_id"])["seller_node_id"]]["external_boundary_flag"]
    ]
    commercial: dict[str, list[dict[str, Any]]] = {
        "supply_contracts.csv": contracts,
        "incoterm_rules.csv": incoterm_rows,
        "import_duty_rates.csv": duties,
        "shipping_lanes.csv": lanes,
        "external_source_prices.csv": prices,
        "conversion_costs.csv": _conversion_costs(
            master_seed,
            network["transformation_recipes.csv"],
            network["transformation_inputs.csv"],
            nodes,
            fx,
        ),
        "cost_allocation_rules.csv": _cost_rules(boundary_contracts),
        "fx_rates.csv": fx_rows,
    }
    targets = {
        "crossover_receiving_pools": crossover_pools,
        "expedited_node_pairs": expedited_pairs,
    }
    return Candidate(commercial, price_build_up, targets)


def build_dataset(
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
) -> dict[str, list[dict[str, Any]]]:
    return build_candidate(master_seed, network_dir).tables


def render_files(
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
) -> dict[str, str]:
    config = load_config()
    candidate = build_candidate(master_seed, network_dir)
    rendered: dict[str, str] = {}
    for file_name in COMMERCIAL_FILES:
        fields = [field["name"] for field in config["raw_contracts"][file_name]["columns"]]
        rendered[f"data/{file_name}"] = _csv_text(candidate.tables[file_name], fields)
    rendered["evidence/external_price_build_up.json"] = canonical_json(
        {
            "status": "PRIVATE_CALIBRATION_EVIDENCE",
            "rows": candidate.external_price_build_up,
        }
    )
    rendered["evidence/generation_targets.json"] = canonical_json(candidate.generation_targets)
    manifest = {
        "configuration_id": config["configuration_id"],
        "configuration_version": config["configuration_version"],
        "generator": "generate_commercial_data.py",
        "master_seed": master_seed,
        "network_manifest_sha256": hashlib.sha256((network_dir / "generation_manifest.json").read_bytes()).hexdigest(),
        "namespaced_seed": namespace_seed(master_seed, "commercial"),
        "files": {
            path: {"rows": len(candidate.tables[path.removeprefix("data/")]), "sha256": sha256_bytes(content.encode())}
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
) -> dict[str, str]:
    rendered = render_files(master_seed, network_dir)
    for relative_path, content in rendered.items():
        path = output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
    return rendered


def check_files(
    output_dir: Path,
    master_seed: int = DEFAULT_MASTER_SEED,
    network_dir: Path = DEFAULT_NETWORK_DIR,
) -> list[str]:
    expected = render_files(master_seed, network_dir)
    return sorted(
        relative_path
        for relative_path, content in expected.items()
        if not (output_dir / relative_path).is_file()
        or (output_dir / relative_path).read_text(encoding="utf-8") != content
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network-dir", type=Path, default=DEFAULT_NETWORK_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--master-seed", type=int, default=DEFAULT_MASTER_SEED)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        drift = check_files(args.output_dir.resolve(), args.master_seed, args.network_dir.resolve())
        if drift:
            print("Commercial generation drift: " + ", ".join(drift), file=sys.stderr)
            return 1
        print(f"Generated commercial files are current ({len(render_files(args.master_seed, args.network_dir.resolve()))} files).")
        return 0
    rendered = write_files(args.output_dir.resolve(), args.master_seed, args.network_dir.resolve())
    with tempfile.TemporaryDirectory() as temporary:
        verification = Path(temporary)
        write_files(verification, args.master_seed, args.network_dir.resolve())
        if check_files(verification, args.master_seed, args.network_dir.resolve()):
            raise RuntimeError("commercial files failed deterministic self-check")
    print(f"Generated {len(rendered)} commercial files in {args.output_dir.resolve()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
