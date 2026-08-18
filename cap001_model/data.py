"""Validated raw-contract loading and model indexes for CAP-001."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from tooling.contract_runtime import (
    ContractError,
    coerce_csv_value,
    load_config,
    resolve_data_dir,
    validate_raw_data_directory,
)


PoolKey = tuple[str, str, str]
SourceKey = tuple[str, str, str]
RecipePeriodKey = tuple[str, str]
DemandKey = tuple[str, str, str]


@dataclass(frozen=True)
class ShipmentRoute:
    route_id: str
    approval_id: str
    contract_id: str
    lane_id: str
    origin_node_id: str
    destination_node_id: str
    material_id: str
    dispatch_period_id: str
    arrival_period_id: str
    minimum_order_quantity: float
    order_multiple: float
    capacity: float
    maximum_approved_share: float | None
    freight_unit_eur: float
    insurance_rate: float
    duty_rate: float
    duty_on_freight: bool
    variable_baseline_cost_eur: float
    fixed_order_cost_eur: float
    fixed_shipment_cost_eur: float
    horizon_activation_cost_eur: float


@dataclass(frozen=True)
class ModelData:
    config: Mapping[str, Any]
    tables: Mapping[str, tuple[Mapping[str, Any], ...]]
    periods: tuple[str, ...]
    period_number: Mapping[str, int]
    pool_keys: tuple[PoolKey, ...]
    inventory_policy: Mapping[tuple[str, str], Mapping[str, Any]]
    opening_inventory: Mapping[tuple[str, str], Mapping[str, Any]]
    nodes: Mapping[str, Mapping[str, Any]]
    materials: Mapping[str, Mapping[str, Any]]
    source_capacity: Mapping[SourceKey, Mapping[str, Any]]
    recipes: Mapping[str, Mapping[str, Any]]
    recipe_inputs: Mapping[str, tuple[Mapping[str, Any], ...]]
    transformation_capacity: Mapping[RecipePeriodKey, Mapping[str, Any]]
    conversion_costs: Mapping[RecipePeriodKey, Mapping[str, Any]]
    demand: Mapping[DemandKey, Mapping[str, Any]]
    standard_costs: Mapping[PoolKey, float]
    source_unit_prices: Mapping[SourceKey, float]
    shipment_routes: Mapping[str, ShipmentRoute]

    def rows(self, name: str) -> tuple[Mapping[str, Any], ...]:
        return self.tables[name]

    def previous_period(self, period_id: str) -> str | None:
        position = self.periods.index(period_id)
        return None if position == 0 else self.periods[position - 1]


def _read_rows(path: Path, columns: list[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    fields = {column["name"]: column for column in columns}
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(
            {
                name: coerce_csv_value(value, fields[name])
                for name, value in row.items()
            }
            for row in csv.DictReader(handle)
        )


def _periods_between(
    periods: tuple[str, ...], start: str, end: str
) -> tuple[str, ...]:
    start_position = periods.index(start)
    end_position = periods.index(end)
    if end_position < start_position:
        raise ContractError(f"invalid period window {start}..{end}")
    return periods[start_position : end_position + 1]


def _arrival_period(
    periods: tuple[str, ...],
    dispatch_period: str,
    handling_days: float,
    transit_days: float,
) -> str:
    lead_periods = math.ceil((handling_days + transit_days) / 7)
    arrival_position = periods.index(dispatch_period) + lead_periods
    if arrival_position >= len(periods):
        raise ContractError(
            f"route dispatched in {dispatch_period} arrives beyond the planning horizon"
        )
    return periods[arrival_position]


def _resolve_duty_rate(
    rows: tuple[Mapping[str, Any], ...],
    *,
    origin_country: str,
    destination_country: str,
    material_family: str,
    period_id: str,
) -> Mapping[str, Any]:
    matches = [
        row
        for row in rows
        if row["origin_country_code"] == origin_country
        and row["destination_country_code"] == destination_country
        and row["material_family"] == material_family
        and row["effective_from_period"] <= period_id <= row["effective_to_period"]
    ]
    if len(matches) != 1:
        raise ContractError(
            "expected exactly one duty rule for "
            f"{origin_country}->{destination_country}/{material_family}@{period_id}, "
            f"found {len(matches)}"
        )
    return matches[0]


def _build_routes(
    *,
    tables: Mapping[str, tuple[Mapping[str, Any], ...]],
    periods: tuple[str, ...],
    nodes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
    standard_costs: Mapping[PoolKey, float],
) -> dict[str, ShipmentRoute]:
    approvals = {row["approval_id"]: row for row in tables["material_flow_approvals.csv"]}
    lanes_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in tables["shipping_lanes.csv"]:
        if row["active_flag"]:
            lanes_by_pair.setdefault(
                (row["origin_node_id"], row["destination_node_id"]), []
            ).append(row)
    incoterms = {
        row["incoterm_code"]: row for row in tables["incoterm_rules.csv"]
    }
    fx_rates = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in tables["fx_rates.csv"]
    }
    duty_rows = tables["import_duty_rates.csv"]
    routes: dict[str, ShipmentRoute] = {}

    for contract in tables["supply_contracts.csv"]:
        if not contract["active_flag"]:
            continue
        approval = approvals[contract["approval_id"]]
        if approval["approval_status"] != "APPROVED":
            continue
        lanes = lanes_by_pair.get(
            (approval["seller_node_id"], approval["buyer_node_id"]), []
        )
        if len(lanes) != 1:
            raise ContractError(
                f"fixture model expects exactly one active lane for contract "
                f"{contract['contract_id']}, found {len(lanes)}"
            )
        lane = lanes[0]
        contract_periods = set(
            _periods_between(
                periods,
                contract["effective_from_period"],
                contract["effective_to_period"],
            )
        )
        approval_periods = set(
            _periods_between(
                periods,
                approval["valid_from_period"],
                approval["valid_to_period"],
            )
        )
        for dispatch_period in periods:
            if dispatch_period not in contract_periods & approval_periods:
                continue
            arrival_period = _arrival_period(
                periods,
                dispatch_period,
                contract["contract_handling_days"],
                lane["base_transit_days"],
            )
            standard_key = (
                approval["seller_node_id"],
                approval["material_id"],
                dispatch_period,
            )
            if standard_key not in standard_costs:
                raise ContractError(
                    f"no baseline standard cost for route {contract['contract_id']} "
                    f"at {standard_key}"
                )
            standard_cost = standard_costs[standard_key]
            contract_fx = fx_rates[(contract["currency"], dispatch_period)]
            freight_fx = fx_rates[(lane["freight_currency"], dispatch_period)]
            incoterm = incoterms[contract["incoterm_code"]]
            freight = (
                lane["variable_freight_cost_per_unit"] * freight_fx
                if incoterm["buyer_pays_main_carriage"]
                else 0.0
            )
            insurance = (
                lane["insurance_rate_pct_of_goods"] * standard_cost
                if incoterm["buyer_pays_insurance"]
                else 0.0
            )
            duty = 0.0
            duty_rate = 0.0
            duty_on_freight = False
            if incoterm["buyer_pays_import_duty"]:
                duty_rule = _resolve_duty_rate(
                    duty_rows,
                    origin_country=nodes[approval["seller_node_id"]]["country_code"],
                    destination_country=nodes[approval["buyer_node_id"]]["country_code"],
                    material_family=materials[approval["material_id"]]["material_family"],
                    period_id=dispatch_period,
                )
                customs_value = (
                    standard_cost
                    if duty_rule["customs_value_basis"] == "GOODS"
                    else standard_cost + freight
                )
                duty_rate = duty_rule["duty_rate"]
                duty_on_freight = duty_rule["customs_value_basis"] != "GOODS"
                duty = duty_rate * customs_value
            route_id = f"{contract['contract_id']}|{lane['lane_id']}|{dispatch_period}"
            routes[route_id] = ShipmentRoute(
                route_id=route_id,
                approval_id=approval["approval_id"],
                contract_id=contract["contract_id"],
                lane_id=lane["lane_id"],
                origin_node_id=approval["seller_node_id"],
                destination_node_id=approval["buyer_node_id"],
                material_id=approval["material_id"],
                dispatch_period_id=dispatch_period,
                arrival_period_id=arrival_period,
                minimum_order_quantity=contract["minimum_order_quantity"],
                order_multiple=contract["order_multiple"],
                capacity=lane["weekly_capacity"],
                maximum_approved_share=approval["maximum_approved_share"],
                freight_unit_eur=freight,
                insurance_rate=(
                    lane["insurance_rate_pct_of_goods"]
                    if incoterm["buyer_pays_insurance"]
                    else 0.0
                ),
                duty_rate=duty_rate,
                duty_on_freight=duty_on_freight,
                variable_baseline_cost_eur=standard_cost + freight + insurance + duty,
                fixed_order_cost_eur=contract["fixed_order_cost"] * contract_fx,
                fixed_shipment_cost_eur=(
                    lane["fixed_shipment_cost"] * freight_fx
                    if incoterm["buyer_pays_main_carriage"]
                    else 0.0
                ),
                horizon_activation_cost_eur=contract["horizon_activation_cost"]
                * contract_fx,
            )
    return routes


def load_model_data(
    data_dir: Path | None = None,
    config: Mapping[str, Any] | None = None,
) -> ModelData:
    """Load all raw contracts and derive model indexes without solving them."""

    if config is None:
        config = load_config()
    resolved = resolve_data_dir(data_dir)
    validate_raw_data_directory(resolved, config)
    tables = {
        name: _read_rows(resolved / name, contract["columns"])
        for name, contract in config["raw_contracts"].items()
    }
    calendar = sorted(tables["planning_calendar.csv"], key=lambda row: row["period_number"])
    periods = tuple(row["period_id"] for row in calendar)
    period_number = {row["period_id"]: row["period_number"] for row in calendar}
    inventory_policy = {
        (row["node_id"], row["material_id"]): row
        for row in tables["inventory_policies.csv"]
    }
    pool_keys = tuple(
        (node_id, material_id, period_id)
        for node_id, material_id in sorted(inventory_policy)
        for period_id in periods
    )
    opening_inventory = {
        (row["node_id"], row["material_id"]): row
        for row in tables["opening_inventory.csv"]
    }
    nodes = {row["node_id"]: row for row in tables["network_nodes.csv"]}
    materials = {row["material_id"]: row for row in tables["materials.csv"]}
    source_capacity = {
        (row["node_id"], row["material_id"], row["period_id"]): row
        for row in tables["source_capacity.csv"]
    }
    recipes = {
        row["recipe_id"]: row
        for row in tables["transformation_recipes.csv"]
        if row["active_flag"]
    }
    recipe_inputs_mutable: dict[str, list[Mapping[str, Any]]] = {}
    for row in tables["transformation_inputs.csv"]:
        recipe_inputs_mutable.setdefault(row["recipe_id"], []).append(row)
    recipe_inputs = {
        recipe_id: tuple(sorted(rows, key=lambda row: row["input_sequence"]))
        for recipe_id, rows in recipe_inputs_mutable.items()
    }
    transformation_capacity = {
        (row["recipe_id"], row["period_id"]): row
        for row in tables["transformation_capacity.csv"]
    }
    conversion_costs = {
        (row["recipe_id"], row["period_id"]): row
        for row in tables["conversion_costs.csv"]
    }
    demand = {
        (row["plant_id"], row["material_id"], row["period_id"]): row
        for row in tables["terminal_demand.csv"]
    }
    standard_costs = {
        (row["node_id"], row["material_id"], row["period_id"]): row[
            "standard_unit_cost_eur"
        ]
        for row in tables["baseline_standard_costs.csv"]
    }
    approvals = {
        row["approval_id"]: row for row in tables["material_flow_approvals.csv"]
    }
    contracts = {
        row["contract_id"]: row for row in tables["supply_contracts.csv"]
    }
    external_prices = {
        (row["contract_id"], row["material_id"], row["period_id"]): row
        for row in tables["external_source_prices.csv"]
    }
    fx_rates = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in tables["fx_rates.csv"]
    }
    source_unit_prices: dict[SourceKey, float] = {}
    for source_key in source_capacity:
        node_id, material_id, period_id = source_key
        prices = {
            external_prices[(contract_id, material_id, period_id)]["unit_price"]
            * fx_rates[
                (
                    external_prices[(contract_id, material_id, period_id)]["currency"],
                    period_id,
                )
            ]
            for contract_id, contract in contracts.items()
            if approvals[contract["approval_id"]]["seller_node_id"] == node_id
            and approvals[contract["approval_id"]]["material_id"] == material_id
            and (contract_id, material_id, period_id) in external_prices
        }
        if len(prices) != 1:
            raise ContractError(
                f"boundary price is not uniform for {source_key}: {sorted(prices)}"
            )
        source_unit_prices[source_key] = next(iter(prices))
    routes = _build_routes(
        tables=tables,
        periods=periods,
        nodes=nodes,
        materials=materials,
        standard_costs=standard_costs,
    )
    return ModelData(
        config=config,
        tables=tables,
        periods=periods,
        period_number=period_number,
        pool_keys=pool_keys,
        inventory_policy=inventory_policy,
        opening_inventory=opening_inventory,
        nodes=nodes,
        materials=materials,
        source_capacity=source_capacity,
        recipes=recipes,
        recipe_inputs=recipe_inputs,
        transformation_capacity=transformation_capacity,
        conversion_costs=conversion_costs,
        demand=demand,
        standard_costs=standard_costs,
        source_unit_prices=source_unit_prices,
        shipment_routes=routes,
    )
