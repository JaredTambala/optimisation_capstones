"""Private physical-feasibility seed MILP and sequential solve controller.

This authoring helper is not a CAP-001 economic baseline or candidate
requirement. Its linear objective uses only locally supplied facts to obtain a
feasible integer plan that can be valued by the recursive formulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pyomo.environ as pyo

from cap001_model.contracts import (
    FormulationClass,
    MethodClassification,
    ObjectiveStageResult,
    SolutionStatus,
    SolverAdapter,
    SolverEvidence,
)
from cap001_model.data import DemandKey, ModelData, PoolKey, load_model_data
from cap001_model.physical import build_physical_model
from cap001_model.solvers import HighsSolverAdapter


@dataclass(frozen=True)
class PhysicalSeedModel:
    formulation_class: FormulationClass
    method_classification: MethodClassification
    data: ModelData
    model: pyo.ConcreteModel


@dataclass(frozen=True)
class PhysicalSeedSolution:
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

    @property
    def success(self) -> bool:
        return self.status in {
            SolutionStatus.GLOBALLY_OPTIMAL,
            SolutionStatus.LOCALLY_OPTIMAL,
            SolutionStatus.FEASIBLE_TIME_LIMITED,
            SolutionStatus.BEST_FOUND,
        }


def build_physical_seed_model(data: ModelData | None = None) -> PhysicalSeedModel:
    """Construct a private local-fact seed objective on the physical MILP."""

    if data is None:
        data = load_model_data()
    model = build_physical_model(data, name="CAP-001 authoring physical-seed MILP")
    route_ids = tuple(model.ROUTE)
    contract_ids = tuple(model.CONTRACT)
    source_keys = tuple(model.SOURCE)
    recipe_period_keys = tuple(model.RECIPE_PERIOD)
    demand_keys = tuple(model.DEMAND)
    routes_by_contract = {
        contract_id: tuple(
            route_id
            for route_id, route in data.shipment_routes.items()
            if route.contract_id == contract_id
        )
        for contract_id in contract_ids
    }

    stage_1_expression = sum(
        data.demand[key]["service_weight"] * model.shortage[key]
        for key in demand_keys
    )
    route_cost = sum(
        data.shipment_routes[route_id].freight_unit_eur
        * model.shipment_quantity[route_id]
        + (
            data.shipment_routes[route_id].fixed_order_cost_eur
            + data.shipment_routes[route_id].fixed_shipment_cost_eur
        )
        * model.shipment_active[route_id]
        for route_id in route_ids
    )
    activation_cost_by_contract = {
        contract_id: max(
            data.shipment_routes[route_id].horizon_activation_cost_eur
            for route_id in routes_by_contract[contract_id]
        )
        for contract_id in contract_ids
    }
    contract_cost = sum(
        activation_cost_by_contract[contract_id] * model.contract_active[contract_id]
        for contract_id in contract_ids
    )
    source_surge_cost = sum(
        data.source_capacity[key]["surge_unit_premium"] * model.source_surge[key]
        for key in source_keys
    )
    production_surge_cost = sum(
        data.transformation_capacity[key]["surge_conversion_premium"]
        * next(
            row["eur_per_currency_unit"]
            for row in data.rows("fx_rates.csv")
            if row["currency"] == data.conversion_costs[key]["currency"]
            and row["period_id"] == key[1]
        )
        * model.production_surge[key]
        for key in recipe_period_keys
    )
    holding_cost = sum(
        data.inventory_policy[(node, material)]["holding_cost_eur_per_unit_week"]
        * model.closing_inventory[node, material, period]
        for node, material, period in data.pool_keys
    )
    source_purchase_cost = sum(
        data.source_unit_prices[key] * model.source_supply[key]
        for key in source_keys
    )
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in data.rows("fx_rates.csv")
    }
    production_local_cost = sum(
        (
            data.conversion_costs[key]["variable_conversion_cost_per_output"]
            + data.conversion_costs[key]["eligible_overhead_variable"]
        )
        * fx[(data.conversion_costs[key]["currency"], key[1])]
        * model.production_quantity[key]
        + (
            data.conversion_costs[key]["fixed_setup_cost"]
            + data.conversion_costs[key]["eligible_overhead_fixed"]
        )
        * fx[(data.conversion_costs[key]["currency"], key[1])]
        * model.production_active[key]
        for key in recipe_period_keys
    )
    stage_2_expression = (
        source_purchase_cost
        + route_cost
        + contract_cost
        + production_local_cost
        + source_surge_cost
        + production_surge_cost
        + holding_cost
    )
    stage_3_expression = (
        sum(model.closing_inventory[key] for key in data.pool_keys)
        + sum(model.shipment_active[route_id] for route_id in route_ids)
        + sum(model.production_active[key] for key in recipe_period_keys)
        + sum(model.contract_active[contract_id] for contract_id in contract_ids)
    )
    model.stage_1_objective = pyo.Objective(
        expr=stage_1_expression, sense=pyo.minimize
    )
    model.stage_2_objective = pyo.Objective(
        expr=stage_2_expression, sense=pyo.minimize
    )
    model.stage_3_objective = pyo.Objective(
        expr=stage_3_expression, sense=pyo.minimize
    )
    model.stage_2_objective.deactivate()
    model.stage_3_objective.deactivate()
    model.lexicographic_locks = pyo.ConstraintList()
    return PhysicalSeedModel(
        formulation_class=FormulationClass.MILP,
        method_classification=MethodClassification.EXACT,
        data=data,
        model=model,
    )


def evaluate_physical_seed_proxy_cost(
    data: ModelData, solution: PhysicalSeedSolution
) -> float:
    """Evaluate the local-fact witness selector for an extracted physical plan."""

    route_cost = sum(
        data.shipment_routes[route_id].freight_unit_eur * quantity
        + (
            data.shipment_routes[route_id].fixed_order_cost_eur
            + data.shipment_routes[route_id].fixed_shipment_cost_eur
        )
        * solution.shipment_active[route_id]
        for route_id, quantity in solution.shipments.items()
    )
    activation_cost = sum(
        max(
            route.horizon_activation_cost_eur
            for route in data.shipment_routes.values()
            if route.contract_id == contract_id
        )
        * active
        for contract_id, active in solution.contract_active.items()
    )
    fx = {
        (row["currency"], row["period_id"]): row["eur_per_currency_unit"]
        for row in data.rows("fx_rates.csv")
    }
    production_cost = sum(
        (
            data.conversion_costs[key]["variable_conversion_cost_per_output"]
            + data.conversion_costs[key]["eligible_overhead_variable"]
        )
        * fx[(data.conversion_costs[key]["currency"], key[1])]
        * quantity
        + (
            data.conversion_costs[key]["fixed_setup_cost"]
            + data.conversion_costs[key]["eligible_overhead_fixed"]
        )
        * fx[(data.conversion_costs[key]["currency"], key[1])]
        * solution.production_active[key]
        for key, quantity in solution.production.items()
    )
    return (
        route_cost
        + activation_cost
        + production_cost
        + sum(
            data.source_capacity[key]["surge_unit_premium"] * quantity
            for key, quantity in solution.source_surge.items()
        )
        + sum(
            data.transformation_capacity[key]["surge_conversion_premium"]
            * fx[(data.conversion_costs[key]["currency"], key[1])]
            * quantity
            for key, quantity in solution.production_surge.items()
        )
        + sum(
            data.inventory_policy[(node, material)][
                "holding_cost_eur_per_unit_week"
            ]
            * quantity
            for (node, material, _), quantity in solution.closing_inventory.items()
        )
        + sum(
            data.source_unit_prices[key] * quantity
            for key, quantity in solution.source_supply.items()
        )
    )


def _lock_tolerance(data: ModelData, kind: str, value: float) -> float:
    policy = data.config["tolerances"][kind]
    return policy["absolute"] + policy.get("relative", 0.0) * abs(value)


def _empty_solution(
    status: SolutionStatus,
    stages: list[ObjectiveStageResult],
    evidence: list[SolverEvidence],
) -> PhysicalSeedSolution:
    return PhysicalSeedSolution(
        status=status,
        formulation_class=FormulationClass.MILP,
        method_classification=MethodClassification.EXACT,
        method_description="HiGHS branch-and-bound on the private physical-seed MILP",
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
    )


def solve_physical_seed(
    seed_model: PhysicalSeedModel,
    *,
    solver: SolverAdapter | None = None,
    time_limit_seconds: float | None = None,
    maximum_stage: int = 3,
    stage_time_limits: Mapping[int, float] | None = None,
    initial_stages: tuple[ObjectiveStageResult, ...] = (),
) -> PhysicalSeedSolution:
    """Solve the requested objective prefix and retain its stage locks."""

    if solver is None:
        solver = HighsSolverAdapter()
    if time_limit_seconds is None:
        time_limit_seconds = seed_model.data.config["runtime_budgets"][
            "reference_benchmark_reproduction_seconds"
        ]
    model = seed_model.model
    stages = list(initial_stages)
    evidence = [stage.evidence for stage in initial_stages]
    if maximum_stage not in {1, 2, 3}:
        raise ValueError("maximum_stage must be 1, 2 or 3")
    completed = tuple(stage.stage for stage in initial_stages)
    if completed != tuple(range(1, len(completed) + 1)):
        raise ValueError("initial stages must be a contiguous prefix starting at stage 1")
    if completed and completed[-1] > maximum_stage:
        raise ValueError("initial stages cannot exceed maximum_stage")
    definitions = tuple(
        definition
        for definition in (
            (1, "WEIGHTED_SHORTAGE", model.stage_1_objective, "quantity"),
            (2, "LOCAL_FACT_SEED_COST", model.stage_2_objective, "value"),
            (
                3,
                "SURPLUS_AND_UNNECESSARY_ACTIVATION",
                model.stage_3_objective,
                "quantity",
            ),
        )[:maximum_stage]
        if definition[0] not in completed
    )
    if stage_time_limits is None:
        stage_limits = {
            stage: time_limit_seconds / max(1, len(definitions))
            for stage, _, _, _ in definitions
        }
    else:
        stage_limits = {
            stage: float(stage_time_limits[stage]) for stage, _, _, _ in definitions
        }
        if any(value <= 0 for value in stage_limits.values()):
            raise ValueError("stage time limits must be positive")

    for stage, name, objective, tolerance_kind in definitions:
        for candidate in (
            model.stage_1_objective,
            model.stage_2_objective,
            model.stage_3_objective,
        ):
            candidate.deactivate()
        objective.activate()
        stage_evidence = solver.solve(
            model,
            time_limit_seconds=stage_limits[stage],
            options={"mip_rel_gap": 0.0},
        )
        evidence.append(stage_evidence)
        if not stage_evidence.has_solution:
            return _empty_solution(stage_evidence.status, stages, evidence)
        objective_value = float(pyo.value(objective.expr))
        tolerance = _lock_tolerance(seed_model.data, tolerance_kind, objective_value)
        stages.append(
            ObjectiveStageResult(
                stage=stage,
                name=name,
                objective_value=objective_value,
                lock_tolerance=tolerance,
                evidence=stage_evidence,
            )
        )
        if stage < maximum_stage:
            model.lexicographic_locks.add(objective.expr <= objective_value + tolerance)

    return PhysicalSeedSolution(
        status=evidence[-1].status,
        formulation_class=FormulationClass.MILP,
        method_classification=MethodClassification.EXACT,
        method_description="HiGHS branch-and-bound on the private physical-seed MILP",
        stages=tuple(stages),
        solver_evidence=tuple(evidence),
        source_supply={
            key: float(pyo.value(model.source_supply[key]))
            for key in seed_model.data.source_capacity
        },
        source_regular={
            key: float(pyo.value(model.source_regular[key]))
            for key in seed_model.data.source_capacity
        },
        source_surge={
            key: float(pyo.value(model.source_surge[key]))
            for key in seed_model.data.source_capacity
        },
        shipments={
            route_id: float(pyo.value(model.shipment_quantity[route_id]))
            for route_id in seed_model.data.shipment_routes
        },
        shipment_active={
            route_id: float(pyo.value(model.shipment_active[route_id]))
            for route_id in seed_model.data.shipment_routes
        },
        shipment_lots={
            route_id: float(pyo.value(model.shipment_lots[route_id]))
            for route_id in seed_model.data.shipment_routes
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
            for key in seed_model.data.pool_keys
        },
        served={
            key: float(pyo.value(model.served[key])) for key in seed_model.data.demand
        },
        shortage={
            key: float(pyo.value(model.shortage[key]))
            for key in seed_model.data.demand
        },
    )
