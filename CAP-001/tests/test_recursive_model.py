from __future__ import annotations

import inspect
import math
from pathlib import Path

import pyomo.environ as pyo
import pytest
from pyomo.repn import generate_standard_repn

from cap001_model.physical_seed import build_physical_seed_model, solve_physical_seed
from cap001_model.contracts import (
    FormulationClass,
    MethodClassification,
    SolutionStatus,
)
from cap001_model.data import load_model_data
from cap001_model.proof_cases import materialize_proof_case
from cap001_model.recursive import (
    build_recursive_model,
    solve_recursive,
    solve_recursive_for_physical_plan,
)
from cap001_model.recursive_validation import (
    validate_published_control_totals,
    validate_recursive_solution,
)
from cap001_model.validation import validate_physical_solution
from tooling.contract_runtime import ContractError


FIXTURE_ROOT = Path("miniature_fixture")
FIXTURE_INPUTS = FIXTURE_ROOT / "inputs"
PROOF_CASES = Path("solver_proof_cases")


def test_recursive_model_is_bounded_and_explicitly_minlp() -> None:
    data = load_model_data(FIXTURE_INPUTS)
    recursive = build_recursive_model(data)
    assert recursive.formulation_class is FormulationClass.MINLP
    recursive.bounds.assert_finite()
    assert len(recursive.bounds.pools) == 110
    assert max(bound.unit_cost_upper for bound in recursive.bounds.pools.values()) < 4_000_000
    assert all(bound.derivation for bound in recursive.bounds.pools.values())
    assert any(variable.is_binary() for variable in recursive.model.component_data_objects(pyo.Var))
    nonlinear = [
        constraint
        for constraint in recursive.model.component_data_objects(pyo.Constraint, active=True)
        if not generate_standard_repn(constraint.body).is_linear()
    ]
    assert len(nonlinear) >= 200
    import cap001_model.recursive as recursive_module

    assert "standard_cost" not in inspect.getsource(recursive_module)


def test_physical_seed_and_recursive_models_use_the_same_physical_constraints() -> None:
    data = load_model_data(FIXTURE_INPUTS)
    seed_model = build_physical_seed_model(data)
    recursive = build_recursive_model(data)
    seed_physical = {
        component.name
        for component in seed_model.model.component_objects(pyo.Constraint)
        if component.name != "lexicographic_locks"
    }
    assert seed_physical == set(recursive.physical_constraint_names)


def test_canonical_recursive_route_reproduces_all_published_control_totals() -> None:
    data = load_model_data(FIXTURE_INPUTS)
    physical = solve_physical_seed(build_physical_seed_model(data))
    assert validate_physical_solution(data, physical).passed
    recursive_model = build_recursive_model(data)
    solution = solve_recursive_for_physical_plan(recursive_model, physical)

    assert solution.status is SolutionStatus.LOCALLY_OPTIMAL
    assert solution.formulation_class is FormulationClass.MINLP
    assert solution.method_classification is MethodClassification.HEURISTIC
    assert [stage.evidence.status for stage in solution.stages] == [
        SolutionStatus.LOCALLY_OPTIMAL,
        SolutionStatus.LOCALLY_OPTIMAL,
        SolutionStatus.LOCALLY_OPTIMAL,
    ]
    assert all(stage.evidence.best_bound is None for stage in solution.stages)
    assert math.isclose(solution.stages[1].objective_value, 2239.3, abs_tol=1e-5)

    validation = validate_recursive_solution(data, solution)
    assert validation.passed, validation.violations
    assert validation.checked_equations > 450
    assert validation.max_residual < 1e-5
    assert max(
        abs(float(recursive_model.model.pool_value_conservation_residual[key]()))
        for key in data.pool_keys
    ) < 1e-5
    inactive_pools = [
        key
        for key, quantity in solution.pool_quantity.items()
        if quantity <= data.config["tolerances"]["quantity"]["absolute"]
    ]
    assert inactive_pools
    assert all(abs(solution.pool_value[key]) < 1e-7 for key in inactive_pools)
    assert all(abs(solution.unit_cost[key]) < 1e-7 for key in inactive_pools)

    failures = validate_published_control_totals(
        data,
        solution,
        definitions_path=FIXTURE_ROOT / "control_total_definitions.json",
        expected_path=FIXTURE_ROOT / "expected_reconciliation/fixture_control_totals.csv",
    )
    assert failures == ()


def test_missing_positive_pool_epsilon_fails_before_solve(tmp_path: Path) -> None:
    variant = tmp_path / "inputs"
    materialize_proof_case(
        PROOF_CASES / "SP-06-zero-pool-bounds.json", variant
    )
    with pytest.raises(ContractError, match="not above exclusive minimum"):
        build_recursive_model(load_model_data(variant))


def test_unrestricted_recursive_search_matches_the_canonical_result() -> None:
    data = load_model_data(FIXTURE_INPUTS)
    recursive_model = build_recursive_model(data)
    solution = solve_recursive(recursive_model)

    assert solution.status is SolutionStatus.LOCALLY_OPTIMAL
    assert solution.formulation_class is FormulationClass.MINLP
    assert solution.method_classification is MethodClassification.HEURISTIC
    assert "global optimality is not claimed" in solution.method_description
    assert [stage.evidence.raw_termination_condition for stage in solution.stages] == [
        "optimal",
        "optimal",
        "optimal",
    ]
    assert all(stage.evidence.best_bound is None for stage in solution.stages)
    assert math.isclose(solution.stages[1].objective_value, 2239.3, abs_tol=1e-5)

    physical_validation = validate_physical_solution(data, solution)
    assert physical_validation.passed, physical_validation.violations
    accounting_validation = validate_recursive_solution(data, solution)
    assert accounting_validation.passed, accounting_validation.violations
    assert accounting_validation.max_residual < 1e-5

    failures = validate_published_control_totals(
        data,
        solution,
        definitions_path=FIXTURE_ROOT / "control_total_definitions.json",
        expected_path=FIXTURE_ROOT
        / "expected_reconciliation/fixture_control_totals.csv",
    )
    assert failures == ()
