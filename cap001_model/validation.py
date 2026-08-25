"""Independent physical validation of extracted CAP-001 decisions."""

from __future__ import annotations

from dataclasses import dataclass

from cap001_model.baseline import BaselineSolution
from cap001_model.data import ModelData, PoolKey


@dataclass(frozen=True)
class PhysicalViolation:
    rule: str
    entity_id: str
    residual: float
    tolerance: float


@dataclass(frozen=True)
class PhysicalValidation:
    checked_equations: int
    max_residual: float
    violations: tuple[PhysicalViolation, ...]

    @property
    def passed(self) -> bool:
        return not self.violations


class _Checks:
    def __init__(self, data: ModelData):
        policy = data.config["tolerances"]["quantity"]
        self.absolute = policy["absolute"]
        self.relative = policy["relative"]
        self.checked = 0
        self.maximum = 0.0
        self.violations: list[PhysicalViolation] = []

    def _tolerance(self, lhs: float, rhs: float) -> float:
        return self.absolute + self.relative * max(abs(lhs), abs(rhs))

    def equality(self, rule: str, entity_id: str, lhs: float, rhs: float) -> None:
        self._record(rule, entity_id, abs(lhs - rhs), self._tolerance(lhs, rhs))

    def upper(self, rule: str, entity_id: str, lhs: float, upper: float) -> None:
        self._record(
            rule, entity_id, max(0.0, lhs - upper), self._tolerance(lhs, upper)
        )

    def lower(self, rule: str, entity_id: str, lhs: float, lower: float) -> None:
        self._record(
            rule, entity_id, max(0.0, lower - lhs), self._tolerance(lhs, lower)
        )

    def _record(
        self, rule: str, entity_id: str, residual: float, tolerance: float
    ) -> None:
        self.checked += 1
        self.maximum = max(self.maximum, residual)
        if residual > tolerance:
            self.violations.append(
                PhysicalViolation(
                    rule=rule,
                    entity_id=entity_id,
                    residual=residual,
                    tolerance=tolerance,
                )
            )


def validate_baseline_solution(
    data: ModelData, solution: BaselineSolution
) -> PhysicalValidation:
    """Recompute balances and limits using extracted values only."""

    if not solution.success:
        raise ValueError("only a successful solution can be physically validated")
    checks = _Checks(data)

    for key, row in data.source_capacity.items():
        quantity = solution.source_supply[key]
        regular = solution.source_regular[key]
        surge = solution.source_surge[key]
        availability = 1 - row["planned_downtime_fraction"]
        entity = "/".join(key)
        checks.equality("SOURCE_SPLIT", entity, quantity, regular + surge)
        checks.lower("SOURCE_REGULAR_NONNEGATIVE", entity, regular, 0.0)
        checks.lower("SOURCE_SURGE_NONNEGATIVE", entity, surge, 0.0)
        checks.upper(
            "SOURCE_REGULAR_CAPACITY",
            entity,
            regular,
            row["regular_capacity"] * availability,
        )
        checks.upper(
            "SOURCE_SURGE_CAPACITY",
            entity,
            surge,
            row["surge_capacity"] * availability,
        )
        checks.lower("SOURCE_MINIMUM", entity, quantity, row["minimum_supply_quantity"])

    for route_id, route in data.shipment_routes.items():
        quantity = solution.shipments[route_id]
        active = solution.shipment_active[route_id]
        lots = solution.shipment_lots[route_id]
        checks.lower("SHIPMENT_NONNEGATIVE", route_id, quantity, 0.0)
        checks._record(
            "SHIPMENT_ACTIVE_BINARY",
            route_id,
            abs(active - round(active)),
            checks.absolute,
        )
        checks._record(
            "SHIPMENT_LOTS_INTEGER",
            route_id,
            abs(lots - round(lots)),
            checks.absolute,
        )
        checks.equality(
            "ORDER_MULTIPLE",
            route_id,
            quantity,
            route.order_multiple * lots,
        )
        checks.lower(
            "ORDER_MINIMUM", route_id, quantity, route.minimum_order_quantity * active
        )
        checks.upper("LANE_CAPACITY", route_id, quantity, route.capacity * active)
        checks.upper(
            "CONTRACT_ACTIVATION_LOWER",
            route_id,
            active,
            solution.contract_active[route.contract_id],
        )

    approval_periods = {
        (route.approval_id, route.dispatch_period_id)
        for route in data.shipment_routes.values()
        if route.maximum_approved_share is not None
    }
    for approval_id, period_id in sorted(approval_periods):
        routes = [
            route
            for route in data.shipment_routes.values()
            if route.approval_id == approval_id
            and route.dispatch_period_id == period_id
        ]
        route = routes[0]
        approval_total = sum(solution.shipments[item.route_id] for item in routes)
        group_total = sum(
            solution.shipments[candidate.route_id]
            for candidate in data.shipment_routes.values()
            if candidate.destination_node_id == route.destination_node_id
            and candidate.material_id == route.material_id
            and candidate.dispatch_period_id == period_id
        )
        checks.upper(
            "MAXIMUM_APPROVED_SHARE",
            f"{approval_id}/{period_id}",
            approval_total,
            route.maximum_approved_share * group_total,
        )

    contract_routes: dict[str, list[str]] = {}
    for route_id, route in data.shipment_routes.items():
        contract_routes.setdefault(route.contract_id, []).append(route_id)
    for contract_id, route_ids in contract_routes.items():
        active = solution.contract_active[contract_id]
        checks._record(
            "CONTRACT_ACTIVE_BINARY",
            contract_id,
            abs(active - round(active)),
            checks.absolute,
        )
        checks.upper(
            "CONTRACT_ACTIVATION_UPPER",
            contract_id,
            active,
            sum(solution.shipment_active[route_id] for route_id in route_ids),
        )

    for key, capacity in data.transformation_capacity.items():
        recipe_id, period_id = key
        quantity = solution.production[key]
        regular = solution.production_regular[key]
        surge = solution.production_surge[key]
        activation = solution.production_active[key]
        recipe = data.recipes[recipe_id]
        active = (
            recipe["effective_from_period"]
            <= period_id
            <= recipe["effective_to_period"]
        )
        availability = 1 - capacity["planned_downtime_fraction"]
        regular_capacity = capacity["regular_output_capacity"] * availability
        surge_capacity = capacity["surge_output_capacity"] * availability
        if not active:
            regular_capacity = 0.0
            surge_capacity = 0.0
        available = regular_capacity + surge_capacity
        entity = f"{recipe_id}/{period_id}"
        checks.equality("PRODUCTION_SPLIT", entity, quantity, regular + surge)
        checks.lower("PRODUCTION_REGULAR_NONNEGATIVE", entity, regular, 0.0)
        checks.lower("PRODUCTION_SURGE_NONNEGATIVE", entity, surge, 0.0)
        checks.upper("REGULAR_PRODUCTION_CAPACITY", entity, regular, regular_capacity)
        checks.upper("SURGE_PRODUCTION_CAPACITY", entity, surge, surge_capacity)
        checks._record(
            "PRODUCTION_ACTIVE_BINARY",
            entity,
            abs(activation - round(activation)),
            checks.absolute,
        )
        checks.upper(
            "PRODUCTION_ACTIVATION_UPPER",
            entity,
            quantity,
            available * activation,
        )
        checks.lower(
            "TRANSFORMATION_MINIMUM_RUN",
            entity,
            quantity,
            recipe["minimum_run_quantity"] * activation,
        )

    shared_groups: dict[tuple[str, str], list[str]] = {}
    for (recipe_id, period_id), capacity in data.transformation_capacity.items():
        group_id = capacity["shared_capacity_group_id"]
        if group_id is not None:
            shared_groups.setdefault((group_id, period_id), []).append(recipe_id)
    for (group_id, period_id), recipe_ids in sorted(shared_groups.items()):
        row = data.transformation_capacity[(recipe_ids[0], period_id)]
        availability = 1 - row["planned_downtime_fraction"]
        regular_use = sum(
            data.transformation_capacity[(recipe_id, period_id)][
                "shared_capacity_coefficient"
            ]
            * solution.production_regular[(recipe_id, period_id)]
            for recipe_id in recipe_ids
        )
        surge_use = sum(
            data.transformation_capacity[(recipe_id, period_id)][
                "shared_capacity_coefficient"
            ]
            * solution.production_surge[(recipe_id, period_id)]
            for recipe_id in recipe_ids
        )
        checks.upper(
            "SHARED_REGULAR_CAPACITY",
            f"{group_id}/{period_id}",
            regular_use,
            row["regular_output_capacity"] * availability,
        )
        checks.upper(
            "SHARED_SURGE_CAPACITY",
            f"{group_id}/{period_id}",
            surge_use,
            row["surge_output_capacity"] * availability,
        )

    for key, demand in data.demand.items():
        checks.equality(
            "DEMAND_BALANCE",
            "/".join(key),
            solution.served[key] + solution.shortage[key],
            demand["demand_quantity"],
        )

    arrivals: dict[PoolKey, float] = {key: 0.0 for key in data.pool_keys}
    dispatches: dict[PoolKey, float] = {key: 0.0 for key in data.pool_keys}
    for route_id, route in data.shipment_routes.items():
        quantity = solution.shipments[route_id]
        arrivals[
            (route.destination_node_id, route.material_id, route.arrival_period_id)
        ] += quantity
        dispatches[
            (route.origin_node_id, route.material_id, route.dispatch_period_id)
        ] += quantity

    produced: dict[PoolKey, float] = {key: 0.0 for key in data.pool_keys}
    consumed: dict[PoolKey, float] = {key: 0.0 for key in data.pool_keys}
    for (recipe_id, period_id), quantity in solution.production.items():
        recipe = data.recipes[recipe_id]
        produced[(recipe["node_id"], recipe["output_material_id"], period_id)] += (
            quantity
        )
        for input_row in data.recipe_inputs[recipe_id]:
            consumed[
                (recipe["node_id"], input_row["input_material_id"], period_id)
            ] += input_row["quantity_per_output"] * quantity / recipe["yield_rate"]

    for node, material, period in data.pool_keys:
        key = (node, material, period)
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening = opening_row["usable_quantity"] if opening_row else 0.0
        else:
            opening = solution.closing_inventory[(node, material, previous)]
        source = solution.source_supply.get(key, 0.0)
        served = solution.served.get(key, 0.0)
        lhs = opening + source + arrivals[key] + produced[key]
        rhs = consumed[key] + dispatches[key] + served + solution.closing_inventory[key]
        checks.equality("POOL_QUANTITY_BALANCE", "/".join(key), lhs, rhs)
        maximum = data.inventory_policy[(node, material)]["maximum_storage_quantity"]
        checks.upper(
            "MAXIMUM_STORAGE",
            "/".join(key),
            solution.closing_inventory[key],
            maximum,
        )
        policy = data.inventory_policy[(node, material)]
        if policy["safety_stock_treatment"] == "HARD":
            checks.lower(
                "HARD_SAFETY_STOCK",
                "/".join(key),
                solution.closing_inventory[key],
                policy["safety_stock_quantity"],
            )

    return PhysicalValidation(
        checked_equations=checks.checked,
        max_residual=checks.maximum,
        violations=tuple(checks.violations),
    )
