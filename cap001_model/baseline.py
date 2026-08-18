"""Fixture-scale fixed-price MILP and sequential solve controller."""

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
class BaselineModel:
    formulation_class: FormulationClass
    method_classification: MethodClassification
    data: ModelData
    model: pyo.ConcreteModel


@dataclass(frozen=True)
class BaselineSolution:
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


def build_baseline_model(data: ModelData | None = None) -> BaselineModel:
    """Construct fixed-price economics on the shared physical MILP."""

    if data is None:
        data = load_model_data()
    model = build_physical_model(data, name="CAP-001 fixed-price baseline MILP")
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
        data.shipment_routes[route_id].variable_baseline_cost_eur
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
        * model.production_surge[key]
        for key in recipe_period_keys
    )
    holding_cost = sum(
        data.inventory_policy[(node, material)]["holding_cost_eur_per_unit_week"]
        * model.closing_inventory[node, material, period]
        for node, material, period in data.pool_keys
    )
    stage_2_expression = (
        route_cost
        + contract_cost
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
    return BaselineModel(
        formulation_class=FormulationClass.MILP,
        method_classification=MethodClassification.EXACT,
        data=data,
        model=model,
    )


def _lock_tolerance(data: ModelData, kind: str, value: float) -> float:
    policy = data.config["tolerances"][kind]
    return policy["absolute"] + policy.get("relative", 0.0) * abs(value)


def _empty_solution(
    status: SolutionStatus,
    stages: list[ObjectiveStageResult],
    evidence: list[SolverEvidence],
) -> BaselineSolution:
    return BaselineSolution(
        status=status,
        formulation_class=FormulationClass.MILP,
        method_classification=MethodClassification.EXACT,
        method_description="HiGHS branch-and-bound on the fixed-price MILP",
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


def solve_baseline(
    baseline: BaselineModel,
    *,
    solver: SolverAdapter | None = None,
    time_limit_seconds: float | None = None,
) -> BaselineSolution:
    """Solve all three objectives sequentially and retain the stage locks."""

    if solver is None:
        solver = HighsSolverAdapter()
    if time_limit_seconds is None:
        time_limit_seconds = baseline.data.config["runtime_budgets"][
            "miniature_fixture_seconds"
        ]
    model = baseline.model
    stages: list[ObjectiveStageResult] = []
    evidence: list[SolverEvidence] = []
    definitions = (
        (1, "WEIGHTED_SHORTAGE", model.stage_1_objective, "quantity"),
        (2, "FIXED_PRICE_OPERATIONAL_COST", model.stage_2_objective, "value"),
        (3, "SURPLUS_AND_UNNECESSARY_ACTIVATION", model.stage_3_objective, "quantity"),
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
            options={"mip_rel_gap": 0.0},
        )
        evidence.append(stage_evidence)
        if not stage_evidence.has_solution:
            return _empty_solution(stage_evidence.status, stages, evidence)
        objective_value = float(pyo.value(objective.expr))
        tolerance = _lock_tolerance(baseline.data, tolerance_kind, objective_value)
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

    return BaselineSolution(
        status=evidence[-1].status,
        formulation_class=FormulationClass.MILP,
        method_classification=MethodClassification.EXACT,
        method_description="HiGHS branch-and-bound on the fixed-price MILP",
        stages=tuple(stages),
        solver_evidence=tuple(evidence),
        source_supply={
            key: float(pyo.value(model.source_supply[key]))
            for key in baseline.data.source_capacity
        },
        source_regular={
            key: float(pyo.value(model.source_regular[key]))
            for key in baseline.data.source_capacity
        },
        source_surge={
            key: float(pyo.value(model.source_surge[key]))
            for key in baseline.data.source_capacity
        },
        shipments={
            route_id: float(pyo.value(model.shipment_quantity[route_id]))
            for route_id in baseline.data.shipment_routes
        },
        shipment_active={
            route_id: float(pyo.value(model.shipment_active[route_id]))
            for route_id in baseline.data.shipment_routes
        },
        shipment_lots={
            route_id: float(pyo.value(model.shipment_lots[route_id]))
            for route_id in baseline.data.shipment_routes
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
            for key in baseline.data.pool_keys
        },
        served={
            key: float(pyo.value(model.served[key])) for key in baseline.data.demand
        },
        shortage={
            key: float(pyo.value(model.shortage[key]))
            for key in baseline.data.demand
        },
    )
