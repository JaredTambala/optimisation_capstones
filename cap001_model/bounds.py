"""Finite, data-derived bounds for the recursive-cost formulation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from cap001_model.data import ModelData, PoolKey
from cap001_model.physical import active_in_period
from tooling.contract_runtime import ContractError


@dataclass(frozen=True)
class PoolBound:
    pool_key: PoolKey
    quantity_upper: float
    value_upper: float
    unit_cost_upper: float
    minimum_meaningful_quantity: float
    derivation: str


@dataclass(frozen=True)
class BoundReport:
    pools: dict[PoolKey, PoolBound]
    shipment_dispatch_value_upper: dict[str, float]
    shipment_receipt_value_upper: dict[str, float]
    production_input_value_upper: dict[tuple[str, str], float]
    production_output_value_upper: dict[tuple[str, str], float]

    def assert_finite(self) -> None:
        values = [
            value
            for bound in self.pools.values()
            for value in (
                bound.quantity_upper,
                bound.value_upper,
                bound.unit_cost_upper,
            )
        ]
        values.extend(self.shipment_dispatch_value_upper.values())
        values.extend(self.shipment_receipt_value_upper.values())
        values.extend(self.production_input_value_upper.values())
        values.extend(self.production_output_value_upper.values())
        if not all(math.isfinite(value) and value >= 0 for value in values):
            raise ContractError("recursive bound report contains a missing or non-finite bound")


def dependency_order(data: ModelData) -> tuple[PoolKey, ...]:
    successors: dict[PoolKey, set[PoolKey]] = {key: set() for key in data.pool_keys}
    indegree: dict[PoolKey, int] = {key: 0 for key in data.pool_keys}

    def add_edge(origin: PoolKey, destination: PoolKey) -> None:
        if origin == destination or destination in successors[origin]:
            return
        successors[origin].add(destination)
        indegree[destination] += 1

    for node, material, period in data.pool_keys:
        previous = data.previous_period(period)
        if previous is not None:
            add_edge((node, material, previous), (node, material, period))
    for route in data.shipment_routes.values():
        add_edge(
            (route.origin_node_id, route.material_id, route.dispatch_period_id),
            (route.destination_node_id, route.material_id, route.arrival_period_id),
        )
    for recipe_id, recipe in data.recipes.items():
        for period in data.periods:
            if not active_in_period(recipe, period):
                continue
            destination = (recipe["node_id"], recipe["output_material_id"], period)
            for input_row in data.recipe_inputs[recipe_id]:
                add_edge(
                    (recipe["node_id"], input_row["input_material_id"], period),
                    destination,
                )

    ready = sorted(key for key, count in indegree.items() if count == 0)
    ordered: list[PoolKey] = []
    while ready:
        key = ready.pop(0)
        ordered.append(key)
        for successor in sorted(successors[key]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
                ready.sort()
    if len(ordered) != len(data.pool_keys):
        unresolved = sorted(key for key, count in indegree.items() if count)
        raise ContractError(f"value-bound dependency graph contains a cycle: {unresolved}")
    return tuple(ordered)


def derive_recursive_bounds(data: ModelData) -> BoundReport:
    """Propagate finite envelopes through periods, routes and recipes."""

    quantity_upper: dict[PoolKey, float] = {}
    for key in data.pool_keys:
        node, material, period = key
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening = opening_row["usable_quantity"] if opening_row else 0.0
        else:
            opening = data.inventory_policy[(node, material)][
                "maximum_storage_quantity"
            ]
        source_row = data.source_capacity.get(key)
        source = (
            (source_row["regular_capacity"] + source_row["surge_capacity"])
            * (1 - source_row["planned_downtime_fraction"])
            if source_row
            else 0.0
        )
        receipts = sum(
            route.capacity
            for route in data.shipment_routes.values()
            if (
                route.destination_node_id,
                route.material_id,
                route.arrival_period_id,
            )
            == key
        )
        production = sum(
            (
                data.transformation_capacity[(recipe_id, period)][
                    "regular_output_capacity"
                ]
                + data.transformation_capacity[(recipe_id, period)][
                    "surge_output_capacity"
                ]
            )
            * (
                1
                - data.transformation_capacity[(recipe_id, period)][
                    "planned_downtime_fraction"
                ]
            )
            for recipe_id, recipe in data.recipes.items()
            if recipe["node_id"] == node
            and recipe["output_material_id"] == material
            and active_in_period(recipe, period)
        )
        quantity_upper[key] = opening + source + receipts + production

    pools: dict[PoolKey, PoolBound] = {}
    dispatch_bounds: dict[str, float] = {}
    receipt_bounds: dict[str, float] = {}
    production_input_bounds: dict[tuple[str, str], float] = {}
    production_output_bounds: dict[tuple[str, str], float] = {}

    for key in dependency_order(data):
        node, material, period = key
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening_value = opening_row["opening_total_value_eur"] if opening_row else 0.0
        else:
            prior = pools[(node, material, previous)]
            # Closing inventory is an outflow of the prior pool, so its value
            # cannot exceed the entire prior pool value. Using U_max * storage
            # would combine incompatible extrema and amplify epsilon at every
            # period.
            opening_value = prior.value_upper

        source_value = 0.0
        source_row = data.source_capacity.get(key)
        if source_row:
            available_regular = source_row["regular_capacity"] * (
                1 - source_row["planned_downtime_fraction"]
            )
            available_surge = source_row["surge_capacity"] * (
                1 - source_row["planned_downtime_fraction"]
            )
            source_price = data.source_unit_prices[key]
            source_value = source_price * available_regular + (
                source_price + source_row["surge_unit_premium"]
            ) * available_surge

        receipt_value = 0.0
        for route in data.shipment_routes.values():
            destination = (
                route.destination_node_id,
                route.material_id,
                route.arrival_period_id,
            )
            if destination != key:
                continue
            origin = (
                route.origin_node_id,
                route.material_id,
                route.dispatch_period_id,
            )
            # A shipment cannot carry more value than exists in its origin
            # pool. This envelope is both safe and much tighter than combining
            # the route capacity with a unit-cost maximum attained only near
            # the minimum meaningful pool quantity.
            dispatched = pools[origin].value_upper
            freight = route.freight_unit_eur * route.capacity
            received = (
                dispatched * (1 + route.insurance_rate + route.duty_rate)
                + freight * (1 + (route.duty_rate if route.duty_on_freight else 0.0))
                + route.fixed_order_cost_eur
                + route.fixed_shipment_cost_eur
            )
            dispatch_bounds[route.route_id] = dispatched
            receipt_bounds[route.route_id] = received
            receipt_value += received

        production_value = 0.0
        for recipe_id, recipe in data.recipes.items():
            if (
                recipe["node_id"] != node
                or recipe["output_material_id"] != material
                or not active_in_period(recipe, period)
            ):
                continue
            capacity = data.transformation_capacity[(recipe_id, period)]
            regular = capacity["regular_output_capacity"] * (
                1 - capacity["planned_downtime_fraction"]
            )
            surge = capacity["surge_output_capacity"] * (
                1 - capacity["planned_downtime_fraction"]
            )
            output_quantity = regular + surge
            input_value = sum(
                pools[(node, row["input_material_id"], period)].value_upper
                for row in data.recipe_inputs[recipe_id]
            )
            conversion = data.conversion_costs[(recipe_id, period)]
            value_add = (
                conversion["variable_conversion_cost_per_output"] * output_quantity
                + capacity["surge_conversion_premium"] * surge
                + (
                    conversion["fixed_setup_cost"]
                    if recipe["setup_required_flag"] and output_quantity > 0
                    else 0.0
                )
                + (
                    conversion["eligible_overhead_fixed"]
                    if output_quantity > 0
                    else 0.0
                )
                + conversion["eligible_overhead_variable"] * output_quantity
            )
            output_value = (input_value + value_add) * (1 + conversion["markup_rate"])
            production_input_bounds[(recipe_id, period)] = input_value
            production_output_bounds[(recipe_id, period)] = output_value
            production_value += output_value

        value_upper = opening_value + source_value + receipt_value + production_value
        epsilon = data.inventory_policy[(node, material)][
            "minimum_meaningful_pool_quantity"
        ]
        if quantity_upper[key] > 0 and epsilon <= 0:
            raise ContractError(f"positive-capacity pool {key} has no positive epsilon")
        unit_cost_upper = value_upper / epsilon if quantity_upper[key] > 0 else 0.0
        pools[key] = PoolBound(
            pool_key=key,
            quantity_upper=quantity_upper[key],
            value_upper=value_upper,
            unit_cost_upper=unit_cost_upper,
            minimum_meaningful_quantity=epsilon,
            derivation="opening/storage + source capacity + inbound lane capacity + transformation capacity; value propagated along the acyclic pool dependency graph",
        )

    report = BoundReport(
        pools=pools,
        shipment_dispatch_value_upper=dispatch_bounds,
        shipment_receipt_value_upper=receipt_bounds,
        production_input_value_upper=production_input_bounds,
        production_output_value_upper=production_output_bounds,
    )
    report.assert_finite()
    return report
