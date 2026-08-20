"""Bounded recursive-cost MINLP and canonical fixture solve route."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

import pyomo.environ as pyo

from cap001_model.baseline import BaselineSolution
from cap001_model.bounds import BoundReport, dependency_order, derive_recursive_bounds
from cap001_model.contracts import (
    FormulationClass,
    MethodClassification,
    ObjectiveStageResult,
    SolutionStatus,
    SolverAdapter,
    SolverEvidence,
)
from cap001_model.data import DemandKey, ModelData, PoolKey, load_model_data
from cap001_model.physical import active_in_period, build_physical_model
from cap001_model.solvers import IpoptSolverAdapter, MindtPySolverAdapter


RecipeInputPeriodKey = tuple[str, str, str]


@dataclass(frozen=True)
class RecursiveModel:
    formulation_class: FormulationClass
    method_classification: MethodClassification
    data: ModelData
    bounds: BoundReport
    model: pyo.ConcreteModel
    physical_constraint_names: tuple[str, ...]


@dataclass(frozen=True)
class RecursiveSolution:
    status: SolutionStatus
    formulation_class: FormulationClass
    method_classification: MethodClassification
    method_description: str
    stages: tuple[ObjectiveStageResult, ...]
    solver_evidence: tuple[SolverEvidence, ...]
    source_supply: Mapping[tuple[str, str, str], float]
    source_regular: Mapping[tuple[str, str, str], float]
    source_surge: Mapping[tuple[str, str, str], float]
    shipments: Mapping[str, float]
    shipment_active: Mapping[str, float]
    shipment_lots: Mapping[str, float]
    contract_active: Mapping[str, float]
    production: Mapping[tuple[str, str], float]
    production_regular: Mapping[tuple[str, str], float]
    production_surge: Mapping[tuple[str, str], float]
    production_active: Mapping[tuple[str, str], float]
    closing_inventory: Mapping[PoolKey, float]
    served: Mapping[DemandKey, float]
    shortage: Mapping[DemandKey, float]
    pool_quantity: Mapping[PoolKey, float]
    pool_value: Mapping[PoolKey, float]
    unit_cost: Mapping[PoolKey, float]
    closing_value: Mapping[PoolKey, float]
    served_value: Mapping[DemandKey, float]
    shipment_dispatch_value: Mapping[str, float]
    shipment_receipt_value: Mapping[str, float]
    production_input_value: Mapping[RecipeInputPeriodKey, float]
    production_output_value: Mapping[tuple[str, str], float]

    @property
    def success(self) -> bool:
        return self.status in {
            SolutionStatus.GLOBALLY_OPTIMAL,
            SolutionStatus.LOCALLY_OPTIMAL,
            SolutionStatus.FEASIBLE_TIME_LIMITED,
            SolutionStatus.BEST_FOUND,
        }


def _cost_rules(data: ModelData) -> dict[str, Mapping[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in data.rows("cost_allocation_rules.csv"):
        grouped.setdefault(row["cost_component"], []).append(row)
    return {
        component: sorted(rows, key=lambda row: -row["precedence"])[0]
        for component, rows in grouped.items()
    }


def build_recursive_model(data: ModelData | None = None) -> RecursiveModel:
    """Add bounded weighted-average value equations to the shared physical core."""

    if data is None:
        data = load_model_data()
    bounds = derive_recursive_bounds(data)
    model = build_physical_model(data, name="CAP-001 recursive-cost MINLP")
    physical_constraint_names = tuple(
        component.name
        for component in model.component_objects(pyo.Constraint, active=True)
    )
    route_ids = tuple(model.ROUTE)
    recipe_period_keys = tuple(model.RECIPE_PERIOD)
    demand_keys = tuple(model.DEMAND)
    input_period_keys = tuple(
        (recipe_id, input_row["input_material_id"], period_id)
        for recipe_id in sorted(data.recipes)
        for input_row in data.recipe_inputs[recipe_id]
        for period_id in data.periods
    )
    model.RECIPE_INPUT_PERIOD = pyo.Set(
        initialize=input_period_keys, dimen=3, ordered=True
    )

    model.pool_quantity = pyo.Var(
        model.POOL,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, node, material, period: (
            0.0,
            bounds.pools[(node, material, period)].quantity_upper,
        ),
    )
    model.pool_value = pyo.Var(
        model.POOL,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, node, material, period: (
            0.0,
            bounds.pools[(node, material, period)].value_upper,
        ),
    )
    model.unit_cost = pyo.Var(
        model.POOL,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, node, material, period: (
            0.0,
            bounds.pools[(node, material, period)].unit_cost_upper,
        ),
    )
    model.pool_active = pyo.Var(model.POOL, domain=pyo.Binary)
    model.closing_value = pyo.Var(
        model.POOL,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, node, material, period: (
            0.0,
            bounds.pools[(node, material, period)].value_upper,
        ),
    )
    model.served_value = pyo.Var(
        model.DEMAND,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, node, material, period: (
            0.0,
            bounds.pools[(node, material, period)].value_upper,
        ),
    )
    model.shipment_dispatch_value = pyo.Var(
        model.ROUTE,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, route_id: (
            0.0,
            bounds.shipment_dispatch_value_upper[route_id],
        ),
    )
    model.shipment_receipt_value = pyo.Var(
        model.ROUTE,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, route_id: (
            0.0,
            bounds.shipment_receipt_value_upper[route_id],
        ),
    )
    model.consumption_value = pyo.Var(
        model.RECIPE_INPUT_PERIOD,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, recipe_id, input_material, period: (
            0.0,
            bounds.pools[
                (data.recipes[recipe_id]["node_id"], input_material, period)
            ].value_upper,
        ),
    )
    model.production_output_value = pyo.Var(
        model.RECIPE_PERIOD,
        domain=pyo.NonNegativeReals,
        bounds=lambda _, recipe_id, period: (
            0.0,
            bounds.production_output_value_upper.get((recipe_id, period), 0.0),
        ),
    )

    model.pool_quantity_activation_upper = pyo.Constraint(
        model.POOL,
        rule=lambda m, node, material, period: m.pool_quantity[
            node, material, period
        ]
        <= bounds.pools[(node, material, period)].quantity_upper
        * m.pool_active[node, material, period],
    )
    model.pool_quantity_activation_lower = pyo.Constraint(
        model.POOL,
        rule=lambda m, node, material, period: m.pool_quantity[
            node, material, period
        ]
        >= bounds.pools[(node, material, period)].minimum_meaningful_quantity
        * m.pool_active[node, material, period],
    )
    model.pool_value_activation = pyo.Constraint(
        model.POOL,
        rule=lambda m, node, material, period: m.pool_value[node, material, period]
        <= bounds.pools[(node, material, period)].value_upper
        * m.pool_active[node, material, period],
    )
    model.unit_cost_activation = pyo.Constraint(
        model.POOL,
        rule=lambda m, node, material, period: m.unit_cost[node, material, period]
        <= bounds.pools[(node, material, period)].unit_cost_upper
        * m.pool_active[node, material, period],
    )
    model.pool_unit_cost = pyo.Constraint(
        model.POOL,
        rule=lambda m, node, material, period: m.pool_value[node, material, period]
        == m.unit_cost[node, material, period]
        * m.pool_quantity[node, material, period],
    )
    model.closing_value_definition = pyo.Constraint(
        model.POOL,
        rule=lambda m, node, material, period: m.closing_value[
            node, material, period
        ]
        == m.unit_cost[node, material, period]
        * m.closing_inventory[node, material, period],
    )
    model.served_value_definition = pyo.Constraint(
        model.DEMAND,
        rule=lambda m, node, material, period: m.served_value[
            node, material, period
        ]
        == m.unit_cost[node, material, period] * m.served[node, material, period],
    )
    model.shipment_dispatch_value_definition = pyo.Constraint(
        model.ROUTE,
        rule=lambda m, route_id: m.shipment_dispatch_value[route_id]
        == m.unit_cost[
            data.shipment_routes[route_id].origin_node_id,
            data.shipment_routes[route_id].material_id,
            data.shipment_routes[route_id].dispatch_period_id,
        ]
        * m.shipment_quantity[route_id],
    )
    model.shipment_receipt_value_definition = pyo.Constraint(
        model.ROUTE,
        rule=lambda m, route_id: m.shipment_receipt_value[route_id]
        == m.shipment_dispatch_value[route_id]
        * (
            1
            + data.shipment_routes[route_id].insurance_rate
            + data.shipment_routes[route_id].duty_rate
        )
        + data.shipment_routes[route_id].freight_unit_eur
        * m.shipment_quantity[route_id]
        * (
            1
            + (
                data.shipment_routes[route_id].duty_rate
                if data.shipment_routes[route_id].duty_on_freight
                else 0.0
            )
        )
        + (
            data.shipment_routes[route_id].fixed_order_cost_eur
            + data.shipment_routes[route_id].fixed_shipment_cost_eur
        )
        * m.shipment_active[route_id],
    )

    def consumption_value_rule(
        m: pyo.ConcreteModel,
        recipe_id: str,
        input_material: str,
        period: str,
    ):
        recipe = data.recipes[recipe_id]
        input_row = next(
            row
            for row in data.recipe_inputs[recipe_id]
            if row["input_material_id"] == input_material
        )
        coefficient = input_row["quantity_per_output"] / recipe["yield_rate"]
        return m.consumption_value[recipe_id, input_material, period] == m.unit_cost[
            recipe["node_id"], input_material, period
        ] * coefficient * m.production_quantity[recipe_id, period]

    model.consumption_value_definition = pyo.Constraint(
        model.RECIPE_INPUT_PERIOD, rule=consumption_value_rule
    )

    rules = _cost_rules(data)
    eligible_names = set(data.config["cost_policy"]["default_markup_eligible_base"])
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in data.rows("fx_rates.csv")
    }

    def production_output_value_rule(
        m: pyo.ConcreteModel, recipe_id: str, period: str
    ):
        recipe = data.recipes[recipe_id]
        conversion_row = data.conversion_costs[(recipe_id, period)]
        capacity_row = data.transformation_capacity[(recipe_id, period)]
        currency_rate = fx[(conversion_row["currency"], period)]
        input_value = sum(
            m.consumption_value[recipe_id, row["input_material_id"], period]
            for row in data.recipe_inputs[recipe_id]
        )
        conversion = (
            conversion_row["variable_conversion_cost_per_output"]
            * currency_rate
            * m.production_quantity[recipe_id, period]
            + capacity_row["surge_conversion_premium"]
            * currency_rate
            * m.production_surge[recipe_id, period]
        )
        setup = (
            conversion_row["fixed_setup_cost"]
            * currency_rate
            * m.production_active[recipe_id, period]
            if recipe["setup_required_flag"]
            else 0.0
        )
        overhead = (
            conversion_row["eligible_overhead_fixed"]
            * currency_rate
            * m.production_active[recipe_id, period]
            + conversion_row["eligible_overhead_variable"]
            * currency_rate
            * m.production_quantity[recipe_id, period]
        )
        markup_base = (
            (input_value if "INPUT_VALUE" in eligible_names else 0.0)
            + (
                conversion
                if rules["CONVERSION"]["markup_eligible_flag"]
                and "CONVERSION" in eligible_names
                else 0.0
            )
            + (
                setup
                if rules["SETUP"]["markup_eligible_flag"]
                and "SETUP" in eligible_names
                else 0.0
            )
            + (
                overhead
                if rules["OVERHEAD"]["markup_eligible_flag"]
                and "ELIGIBLE_OVERHEAD" in eligible_names
                else 0.0
            )
        )
        markup = conversion_row["markup_rate"] * markup_base
        return m.production_output_value[recipe_id, period] == (
            input_value + conversion + setup + overhead + markup
        )

    model.production_output_value_definition = pyo.Constraint(
        model.RECIPE_PERIOD, rule=production_output_value_rule
    )

    model.source_value = pyo.Expression(
        model.SOURCE,
        rule=lambda m, node, material, period: data.source_unit_prices[
            (node, material, period)
        ]
        * m.source_regular[node, material, period]
        + (
            data.source_unit_prices[(node, material, period)]
            + data.source_capacity[(node, material, period)]["surge_unit_premium"]
        )
        * m.source_surge[node, material, period],
    )

    arrivals: dict[PoolKey, tuple[str, ...]] = {}
    dispatches: dict[PoolKey, tuple[str, ...]] = {}
    outputs: dict[PoolKey, tuple[str, ...]] = {}
    inputs: dict[PoolKey, tuple[str, ...]] = {}
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
        outputs[key] = tuple(
            recipe_id
            for recipe_id, recipe in data.recipes.items()
            if recipe["node_id"] == node
            and recipe["output_material_id"] == material
            and active_in_period(recipe, period)
        )
        inputs[key] = tuple(
            recipe_id
            for recipe_id, recipe in data.recipes.items()
            if recipe["node_id"] == node
            and active_in_period(recipe, period)
            and any(
                row["input_material_id"] == material
                for row in data.recipe_inputs[recipe_id]
            )
        )

    def pool_quantity_rule(m: pyo.ConcreteModel, node: str, material: str, period: str):
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
        return m.pool_quantity[node, material, period] == (
            opening
            + source
            + sum(m.shipment_quantity[route_id] for route_id in arrivals[(node, material, period)])
            + sum(
                m.production_quantity[recipe_id, period]
                for recipe_id in outputs[(node, material, period)]
            )
        )

    model.pool_quantity_definition = pyo.Constraint(model.POOL, rule=pool_quantity_rule)

    def pool_value_rule(m: pyo.ConcreteModel, node: str, material: str, period: str):
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening = opening_row["opening_total_value_eur"] if opening_row else 0.0
        else:
            opening = m.closing_value[node, material, previous]
        source = (
            m.source_value[node, material, period]
            if (node, material, period) in data.source_capacity
            else 0.0
        )
        return m.pool_value[node, material, period] == (
            opening
            + source
            + sum(
                m.shipment_receipt_value[route_id]
                for route_id in arrivals[(node, material, period)]
            )
            + sum(
                m.production_output_value[recipe_id, period]
                for recipe_id in outputs[(node, material, period)]
            )
        )

    model.pool_value_rollforward = pyo.Constraint(model.POOL, rule=pool_value_rule)

    model.pool_value_conservation_residual = pyo.Expression(
        model.POOL,
        rule=lambda m, node, material, period: (
            m.pool_value[node, material, period]
            - m.closing_value[node, material, period]
            - (
                m.served_value[node, material, period]
                if (node, material, period) in data.demand
                else 0.0
            )
            - sum(
                m.shipment_dispatch_value[route_id]
                for route_id in dispatches[(node, material, period)]
            )
            - sum(
                m.consumption_value[recipe_id, material, period]
                for recipe_id in inputs[(node, material, period)]
            )
        ),
    )

    stage_1 = sum(
        data.demand[key]["service_weight"] * model.shortage[key]
        for key in demand_keys
    )
    final_period = data.periods[-1]
    served_and_closing_value = sum(
        model.served_value[key] for key in demand_keys
    ) + sum(
        model.closing_value[node, material, final_period]
        for node, material in data.inventory_policy
    )
    holding = sum(
        data.inventory_policy[(node, material)]["holding_cost_eur_per_unit_week"]
        * model.closing_inventory[node, material, period]
        for node, material, period in data.pool_keys
    )
    shortage_cost = sum(
        data.demand[key]["shortage_penalty_eur_per_unit"] * model.shortage[key]
        for key in demand_keys
    )
    activation_by_contract = {
        contract_id: max(
            route.horizon_activation_cost_eur
            for route in data.shipment_routes.values()
            if route.contract_id == contract_id
        )
        for contract_id in model.CONTRACT
    }
    activation = sum(
        activation_by_contract[contract_id] * model.contract_active[contract_id]
        for contract_id in model.CONTRACT
    )
    stage_2 = served_and_closing_value + holding + shortage_cost + activation
    stage_3 = (
        sum(model.closing_inventory[key] for key in data.pool_keys)
        + sum(model.shipment_active[route_id] for route_id in route_ids)
        + sum(model.production_active[key] for key in recipe_period_keys)
        + sum(model.contract_active[contract_id] for contract_id in model.CONTRACT)
    )
    model.stage_1_objective = pyo.Objective(expr=stage_1, sense=pyo.minimize)
    model.stage_2_objective = pyo.Objective(expr=stage_2, sense=pyo.minimize)
    model.stage_3_objective = pyo.Objective(expr=stage_3, sense=pyo.minimize)
    model.stage_2_objective.deactivate()
    model.stage_3_objective.deactivate()
    model.lexicographic_locks = pyo.ConstraintList()
    return RecursiveModel(
        formulation_class=FormulationClass.MINLP,
        method_classification=MethodClassification.EXACT,
        data=data,
        bounds=bounds,
        model=model,
        physical_constraint_names=physical_constraint_names,
    )


def _physical_pool_quantities(
    data: ModelData, physical: BaselineSolution
) -> dict[PoolKey, float]:
    arrivals: dict[PoolKey, float] = {key: 0.0 for key in data.pool_keys}
    produced: dict[PoolKey, float] = {key: 0.0 for key in data.pool_keys}
    for route_id, route in data.shipment_routes.items():
        arrivals[
            (route.destination_node_id, route.material_id, route.arrival_period_id)
        ] += physical.shipments[route_id]
    for (recipe_id, period), quantity in physical.production.items():
        recipe = data.recipes[recipe_id]
        produced[(recipe["node_id"], recipe["output_material_id"], period)] += quantity
    quantities: dict[PoolKey, float] = {}
    for node, material, period in data.pool_keys:
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening = opening_row["usable_quantity"] if opening_row else 0.0
        else:
            opening = physical.closing_inventory[(node, material, previous)]
        quantities[(node, material, period)] = (
            opening
            + physical.source_supply.get((node, material, period), 0.0)
            + arrivals[(node, material, period)]
            + produced[(node, material, period)]
        )
    return quantities


def _normalise_physical_solution(
    data: ModelData, physical: BaselineSolution
) -> BaselineSolution:
    """Remove tolerance-scale solver noise before fixing discrete decisions."""

    from cap001_model.validation import validate_baseline_solution

    tolerance = data.config["tolerances"]["quantity"]["absolute"]

    def nonnegative(value: float) -> float:
        return 0.0 if abs(value) <= tolerance else value

    source_regular = {
        key: nonnegative(value) for key, value in physical.source_regular.items()
    }
    source_surge = {
        key: nonnegative(value) for key, value in physical.source_surge.items()
    }
    shipment_lots = {
        route_id: float(round(value))
        for route_id, value in physical.shipment_lots.items()
    }
    shipments = {
        route_id: data.shipment_routes[route_id].order_multiple
        * shipment_lots[route_id]
        for route_id in physical.shipments
    }
    production_regular = {
        key: nonnegative(value) for key, value in physical.production_regular.items()
    }
    production_surge = {
        key: nonnegative(value) for key, value in physical.production_surge.items()
    }
    production = {
        key: production_regular[key] + production_surge[key]
        for key in physical.production
    }
    shipment_active = {
        route_id: float(shipment_lots[route_id] > 0)
        for route_id in physical.shipment_active
    }
    contract_active = {
        contract_id: float(
            any(
                shipment_active[route_id] > 0.5
                for route_id, route in data.shipment_routes.items()
                if route.contract_id == contract_id
            )
        )
        for contract_id in physical.contract_active
    }
    shortage = {key: nonnegative(value) for key, value in physical.shortage.items()}
    served = {
        key: data.demand[key]["demand_quantity"] - shortage[key]
        for key in physical.served
    }
    normalised = replace(
        physical,
        source_regular=source_regular,
        source_surge=source_surge,
        source_supply={
            key: source_regular[key] + source_surge[key]
            for key in physical.source_supply
        },
        shipments=shipments,
        shipment_active=shipment_active,
        shipment_lots=shipment_lots,
        contract_active=contract_active,
        production_regular=production_regular,
        production_surge=production_surge,
        production=production,
        production_active={
            key: float(production[key] > tolerance) for key in physical.production_active
        },
        closing_inventory={
            key: nonnegative(value)
            for key, value in physical.closing_inventory.items()
        },
        served=served,
        shortage=shortage,
    )
    validation = validate_baseline_solution(data, normalised)
    if not validation.passed:
        raise ValueError(
            "normalising solver tolerances invalidated the physical plan: "
            f"{len(validation.violations)} violations"
        )
    return normalised


def _fix_physical_decisions(recursive: RecursiveModel, physical: BaselineSolution) -> None:
    if not physical.success:
        raise ValueError("a successful physical solution is required")
    data = recursive.data
    model = recursive.model
    from cap001_model.validation import validate_baseline_solution

    validation = validate_baseline_solution(data, physical)
    if not validation.passed:
        raise ValueError(f"physical plan has {len(validation.violations)} violations")
    for key in physical.source_supply:
        model.source_regular[key].fix(physical.source_regular[key])
        model.source_surge[key].fix(physical.source_surge[key])
    for route_id, quantity in physical.shipments.items():
        active = physical.shipment_active[route_id]
        model.shipment_quantity[route_id].fix(quantity)
        model.shipment_active[route_id].fix(active)
        model.shipment_lots[route_id].fix(physical.shipment_lots[route_id])
    for contract_id in model.CONTRACT:
        model.contract_active[contract_id].fix(physical.contract_active[contract_id])
    for key in physical.production:
        model.production_regular[key].fix(physical.production_regular[key])
        model.production_surge[key].fix(physical.production_surge[key])
        model.production_active[key].fix(physical.production_active[key])
    for key, quantity in physical.closing_inventory.items():
        model.closing_inventory[key].fix(quantity)
    for key, quantity in physical.served.items():
        model.served[key].fix(quantity)
        model.shortage[key].fix(physical.shortage[key])

    quantities = _physical_pool_quantities(data, physical)
    for key, quantity in quantities.items():
        model.pool_quantity[key].value = quantity
        epsilon = recursive.bounds.pools[key].minimum_meaningful_quantity
        model.pool_active[key].fix(int(quantity >= epsilon))
    # With every physical decision fixed and independently validated, the
    # physical equalities would be constant redundant rows in the conditioned
    # NLP. Deactivate those rows for IPOPT; the original variables, bounds and
    # named components remain part of the constructed MINLP.
    for name in recursive.physical_constraint_names:
        model.find_component(name).deactivate()


def _initialize_values(recursive: RecursiveModel, physical: BaselineSolution) -> None:
    """Create a feasible value-flow warm start from fixed physical decisions."""

    data = recursive.data
    model = recursive.model
    pool_value: dict[PoolKey, float] = {}
    unit_cost: dict[PoolKey, float] = {}
    closing_value: dict[PoolKey, float] = {}
    route_dispatch: dict[str, float] = {}
    route_receipt: dict[str, float] = {}
    production_output: dict[tuple[str, str], float] = {}
    consumption_value: dict[RecipeInputPeriodKey, float] = {}
    rules = _cost_rules(data)
    eligible_names = set(data.config["cost_policy"]["default_markup_eligible_base"])
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in data.rows("fx_rates.csv")
    }
    for key in model.RECIPE_INPUT_PERIOD:
        model.consumption_value[key].value = 0.0
    for key in model.RECIPE_PERIOD:
        model.production_output_value[key].value = 0.0

    for key in dependency_order(data):
        node, material, period = key
        previous = data.previous_period(period)
        if previous is None:
            opening_row = data.opening_inventory.get((node, material))
            opening = opening_row["opening_total_value_eur"] if opening_row else 0.0
        else:
            opening = closing_value[(node, material, previous)]
        source = 0.0
        if key in data.source_capacity:
            source = float(pyo.value(model.source_value[key]))
        receipts = sum(
            route_receipt[route_id]
            for route_id, route in data.shipment_routes.items()
            if (
                route.destination_node_id,
                route.material_id,
                route.arrival_period_id,
            )
            == key
        )
        outputs = 0.0
        for recipe_id, recipe in data.recipes.items():
            if (
                recipe["node_id"] != node
                or recipe["output_material_id"] != material
                or not active_in_period(recipe, period)
            ):
                continue
            quantity = physical.production[(recipe_id, period)]
            input_value = 0.0
            for input_row in data.recipe_inputs[recipe_id]:
                input_key = (recipe_id, input_row["input_material_id"], period)
                value = (
                    unit_cost[(node, input_row["input_material_id"], period)]
                    * input_row["quantity_per_output"]
                    * quantity
                    / recipe["yield_rate"]
                )
                consumption_value[input_key] = value
                model.consumption_value[input_key].value = value
                input_value += value
            conversion_row = data.conversion_costs[(recipe_id, period)]
            capacity_row = data.transformation_capacity[(recipe_id, period)]
            currency_rate = fx[(conversion_row["currency"], period)]
            conversion = (
                conversion_row["variable_conversion_cost_per_output"]
                * currency_rate
                * quantity
                + capacity_row["surge_conversion_premium"]
                * currency_rate
                * float(pyo.value(model.production_surge[recipe_id, period]))
            )
            active = quantity > data.config["tolerances"]["quantity"]["absolute"]
            setup = (
                conversion_row["fixed_setup_cost"] * currency_rate
                if recipe["setup_required_flag"] and active
                else 0.0
            )
            overhead = (
                conversion_row["eligible_overhead_fixed"] * currency_rate
                if active
                else 0.0
            ) + conversion_row["eligible_overhead_variable"] * currency_rate * quantity
            markup_base = (
                (input_value if "INPUT_VALUE" in eligible_names else 0.0)
                + (
                    conversion
                    if rules["CONVERSION"]["markup_eligible_flag"]
                    and "CONVERSION" in eligible_names
                    else 0.0
                )
                + (
                    setup
                    if rules["SETUP"]["markup_eligible_flag"]
                    and "SETUP" in eligible_names
                    else 0.0
                )
                + (
                    overhead
                    if rules["OVERHEAD"]["markup_eligible_flag"]
                    and "ELIGIBLE_OVERHEAD" in eligible_names
                    else 0.0
                )
            )
            output = (
                input_value
                + conversion
                + setup
                + overhead
                + conversion_row["markup_rate"] * markup_base
            )
            production_output[(recipe_id, period)] = output
            model.production_output_value[recipe_id, period].value = output
            outputs += output
        value = opening + source + receipts + outputs
        quantity = float(pyo.value(model.pool_quantity[key]))
        cost = value / quantity if quantity > 0 else 0.0
        close = cost * physical.closing_inventory[key]
        pool_value[key] = value
        unit_cost[key] = cost
        closing_value[key] = close
        model.pool_value[key].value = value
        model.unit_cost[key].value = cost
        model.closing_value[key].value = close
        if key in data.demand:
            model.served_value[key].value = cost * physical.served[key]
        for route_id, route in data.shipment_routes.items():
            if (
                route.origin_node_id,
                route.material_id,
                route.dispatch_period_id,
            ) != key:
                continue
            dispatched = cost * physical.shipments[route_id]
            received = (
                dispatched * (1 + route.insurance_rate + route.duty_rate)
                + route.freight_unit_eur
                * physical.shipments[route_id]
                * (1 + (route.duty_rate if route.duty_on_freight else 0.0))
                + (
                    route.fixed_order_cost_eur + route.fixed_shipment_cost_eur
                    if physical.shipments[route_id] > 0
                    else 0.0
                )
            )
            route_dispatch[route_id] = dispatched
            route_receipt[route_id] = received
            model.shipment_dispatch_value[route_id].value = dispatched
            model.shipment_receipt_value[route_id].value = received


def _lock_tolerance(data: ModelData, kind: str, value: float) -> float:
    policy = data.config["tolerances"][kind]
    return policy["absolute"] + policy.get("relative", 0.0) * abs(value)


def _empty_solution(
    status: SolutionStatus,
    stages: list[ObjectiveStageResult],
    evidence: list[SolverEvidence],
    *,
    method_description: str,
) -> RecursiveSolution:
    return RecursiveSolution(
        status=status,
        formulation_class=FormulationClass.MINLP,
        method_classification=MethodClassification.HEURISTIC,
        method_description=method_description,
        stages=tuple(stages),
        solver_evidence=tuple(evidence),
        source_supply={},
        source_regular={},
        source_surge={},
        shipments={},
        shipment_active={},
        shipment_lots={},
        contract_active={},
        production={},
        production_regular={},
        production_surge={},
        production_active={},
        closing_inventory={},
        served={},
        shortage={},
        pool_quantity={},
        pool_value={},
        unit_cost={},
        closing_value={},
        served_value={},
        shipment_dispatch_value={},
        shipment_receipt_value={},
        production_input_value={},
        production_output_value={},
    )


def _extract_solution(
    recursive: RecursiveModel,
    stages: list[ObjectiveStageResult],
    evidence: list[SolverEvidence],
    *,
    method_description: str,
) -> RecursiveSolution:
    model = recursive.model
    return RecursiveSolution(
        status=evidence[-1].status,
        formulation_class=FormulationClass.MINLP,
        method_classification=MethodClassification.HEURISTIC,
        method_description=method_description,
        stages=tuple(stages),
        solver_evidence=tuple(evidence),
        source_supply={
            key: float(pyo.value(model.source_supply[key]))
            for key in recursive.data.source_capacity
        },
        source_regular={
            key: float(pyo.value(model.source_regular[key]))
            for key in recursive.data.source_capacity
        },
        source_surge={
            key: float(pyo.value(model.source_surge[key]))
            for key in recursive.data.source_capacity
        },
        shipments={
            route_id: float(pyo.value(model.shipment_quantity[route_id]))
            for route_id in recursive.data.shipment_routes
        },
        shipment_active={
            route_id: float(pyo.value(model.shipment_active[route_id]))
            for route_id in recursive.data.shipment_routes
        },
        shipment_lots={
            route_id: float(pyo.value(model.shipment_lots[route_id]))
            for route_id in recursive.data.shipment_routes
        },
        contract_active={
            contract_id: float(pyo.value(model.contract_active[contract_id]))
            for contract_id in model.CONTRACT
        },
        production={
            key: float(pyo.value(model.production_quantity[key]))
            for key in model.RECIPE_PERIOD
        },
        production_regular={
            key: float(pyo.value(model.production_regular[key]))
            for key in model.RECIPE_PERIOD
        },
        production_surge={
            key: float(pyo.value(model.production_surge[key]))
            for key in model.RECIPE_PERIOD
        },
        production_active={
            key: float(pyo.value(model.production_active[key]))
            for key in model.RECIPE_PERIOD
        },
        closing_inventory={
            key: float(pyo.value(model.closing_inventory[key]))
            for key in recursive.data.pool_keys
        },
        served={
            key: float(pyo.value(model.served[key])) for key in recursive.data.demand
        },
        shortage={
            key: float(pyo.value(model.shortage[key]))
            for key in recursive.data.demand
        },
        pool_quantity={
            key: float(pyo.value(model.pool_quantity[key]))
            for key in recursive.data.pool_keys
        },
        pool_value={
            key: float(pyo.value(model.pool_value[key]))
            for key in recursive.data.pool_keys
        },
        unit_cost={
            key: float(pyo.value(model.unit_cost[key]))
            for key in recursive.data.pool_keys
        },
        closing_value={
            key: float(pyo.value(model.closing_value[key]))
            for key in recursive.data.pool_keys
        },
        served_value={
            key: float(pyo.value(model.served_value[key]))
            for key in recursive.data.demand
        },
        shipment_dispatch_value={
            route_id: float(pyo.value(model.shipment_dispatch_value[route_id]))
            for route_id in recursive.data.shipment_routes
        },
        shipment_receipt_value={
            route_id: float(pyo.value(model.shipment_receipt_value[route_id]))
            for route_id in recursive.data.shipment_routes
        },
        production_input_value={
            key: float(pyo.value(model.consumption_value[key]))
            for key in model.RECIPE_INPUT_PERIOD
        },
        production_output_value={
            key: float(pyo.value(model.production_output_value[key]))
            for key in model.RECIPE_PERIOD
        },
    )


def solve_recursive(
    recursive: RecursiveModel,
    *,
    solver: SolverAdapter | None = None,
    time_limit_seconds: float | None = None,
) -> RecursiveSolution:
    """Search the unrestricted MINLP with an honestly classified OA route."""

    if solver is None:
        solver = MindtPySolverAdapter()
    if time_limit_seconds is None:
        time_limit_seconds = recursive.data.config["runtime_budgets"][
            "miniature_fixture_seconds"
        ]
    model = recursive.model
    stages: list[ObjectiveStageResult] = []
    evidence: list[SolverEvidence] = []
    definitions = (
        (1, "WEIGHTED_SHORTAGE", model.stage_1_objective, "quantity"),
        (2, "SERVED_AND_CLOSING_RECURSIVE_VALUE", model.stage_2_objective, "value"),
        (3, "SURPLUS_AND_UNNECESSARY_ACTIVATION", model.stage_3_objective, "quantity"),
    )
    method_description = (
        "MindtPy outer-approximation search with HiGHS MILP masters and IPOPT "
        "nonlinear subproblems; non-convex global optimality is not claimed"
    )
    per_stage_limit = time_limit_seconds / len(definitions)

    for position, (stage, name, objective, tolerance_kind) in enumerate(definitions):
        for candidate in (
            model.stage_1_objective,
            model.stage_2_objective,
            model.stage_3_objective,
        ):
            candidate.deactivate()
        objective.activate()
        stage_evidence = solver.solve(
            model,
            time_limit_seconds=per_stage_limit,
            options={
                "init_strategy": "rNLP" if position == 0 else "initial_binary"
            },
        )
        evidence.append(stage_evidence)
        if not stage_evidence.has_solution:
            return _empty_solution(
                stage_evidence.status,
                stages,
                evidence,
                method_description=method_description,
            )
        objective_value = float(pyo.value(objective.expr))
        tolerance = _lock_tolerance(recursive.data, tolerance_kind, objective_value)
        stages.append(
            ObjectiveStageResult(
                stage=stage,
                name=name,
                objective_value=objective_value,
                lock_tolerance=tolerance,
                evidence=stage_evidence,
            )
        )
        if position < len(definitions) - 1:
            model.lexicographic_locks.add(objective.expr <= objective_value + tolerance)

    return _extract_solution(
        recursive,
        stages,
        evidence,
        method_description=method_description,
    )


def solve_recursive_for_physical_plan(
    recursive: RecursiveModel,
    physical: BaselineSolution,
    *,
    solver: SolverAdapter | None = None,
    time_limit_seconds: float | None = None,
    maximum_stage: int = 3,
) -> RecursiveSolution:
    """Solve exact value equations for a supplied, fixed feasible physical plan."""

    if solver is None:
        solver = IpoptSolverAdapter()
    if time_limit_seconds is None:
        time_limit_seconds = recursive.data.config["runtime_budgets"][
            "miniature_fixture_seconds"
        ]
    physical = _normalise_physical_solution(recursive.data, physical)
    _fix_physical_decisions(recursive, physical)
    _initialize_values(recursive, physical)
    model = recursive.model
    stages: list[ObjectiveStageResult] = []
    evidence: list[SolverEvidence] = []
    if maximum_stage not in {1, 2, 3}:
        raise ValueError("maximum_stage must be 1, 2 or 3")
    definitions = (
        (1, "WEIGHTED_SHORTAGE", model.stage_1_objective, "quantity"),
        (2, "SERVED_AND_CLOSING_RECURSIVE_VALUE", model.stage_2_objective, "value"),
        (3, "SURPLUS_AND_UNNECESSARY_ACTIVATION", model.stage_3_objective, "quantity"),
    )[:maximum_stage]
    for position, (stage, name, objective, tolerance_kind) in enumerate(definitions):
        for candidate in (
            model.stage_1_objective,
            model.stage_2_objective,
            model.stage_3_objective,
        ):
            candidate.deactivate()
        objective.activate()
        stage_evidence = solver.solve(
            model,
            time_limit_seconds=time_limit_seconds / maximum_stage,
            options={"tol": 1e-9, "constr_viol_tol": 1e-8},
        )
        evidence.append(stage_evidence)
        if not stage_evidence.has_solution:
            raise RuntimeError(
                f"recursive solve failed at stage {stage}: "
                f"{stage_evidence.raw_termination_condition}: "
                f"{stage_evidence.termination_message}"
            )
        value = float(pyo.value(objective.expr))
        tolerance = _lock_tolerance(recursive.data, tolerance_kind, value)
        stages.append(
            ObjectiveStageResult(
                stage=stage,
                name=name,
                objective_value=value,
                lock_tolerance=tolerance,
                evidence=stage_evidence,
            )
        )
        if position < len(definitions) - 1:
            model.lexicographic_locks.add(objective.expr <= value + tolerance)

    return _extract_solution(
        recursive,
        stages,
        evidence,
        method_description=(
            "IPOPT solution of exact recursive value equations with an "
            "independently feasible physical plan fixed"
        ),
    )
