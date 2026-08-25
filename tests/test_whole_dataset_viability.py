from __future__ import annotations

from pathlib import Path

import pytest
from pyomo.repn import generate_standard_repn

from cap001_model.baseline import build_baseline_model, solve_baseline
from cap001_model.data import load_model_data
from tooling.assess_whole_dataset_viability import (
    DEFAULT_DATASET_DIR,
    DEFAULT_POLICY_PATH,
    FORBIDDEN_EVIDENCE_KEYS,
    apply_data_policy,
    apply_model_policy,
    data_participation,
    load_policy_matrix,
    verify_frozen_inputs,
)
from tooling.contract_runtime import ContractError, EXPECTED_RAW_FILES


FIXTURE_INPUTS = Path("capstones/CAP-001/miniature_fixture/inputs")


def test_audit_matrix_is_bounded_and_covers_every_capability() -> None:
    matrix = load_policy_matrix(DEFAULT_POLICY_PATH)
    policy_types = {policy["policy_type"] for policy in matrix["policies"]}
    assert policy_types == {
        "DEFAULT",
        "PARENT_SHARE_LIMIT",
        "EXPEDITED_ELIGIBILITY",
        "APPROVAL_SHARE_OVERRIDE",
        "SERVICE_WEIGHT_MULTIPLIER",
    }
    assert matrix["solver_budgets"]["milp_maximum_stage"] == 2
    assert matrix["solver_budgets"]["milp_service_seconds"] == 90
    assert matrix["solver_budgets"]["milp_economic_seconds"] == 30
    assert matrix["solver_budgets"]["recursive_maximum_stage"] == 2
    assert len(matrix["milp_runs"]) == 12
    assert len(matrix["recursive_runs"]) == 3


def test_frozen_package_hashes_and_data_participation_are_complete() -> None:
    assert len(verify_frozen_inputs(DEFAULT_DATASET_DIR)) == 6
    participation = data_participation()
    assert participation["status"] == "PASS"
    assert {record["file"] for record in participation["files"]} == set(
        EXPECTED_RAW_FILES
    )


def test_unauthorised_approval_exception_is_rejected_before_construction() -> None:
    matrix = load_policy_matrix(DEFAULT_POLICY_PATH)
    policy = next(
        item
        for item in matrix["policies"]
        if item["policy_id"] == "UNAUTHORISED_EXCEPTION_NEGATIVE"
    )
    data = load_model_data(DEFAULT_DATASET_DIR / "SCN-03" / "data")
    with pytest.raises(ContractError, match="lacks explicit authorisation"):
        apply_data_policy(data, policy)


def test_authorised_approval_exception_is_explicit_and_does_not_mutate_input() -> None:
    matrix = load_policy_matrix(DEFAULT_POLICY_PATH)
    policy = next(
        item
        for item in matrix["policies"]
        if item["policy_id"] == "APPROVAL_SHARE_EXCEPTION"
    )
    data = load_model_data(DEFAULT_DATASET_DIR / "SCN-03" / "data")
    effective, evidence = apply_data_policy(data, policy)
    original = {
        route.maximum_approved_share
        for route in data.shipment_routes.values()
        if route.approval_id == "APR-00119"
    }
    changed = {
        route.maximum_approved_share
        for route in effective.shipment_routes.values()
        if route.approval_id == "APR-00119"
    }
    assert original == {0.7}
    assert changed == {1.0}
    assert evidence["authority"] == "CAPSTONE_OWNER_WP7_AUDIT"


def test_parent_diversity_policy_adds_only_linear_constraints() -> None:
    matrix = load_policy_matrix(DEFAULT_POLICY_PATH)
    policy = next(
        item
        for item in matrix["policies"]
        if item["policy_id"] == "PARENT_DIVERSITY_58"
    )
    baseline = build_baseline_model(
        load_model_data(DEFAULT_DATASET_DIR / "BASE" / "data")
    )
    evidence = apply_model_policy(baseline, policy)
    assert evidence["additional_constraint_count"] > 0
    assert all(
        generate_standard_repn(constraint.body).is_linear()
        for constraint in baseline.model.audit_parent_share.values()
    )


def test_baseline_can_stop_after_the_economic_stage() -> None:
    baseline = build_baseline_model(load_model_data(FIXTURE_INPUTS))
    solution = solve_baseline(
        baseline,
        time_limit_seconds=120,
        maximum_stage=2,
    )
    assert solution.success
    assert [stage.stage for stage in solution.stages] == [1, 2]


def test_privacy_key_set_names_row_level_solution_families() -> None:
    assert FORBIDDEN_EVIDENCE_KEYS == {
        "orders",
        "shipments",
        "production",
        "closing_inventory",
        "source_supply",
        "served",
        "shortage",
        "pool_quantity",
        "pool_value",
        "unit_cost",
    }
