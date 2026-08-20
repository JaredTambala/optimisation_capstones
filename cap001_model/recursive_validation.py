"""Independent accounting checks for extracted recursive-cost solutions."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from cap001_model.data import ModelData, PoolKey
from cap001_model.physical import active_in_period
from cap001_model.recursive import RecipeInputPeriodKey, RecursiveSolution
from tooling.contract_runtime import within_tolerance


@dataclass(frozen=True)
class AccountingViolation:
    rule: str
    entity_id: str
    residual: float
    tolerance: float


@dataclass(frozen=True)
class RecursiveValidation:
    checked_equations: int
    max_residual: float
    violations: tuple[AccountingViolation, ...]

    @property
    def passed(self) -> bool:
        return not self.violations


def _actual_source_split(data: ModelData, solution: RecursiveSolution, key: PoolKey):
    return solution.source_regular[key], solution.source_surge[key]


def _component_totals(data: ModelData, solution: RecursiveSolution) -> dict[str, float]:
    totals = {
        component: 0.0
        for component in data.config["cost_policy"]["capitalised_components"]
        + data.config["cost_policy"]["noncapitalised_components"]
    }
    for key, quantity in solution.source_supply.items():
        regular, surge = _actual_source_split(data, solution, key)
        price = data.source_unit_prices[key]
        totals["EXTERNAL_PURCHASE"] += price * (regular + surge)
        totals["SURGE"] += data.source_capacity[key]["surge_unit_premium"] * surge
    for route_id, route in data.shipment_routes.items():
        quantity = solution.shipments[route_id]
        dispatched = solution.shipment_dispatch_value[route_id]
        freight = route.freight_unit_eur * quantity
        totals["FREIGHT"] += freight
        totals["INSURANCE"] += route.insurance_rate * dispatched
        totals["DUTY"] += route.duty_rate * (
            dispatched + (freight if route.duty_on_freight else 0.0)
        )
        if solution.shipment_active[route_id] > 0.5:
            totals["FIXED_ORDER"] += route.fixed_order_cost_eur
            totals["FIXED_SHIPMENT"] += route.fixed_shipment_cost_eur
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in data.rows("fx_rates.csv")
    }
    rules_by_component = {
        row["cost_component"]: row for row in data.rows("cost_allocation_rules.csv")
    }
    eligible = set(data.config["cost_policy"]["default_markup_eligible_base"])
    for (recipe_id, period), quantity in solution.production.items():
        if solution.production_active[(recipe_id, period)] <= 0.5:
            continue
        recipe = data.recipes[recipe_id]
        conversion_row = data.conversion_costs[(recipe_id, period)]
        capacity_row = data.transformation_capacity[(recipe_id, period)]
        rate = fx[(conversion_row["currency"], period)]
        surge = solution.production_surge[(recipe_id, period)]
        input_value = sum(
            solution.production_input_value[
                (recipe_id, row["input_material_id"], period)
            ]
            for row in data.recipe_inputs[recipe_id]
        )
        conversion = conversion_row["variable_conversion_cost_per_output"] * rate * quantity
        setup = (
            conversion_row["fixed_setup_cost"] * rate
            if recipe["setup_required_flag"]
            else 0.0
        )
        overhead = (
            conversion_row["eligible_overhead_fixed"] * rate
            + conversion_row["eligible_overhead_variable"] * rate * quantity
        )
        surge_cost = capacity_row["surge_conversion_premium"] * rate * surge
        totals["CONVERSION"] += conversion
        totals["SETUP"] += setup
        totals["OVERHEAD"] += overhead
        totals["SURGE"] += surge_cost
        markup_base = (
            (input_value if "INPUT_VALUE" in eligible else 0.0)
            + (
                conversion + surge_cost
                if rules_by_component["CONVERSION"]["markup_eligible_flag"]
                and "CONVERSION" in eligible
                else 0.0
            )
            + (
                setup
                if rules_by_component["SETUP"]["markup_eligible_flag"]
                and "SETUP" in eligible
                else 0.0
            )
            + (
                overhead
                if rules_by_component["OVERHEAD"]["markup_eligible_flag"]
                and "ELIGIBLE_OVERHEAD" in eligible
                else 0.0
            )
        )
        totals["MARKUP"] += conversion_row["markup_rate"] * markup_base
    totals["HOLDING"] = sum(
        data.inventory_policy[(node, material)]["holding_cost_eur_per_unit_week"]
        * solution.closing_inventory[node, material, period]
        for node, material, period in data.pool_keys
    )
    totals["ACTIVATION"] = sum(
        max(
            route.horizon_activation_cost_eur
            for route in data.shipment_routes.values()
            if route.contract_id == contract_id
        )
        for contract_id in {route.contract_id for route in data.shipment_routes.values()}
        if solution.contract_active[contract_id] > 0.5
    )
    totals["SHORTAGE"] = sum(
        data.demand[key]["shortage_penalty_eur_per_unit"] * quantity
        for key, quantity in solution.shortage.items()
    )
    return totals


def evaluate_control_selector(
    data: ModelData,
    solution: RecursiveSolution,
    selector: Mapping[str, Any],
) -> float:
    measure = selector["measure"]
    if measure in {"pool_quantity", "pool_value", "pool_unit_cost", "closing_value", "served_value"}:
        key = (selector["node_id"], selector["material_id"], selector["period_id"])
        mapping = {
            "pool_quantity": solution.pool_quantity,
            "pool_value": solution.pool_value,
            "pool_unit_cost": solution.unit_cost,
            "closing_value": solution.closing_value,
            "served_value": solution.served_value,
        }[measure]
        return mapping[key]
    if measure == "leg_receipt_value":
        route_id = next(
            route_id
            for route_id, route in data.shipment_routes.items()
            if route.lane_id == selector["lane_id"]
        )
        return solution.shipment_receipt_value[route_id]
    if measure == "served_value_total":
        return sum(
            value
            for (node, material, _), value in solution.served_value.items()
            if node == selector["node_id"] and material == selector["material_id"]
        )
    if measure == "served_value_total_all":
        return sum(solution.served_value.values())
    if measure == "terminal_closing_total":
        final_period = data.periods[-1]
        return sum(
            value
            for (_, _, period), value in solution.closing_value.items()
            if period == final_period
        )
    totals = _component_totals(data, solution)
    if measure == "ledger_component_total":
        return totals[selector["component"]]
    if measure == "noncapitalised_total":
        return sum(
            totals[component]
            for component in data.config["cost_policy"]["noncapitalised_components"]
        )
    if measure == "stage_2_value":
        return (
            evaluate_control_selector(
                data, solution, {"measure": "served_value_total_all"}
            )
            + evaluate_control_selector(
                data, solution, {"measure": "terminal_closing_total"}
            )
            + evaluate_control_selector(
                data, solution, {"measure": "noncapitalised_total"}
            )
        )
    if measure == "capitalised_plus_opening_total":
        capitalised = sum(
            totals[component]
            for component in data.config["cost_policy"]["capitalised_components"]
        )
        opening = sum(
            row["opening_total_value_eur"] for row in data.opening_inventory.values()
        )
        return capitalised + opening
    raise ValueError(f"unsupported control-total measure {measure}")


def validate_published_control_totals(
    data: ModelData,
    solution: RecursiveSolution,
    *,
    definitions_path: Path,
    expected_path: Path,
) -> tuple[str, ...]:
    definitions = {
        row["control_total_id"]: row
        for row in json.loads(definitions_path.read_text(encoding="utf-8"))
    }
    with expected_path.open(newline="", encoding="utf-8") as handle:
        expected = {
            row["control_total_id"]: float(row["expected_value"])
            for row in csv.DictReader(handle)
        }
    failures: list[str] = []
    for control_total_id, definition in definitions.items():
        actual = evaluate_control_selector(data, solution, definition["selector"])
        if not within_tolerance(
            actual,
            expected[control_total_id],
            definition["absolute_tolerance"],
            definition["relative_tolerance"],
        ):
            failures.append(
                f"{control_total_id}: actual={actual}, expected={expected[control_total_id]}"
            )
    return tuple(failures)


def validate_recursive_solution(
    data: ModelData, solution: RecursiveSolution
) -> RecursiveValidation:
    """Recompute recursive accounting equations without a live Pyomo model."""

    value_policy = data.config["tolerances"]["value"]
    unit_policy = data.config["tolerances"]["unit_cost"]
    checked = 0
    maximum = 0.0
    violations: list[AccountingViolation] = []

    def check(rule: str, entity: str, lhs: float, rhs: float, *, unit: bool = False):
        nonlocal checked, maximum
        policy = unit_policy if unit else value_policy
        tolerance = policy["absolute"] + policy["relative"] * max(abs(lhs), abs(rhs))
        residual = abs(lhs - rhs)
        checked += 1
        maximum = max(maximum, residual)
        if residual > tolerance:
            violations.append(AccountingViolation(rule, entity, residual, tolerance))

    incoming: dict[PoolKey, list[str]] = {key: [] for key in data.pool_keys}
    outgoing: dict[PoolKey, list[str]] = {key: [] for key in data.pool_keys}
    for route_id, route in data.shipment_routes.items():
        incoming[(route.destination_node_id, route.material_id, route.arrival_period_id)].append(route_id)
        outgoing[(route.origin_node_id, route.material_id, route.dispatch_period_id)].append(route_id)

    component_totals = _component_totals(data, solution)
    for route_id, route in data.shipment_routes.items():
        quantity = solution.shipments[route_id]
        dispatch_expected = solution.unit_cost[
            (route.origin_node_id, route.material_id, route.dispatch_period_id)
        ] * quantity
        check("SHIPMENT_DISPATCH_VALUE", route_id, solution.shipment_dispatch_value[route_id], dispatch_expected)
        freight = route.freight_unit_eur * quantity
        receipt_expected = (
            dispatch_expected * (1 + route.insurance_rate + route.duty_rate)
            + freight * (1 + (route.duty_rate if route.duty_on_freight else 0.0))
            + (route.fixed_order_cost_eur + route.fixed_shipment_cost_eur if quantity > 0 else 0.0)
        )
        check("SHIPMENT_RECEIPT_VALUE", route_id, solution.shipment_receipt_value[route_id], receipt_expected)

    outputs_by_pool: dict[PoolKey, list[tuple[str, str]]] = {key: [] for key in data.pool_keys}
    inputs_by_pool: dict[PoolKey, list[RecipeInputPeriodKey]] = {key: [] for key in data.pool_keys}
    for recipe_id, recipe in data.recipes.items():
        for period in data.periods:
            if active_in_period(recipe, period):
                outputs_by_pool[(recipe["node_id"], recipe["output_material_id"], period)].append((recipe_id, period))
                for row in data.recipe_inputs[recipe_id]:
                    inputs_by_pool[(recipe["node_id"], row["input_material_id"], period)].append((recipe_id, row["input_material_id"], period))

    for key in data.pool_keys:
        node, material, period = key
        check("POOL_UNIT_COST", "/".join(key), solution.pool_value[key], solution.pool_quantity[key] * solution.unit_cost[key])
        check("CLOSING_VALUE", "/".join(key), solution.closing_value[key], solution.closing_inventory[key] * solution.unit_cost[key])
        if key in data.demand:
            check("SERVED_VALUE", "/".join(key), solution.served_value[key], solution.served[key] * solution.unit_cost[key])
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening_value = opening_row["opening_total_value_eur"] if opening_row else 0.0
        else:
            opening_value = solution.closing_value[(node, material, previous)]
        source_value = 0.0
        if key in data.source_capacity:
            regular, surge = _actual_source_split(data, solution, key)
            price = data.source_unit_prices[key]
            source_value = price * (regular + surge) + data.source_capacity[key]["surge_unit_premium"] * surge
        rollforward = (
            opening_value
            + source_value
            + sum(solution.shipment_receipt_value[route_id] for route_id in incoming[key])
            + sum(solution.production_output_value[event] for event in outputs_by_pool[key])
        )
        check("POOL_VALUE_ROLLFORWARD", "/".join(key), solution.pool_value[key], rollforward)
        conservation = (
            solution.closing_value[key]
            + solution.served_value.get(key, 0.0)
            + sum(solution.shipment_dispatch_value[route_id] for route_id in outgoing[key])
            + sum(solution.production_input_value[event] for event in inputs_by_pool[key])
        )
        check("POOL_VALUE_CONSERVATION", "/".join(key), solution.pool_value[key], conservation)

    check(
        "GLOBAL_VALUE_CONSERVATION",
        "CAP-001",
        sum(
            component_totals[component]
            for component in data.config["cost_policy"]["capitalised_components"]
        )
        + sum(row["opening_total_value_eur"] for row in data.opening_inventory.values()),
        evaluate_control_selector(
            data, solution, {"measure": "served_value_total_all"}
        )
        + evaluate_control_selector(
            data, solution, {"measure": "terminal_closing_total"}
        ),
    )
    return RecursiveValidation(checked, maximum, tuple(violations))
