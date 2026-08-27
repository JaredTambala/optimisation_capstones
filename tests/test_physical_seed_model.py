from __future__ import annotations

import csv
import inspect
import json
from pathlib import Path

import pyomo.environ as pyo
import pytest
from pyomo.repn import generate_standard_repn

from cap001_model.physical_seed import (
    build_physical_seed_model,
    evaluate_physical_seed_proxy_cost,
    solve_physical_seed,
)
from cap001_model.contracts import (
    FormulationClass,
    MethodClassification,
    SolutionStatus,
)
from cap001_model.data import load_model_data
from cap001_model.proof_cases import load_proof_case, materialize_proof_case
from cap001_model.validation import validate_physical_solution


FIXTURE_INPUTS = Path("capstones/CAP-001/miniature_fixture/inputs")
REFERENCE_SOLUTION = Path("capstones/CAP-001/miniature_fixture/reference_solution")
PROOF_CASES = Path("capstones/CAP-001/solver_proof_cases")


def _csv_quantities(path: Path, id_column: str, quantity_column: str) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            row[id_column]: float(row[quantity_column]) for row in csv.DictReader(handle)
        }


def test_model_loader_reads_all_raw_contracts_without_using_reconciler() -> None:
    data = load_model_data(FIXTURE_INPUTS)
    assert len(data.tables) == 25
    assert len(data.pool_keys) == 110
    assert len(data.shipment_routes) == 15
    import cap001_model.physical_seed as physical_seed_module
    import cap001_model.data as data_module

    source = inspect.getsource(physical_seed_module) + inspect.getsource(data_module)
    assert "fixture_reconciler" not in source
    assert "value_plan" not in source


def test_private_physical_seed_is_an_explicit_milp() -> None:
    seed_model = build_physical_seed_model(load_model_data(FIXTURE_INPUTS))
    model = seed_model.model
    assert seed_model.formulation_class is FormulationClass.MILP
    assert model.nvariables() > 300
    assert model.nconstraints() > 350
    assert any(variable.is_binary() for variable in model.component_data_objects(pyo.Var))
    assert any(variable.is_integer() for variable in model.component_data_objects(pyo.Var))
    for constraint in model.component_data_objects(pyo.Constraint, active=True):
        assert generate_standard_repn(constraint.body).is_linear(), constraint.name
    for objective in model.component_data_objects(pyo.Objective):
        assert generate_standard_repn(objective.expr).is_linear(), objective.name


def test_canonical_physical_seed_solves_and_matches_published_physical_plan() -> None:
    data = load_model_data(FIXTURE_INPUTS)
    solution = solve_physical_seed(build_physical_seed_model(data))
    assert solution.status is SolutionStatus.GLOBALLY_OPTIMAL
    assert solution.formulation_class is FormulationClass.MILP
    assert solution.method_classification is MethodClassification.EXACT
    assert [stage.objective_value for stage in solution.stages][0] == 0.0
    assert all(stage.evidence.absolute_gap == 0.0 for stage in solution.stages)
    assert evaluate_physical_seed_proxy_cost(data, solution) == pytest.approx(
        solution.stages[1].objective_value
    )

    expected_shipments = _csv_quantities(
        REFERENCE_SOLUTION / "shipments.csv", "lane_id", "quantity_units"
    )
    actual_shipments = {
        data.shipment_routes[route_id].lane_id: quantity
        for route_id, quantity in solution.shipments.items()
    }
    assert actual_shipments == expected_shipments

    expected_production = _csv_quantities(
        REFERENCE_SOLUTION / "production.csv", "recipe_id", "output_quantity_units"
    )
    actual_production = {
        recipe_id: quantity
        for (recipe_id, _), quantity in solution.production.items()
        if quantity > 1e-7
    }
    assert actual_production == expected_production

    with (REFERENCE_SOLUTION / "demand_service.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        expected_service = {
            (row["plant_id"], row["material_id"], row["period_id"]): float(
                row["served_quantity_units"]
            )
            for row in csv.DictReader(handle)
        }
    assert solution.served == expected_service

    validation = validate_physical_solution(data, solution)
    assert validation.passed
    assert validation.checked_equations > 250
    assert validation.max_residual < 1e-7


def test_shortage_variant_preserves_the_lexicographic_service_optimum(
    tmp_path: Path,
) -> None:
    variant = tmp_path / "inputs"
    materialize_proof_case(PROOF_CASES / "SP-04-shortage.json", variant)
    data = load_model_data(variant)
    solution = solve_physical_seed(build_physical_seed_model(data))
    assert solution.status is SolutionStatus.GLOBALLY_OPTIMAL
    assert len(solution.stages) == 3
    assert abs(solution.stages[0].objective_value - 22.5) < 1e-7
    assert abs(sum(solution.shortage.values()) - 15.0) < 1e-7
    weighted_shortage = sum(
        data.demand[key]["service_weight"] * quantity
        for key, quantity in solution.shortage.items()
    )
    assert weighted_shortage <= (
        solution.stages[0].objective_value + solution.stages[0].lock_tolerance
    )
    assert validate_physical_solution(data, solution).passed


def test_infeasible_variant_returns_controlled_solver_evidence(tmp_path: Path) -> None:
    variant = tmp_path / "inputs"
    materialize_proof_case(PROOF_CASES / "SP-07-infeasible.json", variant)
    solution = solve_physical_seed(build_physical_seed_model(load_model_data(variant)))
    assert solution.status is SolutionStatus.INFEASIBLE
    assert not solution.success
    assert solution.stages == ()
    assert solution.shipments == {}
    assert solution.solver_evidence[-1].raw_termination_condition == "infeasible"


def test_sourcing_variant_selects_the_cheapest_enumerated_allocation(
    tmp_path: Path,
) -> None:
    manifest_path = PROOF_CASES / "SP-03-sourcing.json"
    manifest = load_proof_case(manifest_path)
    variant = tmp_path / "inputs"
    materialize_proof_case(manifest_path, variant)
    data = load_model_data(variant)

    selected = solve_physical_seed(build_physical_seed_model(data))
    assert selected.status is SolutionStatus.GLOBALLY_OPTIMAL
    route_by_lane = {
        route.lane_id: route_id for route_id, route in data.shipment_routes.items()
    }
    decision_route = route_by_lane["LANE-00003"]
    alternate_route = route_by_lane["LANE-00005"]
    node_0003_to_node_0007 = route_by_lane["LANE-00006"]
    assert selected.shipments[decision_route] == manifest["expected_selected_quantity"]
    assert selected.shipments[alternate_route] == 0.0
    assert selected.shipments[node_0003_to_node_0007] == 40.0
    assert validate_physical_solution(data, selected).passed

    enumerated_costs: dict[float, float] = {}
    for quantity in manifest["enumerated_node_0002_to_node_0006_quantities"]:
        candidate_model = build_physical_seed_model(data)
        candidate_model.model.enumerated_allocation = pyo.Constraint(
            expr=candidate_model.model.shipment_quantity[decision_route] == quantity
        )
        candidate = solve_physical_seed(candidate_model)
        assert candidate.status is SolutionStatus.GLOBALLY_OPTIMAL
        assert validate_physical_solution(data, candidate).passed
        enumerated_costs[quantity] = candidate.stages[1].objective_value
    assert min(enumerated_costs, key=enumerated_costs.get) == manifest[
        "expected_selected_quantity"
    ]
    assert selected.stages[1].objective_value == min(enumerated_costs.values())


def test_implemented_solver_proof_manifests_are_well_formed() -> None:
    manifests = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in PROOF_CASES.glob("SP-*.json")
    }
    assert set(manifests) == {
        "SP-01-canonical.json",
        "SP-03-sourcing.json",
        "SP-04-shortage.json",
        "SP-06-zero-pool-bounds.json",
        "SP-07-infeasible.json",
    }
    assert {manifest["proof_case_id"] for manifest in manifests.values()} == {
        "SP-01",
        "SP-03",
        "SP-04",
        "SP-06",
        "SP-07",
    }
