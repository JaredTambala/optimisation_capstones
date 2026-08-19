"""Shared tier-neutral physical formulation for CAP-001 models."""

from __future__ import annotations

from typing import Mapping

import pyomo.environ as pyo

from cap001_model.data import ModelData, PoolKey
from tooling.contract_runtime import ContractError


def active_in_period(row: Mapping[str, object], period_id: str) -> bool:
    return bool(
        row["active_flag"]
        and row["effective_from_period"] <= period_id <= row["effective_to_period"]
    )


def _validate_references(data: ModelData) -> None:
    pools = set(data.pool_keys)
    for source_key in data.source_capacity:
        if source_key not in pools:
            raise ContractError(
                f"source capacity references untracked pool {source_key}"
            )
    for route in data.shipment_routes.values():
        origin = (route.origin_node_id, route.material_id, route.dispatch_period_id)
        destination = (
            route.destination_node_id,
            route.material_id,
            route.arrival_period_id,
        )
        if origin not in pools or destination not in pools:
            raise ContractError(
                f"route {route.route_id} references untracked pool {origin} or {destination}"
            )
    for recipe_id, recipe in data.recipes.items():
        for period_id in data.periods:
            for input_row in data.recipe_inputs[recipe_id]:
                key = (recipe["node_id"], input_row["input_material_id"], period_id)
                if key not in pools:
                    raise ContractError(
                        f"recipe {recipe_id} references untracked input pool {key}"
                    )
            output = (recipe["node_id"], recipe["output_material_id"], period_id)
            if output not in pools:
                raise ContractError(
                    f"recipe {recipe_id} references untracked output pool {output}"
                )
    missing_demand_pools = sorted(set(data.demand) - pools)
    if missing_demand_pools:
        raise ContractError(
            f"demand references untracked pools: {missing_demand_pools}"
        )


def build_physical_model(data: ModelData, *, name: str) -> pyo.ConcreteModel:
    """Construct shared flow, timing, capacity and discrete controls."""

    _validate_references(data)
    model = pyo.ConcreteModel(name=name)
    source_keys = tuple(sorted(data.source_capacity))
    recipe_period_keys = tuple(
        (recipe_id, period_id)
        for recipe_id in sorted(data.recipes)
        for period_id in data.periods
    )
    route_ids = tuple(sorted(data.shipment_routes))
    contract_ids = tuple(
        sorted({route.contract_id for route in data.shipment_routes.values()})
    )
    demand_keys = tuple(sorted(data.demand))

    model.POOL = pyo.Set(initialize=data.pool_keys, dimen=3, ordered=True)
    model.SOURCE = pyo.Set(initialize=source_keys, dimen=3, ordered=True)
    model.RECIPE_PERIOD = pyo.Set(initialize=recipe_period_keys, dimen=2, ordered=True)
    model.ROUTE = pyo.Set(initialize=route_ids, ordered=True)
    model.CONTRACT = pyo.Set(initialize=contract_ids, ordered=True)
    model.DEMAND = pyo.Set(initialize=demand_keys, dimen=3, ordered=True)

    model.source_regular = pyo.Var(model.SOURCE, domain=pyo.NonNegativeReals)
    model.source_surge = pyo.Var(model.SOURCE, domain=pyo.NonNegativeReals)
    model.source_supply = pyo.Expression(
        model.SOURCE,
        rule=lambda m, node, material, period: (
            m.source_regular[node, material, period]
            + m.source_surge[node, material, period]
        ),
    )
    model.shipment_quantity = pyo.Var(model.ROUTE, domain=pyo.NonNegativeReals)
    model.shipment_active = pyo.Var(model.ROUTE, domain=pyo.Binary)
    model.shipment_lots = pyo.Var(model.ROUTE, domain=pyo.NonNegativeIntegers)
    model.contract_active = pyo.Var(model.CONTRACT, domain=pyo.Binary)
    model.production_regular = pyo.Var(model.RECIPE_PERIOD, domain=pyo.NonNegativeReals)
    model.production_surge = pyo.Var(model.RECIPE_PERIOD, domain=pyo.NonNegativeReals)
    model.production_quantity = pyo.Expression(
        model.RECIPE_PERIOD,
        rule=lambda m, recipe, period: (
            m.production_regular[recipe, period] + m.production_surge[recipe, period]
        ),
    )
    model.production_active = pyo.Var(model.RECIPE_PERIOD, domain=pyo.Binary)

    def inventory_bounds(_: pyo.ConcreteModel, node: str, material: str, period: str):
        return (
            0.0,
            data.inventory_policy[(node, material)]["maximum_storage_quantity"],
        )

    model.closing_inventory = pyo.Var(
        model.POOL, domain=pyo.NonNegativeReals, bounds=inventory_bounds
    )
    model.served = pyo.Var(model.DEMAND, domain=pyo.NonNegativeReals)
    model.shortage = pyo.Var(model.DEMAND, domain=pyo.NonNegativeReals)

    model.source_regular_capacity = pyo.Constraint(
        model.SOURCE,
        rule=lambda m, node, material, period: (
            m.source_regular[node, material, period]
            <= data.source_capacity[(node, material, period)]["regular_capacity"]
            * (
                1
                - data.source_capacity[(node, material, period)][
                    "planned_downtime_fraction"
                ]
            )
        ),
    )
    model.source_surge_capacity = pyo.Constraint(
        model.SOURCE,
        rule=lambda m, node, material, period: (
            m.source_surge[node, material, period]
            <= data.source_capacity[(node, material, period)]["surge_capacity"]
            * (
                1
                - data.source_capacity[(node, material, period)][
                    "planned_downtime_fraction"
                ]
            )
        ),
    )
    model.minimum_source_supply = pyo.Constraint(
        model.SOURCE,
        rule=lambda m, node, material, period: (
            m.source_supply[node, material, period]
            >= data.source_capacity[(node, material, period)]["minimum_supply_quantity"]
        ),
    )

    model.order_multiple = pyo.Constraint(
        model.ROUTE,
        rule=lambda m, route_id: (
            m.shipment_quantity[route_id]
            == data.shipment_routes[route_id].order_multiple * m.shipment_lots[route_id]
        ),
    )
    model.minimum_order = pyo.Constraint(
        model.ROUTE,
        rule=lambda m, route_id: (
            m.shipment_quantity[route_id]
            >= data.shipment_routes[route_id].minimum_order_quantity
            * m.shipment_active[route_id]
        ),
    )
    model.lane_capacity = pyo.Constraint(
        model.ROUTE,
        rule=lambda m, route_id: (
            m.shipment_quantity[route_id]
            <= data.shipment_routes[route_id].capacity * m.shipment_active[route_id]
        ),
    )
    model.contract_activation_lower = pyo.Constraint(
        model.ROUTE,
        rule=lambda m, route_id: (
            m.shipment_active[route_id]
            <= m.contract_active[data.shipment_routes[route_id].contract_id]
        ),
    )
    routes_by_contract = {
        contract_id: tuple(
            route_id
            for route_id, route in data.shipment_routes.items()
            if route.contract_id == contract_id
        )
        for contract_id in contract_ids
    }
    model.contract_activation_upper = pyo.Constraint(
        model.CONTRACT,
        rule=lambda m, contract_id: (
            m.contract_active[contract_id]
            <= sum(
                m.shipment_active[route_id]
                for route_id in routes_by_contract[contract_id]
            )
        ),
    )

    receiving_groups: dict[tuple[str, str, str], list[str]] = {}
    approval_period_groups: dict[tuple[str, str], list[str]] = {}
    for route in data.shipment_routes.values():
        receiving_groups.setdefault(
            (
                route.destination_node_id,
                route.material_id,
                route.dispatch_period_id,
            ),
            [],
        ).append(route.route_id)
        approval_period_groups.setdefault(
            (route.approval_id, route.dispatch_period_id), []
        ).append(route.route_id)
    model.maximum_approved_share = pyo.ConstraintList()
    for route_ids in approval_period_groups.values():
        route = data.shipment_routes[route_ids[0]]
        if route.maximum_approved_share is None:
            continue
        receiving = receiving_groups[
            (
                route.destination_node_id,
                route.material_id,
                route.dispatch_period_id,
            )
        ]
        model.maximum_approved_share.add(
            sum(model.shipment_quantity[route_id] for route_id in route_ids)
            <= route.maximum_approved_share
            * sum(model.shipment_quantity[route_id] for route_id in receiving)
        )

    def regular_production_capacity(
        m: pyo.ConcreteModel, recipe_id: str, period_id: str
    ):
        row = data.transformation_capacity[(recipe_id, period_id)]
        limit = row["regular_output_capacity"] * (1 - row["planned_downtime_fraction"])
        if not active_in_period(data.recipes[recipe_id], period_id):
            limit = 0.0
        return m.production_regular[recipe_id, period_id] <= limit

    def surge_production_capacity(m: pyo.ConcreteModel, recipe_id: str, period_id: str):
        row = data.transformation_capacity[(recipe_id, period_id)]
        limit = row["surge_output_capacity"] * (1 - row["planned_downtime_fraction"])
        if not active_in_period(data.recipes[recipe_id], period_id):
            limit = 0.0
        return m.production_surge[recipe_id, period_id] <= limit

    model.regular_production_capacity = pyo.Constraint(
        model.RECIPE_PERIOD, rule=regular_production_capacity
    )
    model.surge_production_capacity = pyo.Constraint(
        model.RECIPE_PERIOD, rule=surge_production_capacity
    )

    shared_groups: dict[tuple[str, str], list[str]] = {}
    for (recipe_id, period_id), row in data.transformation_capacity.items():
        group_id = row["shared_capacity_group_id"]
        if group_id is not None:
            shared_groups.setdefault((group_id, period_id), []).append(recipe_id)
    model.shared_regular_capacity = pyo.ConstraintList()
    model.shared_surge_capacity = pyo.ConstraintList()
    for (group_id, period_id), recipe_ids in sorted(shared_groups.items()):
        rows = [
            data.transformation_capacity[(recipe_id, period_id)]
            for recipe_id in recipe_ids
        ]
        signatures = {
            (
                row["regular_output_capacity"],
                row["surge_output_capacity"],
                row["planned_downtime_fraction"],
            )
            for row in rows
        }
        if len(signatures) != 1:
            raise ContractError(
                f"shared capacity group {group_id}/{period_id} has inconsistent limits"
            )
        regular_limit, surge_limit, downtime = next(iter(signatures))
        model.shared_regular_capacity.add(
            sum(
                data.transformation_capacity[(recipe_id, period_id)][
                    "shared_capacity_coefficient"
                ]
                * model.production_regular[recipe_id, period_id]
                for recipe_id in recipe_ids
            )
            <= regular_limit * (1 - downtime)
        )
        model.shared_surge_capacity.add(
            sum(
                data.transformation_capacity[(recipe_id, period_id)][
                    "shared_capacity_coefficient"
                ]
                * model.production_surge[recipe_id, period_id]
                for recipe_id in recipe_ids
            )
            <= surge_limit * (1 - downtime)
        )

    def production_activation_upper(
        m: pyo.ConcreteModel, recipe_id: str, period_id: str
    ):
        row = data.transformation_capacity[(recipe_id, period_id)]
        capacity = (row["regular_output_capacity"] + row["surge_output_capacity"]) * (
            1 - row["planned_downtime_fraction"]
        )
        if not active_in_period(data.recipes[recipe_id], period_id):
            capacity = 0.0
        return (
            m.production_quantity[recipe_id, period_id]
            <= capacity * m.production_active[recipe_id, period_id]
        )

    model.production_activation_upper = pyo.Constraint(
        model.RECIPE_PERIOD, rule=production_activation_upper
    )
    model.production_minimum_run = pyo.Constraint(
        model.RECIPE_PERIOD,
        rule=lambda m, recipe_id, period_id: (
            m.production_quantity[recipe_id, period_id]
            >= data.recipes[recipe_id]["minimum_run_quantity"]
            * m.production_active[recipe_id, period_id]
        ),
    )

    model.exclusive_recipe_groups = pyo.ConstraintList()
    exclusive_groups: dict[tuple[str, str, str], list[str]] = {}
    for recipe_id, recipe in data.recipes.items():
        if recipe["activation_mode"] != "EXCLUSIVE":
            continue
        group = recipe["recipe_group_id"] or recipe_id
        for period_id in data.periods:
            exclusive_groups.setdefault(
                (recipe["node_id"], group, period_id), []
            ).append(recipe_id)
    for (_, _, period_id), recipe_ids in sorted(exclusive_groups.items()):
        model.exclusive_recipe_groups.add(
            sum(
                model.production_active[recipe_id, period_id]
                for recipe_id in recipe_ids
            )
            <= 1
        )

    model.demand_balance = pyo.Constraint(
        model.DEMAND,
        rule=lambda m, node, material, period: (
            m.served[node, material, period] + m.shortage[node, material, period]
            == data.demand[(node, material, period)]["demand_quantity"]
        ),
    )

    arrivals: dict[PoolKey, tuple[str, ...]] = {}
    dispatches: dict[PoolKey, tuple[str, ...]] = {}
    production_outputs: dict[PoolKey, tuple[str, ...]] = {}
    production_inputs: dict[PoolKey, tuple[tuple[str, float], ...]] = {}
    for key in data.pool_keys:
        node, material, period = key
        arrivals[key] = tuple(
            route.route_id
            for route in data.shipment_routes.values()
            if (
                route.destination_node_id,
                route.material_id,
                route.arrival_period_id,
            )
            == key
        )
        dispatches[key] = tuple(
            route.route_id
            for route in data.shipment_routes.values()
            if (
                route.origin_node_id,
                route.material_id,
                route.dispatch_period_id,
            )
            == key
        )
        production_outputs[key] = tuple(
            recipe_id
            for recipe_id, recipe in data.recipes.items()
            if recipe["node_id"] == node
            and recipe["output_material_id"] == material
            and active_in_period(recipe, period)
        )
        input_terms: list[tuple[str, float]] = []
        for recipe_id, recipe in data.recipes.items():
            if recipe["node_id"] != node or not active_in_period(recipe, period):
                continue
            for input_row in data.recipe_inputs[recipe_id]:
                if input_row["input_material_id"] == material:
                    input_terms.append(
                        (
                            recipe_id,
                            input_row["quantity_per_output"] / recipe["yield_rate"],
                        )
                    )
        production_inputs[key] = tuple(input_terms)

    def pool_balance(m: pyo.ConcreteModel, node: str, material: str, period: str):
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening = opening_row["usable_quantity"] if opening_row else 0.0
        else:
            opening = m.closing_inventory[node, material, previous]
        source = (
            m.source_supply[node, material, period]
            if (node, material, period) in data.source_capacity
            else 0.0
        )
        receipt = sum(
            m.shipment_quantity[route_id]
            for route_id in arrivals[(node, material, period)]
        )
        produced = sum(
            m.production_quantity[recipe_id, period]
            for recipe_id in production_outputs[(node, material, period)]
        )
        consumed = sum(
            coefficient * m.production_quantity[recipe_id, period]
            for recipe_id, coefficient in production_inputs[(node, material, period)]
        )
        dispatched = sum(
            m.shipment_quantity[route_id]
            for route_id in dispatches[(node, material, period)]
        )
        served = (
            m.served[node, material, period]
            if (node, material, period) in data.demand
            else 0.0
        )
        return (
            opening + source + receipt + produced
            == consumed
            + dispatched
            + served
            + m.closing_inventory[node, material, period]
        )

    model.pool_balance = pyo.Constraint(model.POOL, rule=pool_balance)
    model.terminal_inventory_targets = pyo.ConstraintList()
    final_period = data.periods[-1]
    for (node, material), policy in sorted(data.inventory_policy.items()):
        target = policy["terminal_target_quantity"]
        if target is not None:
            model.terminal_inventory_targets.add(
                model.closing_inventory[node, material, final_period] >= target
            )
    return model
