#!/usr/bin/env python3
"""Run the bounded whole-dataset viability audit and retain aggregate evidence."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

import pyomo.environ as pyo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap001_model.physical_seed import (  # noqa: E402
    PhysicalSeedModel,
    PhysicalSeedSolution,
    build_physical_seed_model,
    evaluate_physical_seed_proxy_cost,
    solve_physical_seed,
)
from cap001_model.bounds import derive_recursive_bounds  # noqa: E402
from cap001_model.contracts import (  # noqa: E402
    MethodClassification,
    ObjectiveStageResult,
    SolutionStatus,
    SolverEvidence,
)
from cap001_model.data import ModelData, ShipmentRoute, load_model_data  # noqa: E402
from cap001_model.recursive import (  # noqa: E402
    build_recursive_model,
    solve_recursive_for_physical_plan,
)
from cap001_model.recursive_validation import (  # noqa: E402
    evaluate_control_selector,
    validate_recursive_solution,
)
from cap001_model.solvers import HighsSolverAdapter  # noqa: E402
from cap001_model.validation import validate_physical_solution  # noqa: E402
from tooling.contract_runtime import (  # noqa: E402
    EXPECTED_RAW_FILES,
    ContractError,
    canonical_json,
    sha256_bytes,
    sha256_path,
)


DATASET_IDS = ("BASE", "SCN-01", "SCN-02", "SCN-03", "SCN-04", "SCN-05")
FROZEN_DATASET_HASHES = {
    "BASE": "a298c1b63350cc2213c9bf06d437bba4b60919cb90fad3bd4a864570790339a0",
    "SCN-01": "1325b03d3b75535b5f85fc7b95201e47c5b7664d903237b62023bfbe5b34823d",
    "SCN-02": "ee6e5c49d88686ed140d5b91bbf1f31c23ad03ac24e01a13252fb6e885ab9cc6",
    "SCN-03": "74137fb78c7a8c2a759062081f46ceeedb52ea0221e9c758f2f8f255483bf820",
    "SCN-04": "55a7af1cc0f103f19481301184b4298cf21cbc89441f2a1b197697923918d676",
    "SCN-05": "d65af5568ba0a40b1f63eab1616470c2952d718a90e1c8e7548265149b2d80f6",
}
DEFAULT_DATASET_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "datasets"
DEFAULT_POLICY_PATH = ROOT / "capstones" / "CAP-001" / "viability_audit_policy_matrix.json"
DEFAULT_OUTPUT_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "viability"
EVIDENCE_FILES = (
    "bound_summary.json",
    "data_participation.json",
    "milp_case_summary.json",
    "recursive_case_summary.json",
    "viability_scorecard.json",
    "WHOLE_DATASET_VIABILITY_REPORT.md",
)
FORBIDDEN_EVIDENCE_KEYS = {
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


@dataclass(frozen=True)
class CaseResult:
    dataset_id: str
    policy_id: str
    policy_hash: str
    model_variables: int
    model_constraints: int
    policy_application: Mapping[str, Any]
    solution: PhysicalSeedSolution
    raw_metrics: Mapping[str, Any]
    retained_record: Mapping[str, Any]


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def load_policy_matrix(path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    policies = matrix.get("policies", [])
    policy_ids = [policy.get("policy_id") for policy in policies]
    if len(policy_ids) != len(set(policy_ids)) or None in policy_ids:
        raise ContractError("policy matrix contains duplicate or missing policy identifiers")
    known = set(policy_ids)
    for run_family in ("milp_runs", "recursive_runs"):
        for run in matrix.get(run_family, []):
            if run.get("dataset_id") not in DATASET_IDS:
                raise ContractError(f"unknown dataset in {run_family}: {run}")
            if run.get("policy_id") not in known:
                raise ContractError(f"unknown policy in {run_family}: {run}")
    budgets = matrix.get("solver_budgets", {})
    if budgets.get("milp_maximum_stage") != 2:
        raise ContractError("viability MILP runs must retain service and economic stages")
    if any(float(value) <= 0 for key, value in budgets.items() if key.endswith("seconds")):
        raise ContractError("solver budgets must be positive")
    return matrix


def _policy_map(matrix: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {policy["policy_id"]: policy for policy in matrix["policies"]}


def _dataset_manifest(dataset_dir: Path, dataset_id: str) -> dict[str, Any]:
    path = dataset_dir / dataset_id / "dataset_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_frozen_inputs(dataset_dir: Path) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for dataset_id in DATASET_IDS:
        package = dataset_dir / dataset_id
        manifest = _dataset_manifest(dataset_dir, dataset_id)
        file_hashes = {
            name: sha256_path(package / "data" / name) for name in EXPECTED_RAW_FILES
        }
        aggregate = sha256_bytes(
            json.dumps(file_hashes, sort_keys=True, separators=(",", ":")).encode()
        )
        expected = FROZEN_DATASET_HASHES[dataset_id]
        if aggregate != expected or manifest.get("dataset_sha256") != expected:
            raise ContractError(
                f"{dataset_id} does not match frozen hash {expected}: {aggregate}"
            )
        records[dataset_id] = {
            "dataset_sha256": aggregate,
            "raw_file_count": len(file_hashes),
            "manifest_identity": manifest.get("dataset_id") == dataset_id
            and manifest.get("source_package_id") == dataset_id
            and manifest.get("package_semantics") == "COMPLETE_DATASET",
        }
    return records


def _ultimate_parent_by_node(data: ModelData) -> dict[str, str]:
    organisations = {
        row["supplier_id"]: row for row in data.rows("supplier_organisations.csv")
    }

    def ultimate_parent(supplier_id: str) -> str:
        visited: set[str] = set()
        current = supplier_id
        while organisations[current]["parent_group_id"] is not None:
            if current in visited:
                raise ContractError("supplier parent hierarchy contains a cycle")
            visited.add(current)
            current = organisations[current]["parent_group_id"]
        return current

    return {
        node_id: ultimate_parent(row["supplier_id"])
        for node_id, row in data.nodes.items()
        if row["supplier_id"] is not None
    }


def apply_data_policy(
    data: ModelData, policy: Mapping[str, Any]
) -> tuple[ModelData, dict[str, Any]]:
    policy_type = policy["policy_type"]
    if policy_type != "APPROVAL_SHARE_OVERRIDE":
        return data, {"data_override_count": 0}
    if not policy.get("authorised") or not str(policy.get("authority", "")).strip():
        raise ContractError("approval-share override lacks explicit authorisation")
    approval_id = policy["approval_id"]
    original = float(policy["original_maximum_share"])
    effective = float(policy["effective_maximum_share"])
    if not 0 < effective <= 1:
        raise ContractError("effective approval share must be in (0, 1]")
    changed: dict[str, ShipmentRoute] = {}
    for route_id, route in data.shipment_routes.items():
        if route.approval_id != approval_id:
            changed[route_id] = route
            continue
        if route.maximum_approved_share is None or not math.isclose(
            route.maximum_approved_share, original, abs_tol=1e-12
        ):
            raise ContractError(
                f"approval {approval_id} original share does not match {original}"
            )
        changed[route_id] = replace(route, maximum_approved_share=effective)
    changed_count = sum(
        route.approval_id == approval_id for route in data.shipment_routes.values()
    )
    if changed_count == 0:
        raise ContractError(f"approval override target {approval_id} is not active")
    return replace(data, shipment_routes=changed), {
        "data_override_count": changed_count,
        "target_type": "APPROVAL_MAXIMUM_SHARE",
        "target_id": approval_id,
        "original_value": original,
        "effective_value": effective,
        "authority": policy["authority"],
        "reason": policy["reason"],
    }


def apply_model_policy(
    seed_model: PhysicalSeedModel, policy: Mapping[str, Any]
) -> dict[str, Any]:
    data = seed_model.data
    model = seed_model.model
    policy_type = policy["policy_type"]
    if policy_type in {"DEFAULT", "APPROVAL_SHARE_OVERRIDE"}:
        return {"additional_constraint_count": 0, "objective_modified": False}
    if policy_type == "EXPEDITED_ELIGIBILITY":
        if policy.get("expedited_enabled") is not False:
            raise ContractError("only the explicit expedited-disabled probe is supported")
        expedited_lanes = {
            row["lane_id"]
            for row in data.rows("shipping_lanes.csv")
            if row["expedited_flag"]
        }
        model.audit_expedited_eligibility = pyo.ConstraintList()
        for route_id, route in data.shipment_routes.items():
            if route.lane_id in expedited_lanes:
                model.audit_expedited_eligibility.add(
                    model.shipment_quantity[route_id] == 0
                )
        return {
            "additional_constraint_count": len(model.audit_expedited_eligibility),
            "objective_modified": False,
            "rule": "EXPEDITED_DISABLED",
        }
    if policy_type == "SERVICE_WEIGHT_MULTIPLIER":
        priority = policy["priority_class"]
        multiplier = float(policy["multiplier"])
        if multiplier <= 0:
            raise ContractError("service-weight multiplier must be positive")
        model.stage_1_objective.set_value(
            sum(
                data.demand[key]["service_weight"]
                * (multiplier if data.demand[key]["priority_class"] == priority else 1)
                * model.shortage[key]
                for key in model.DEMAND
            )
        )
        return {
            "additional_constraint_count": 0,
            "objective_modified": True,
            "priority_class": priority,
            "multiplier": multiplier,
        }
    if policy_type == "PARENT_SHARE_LIMIT":
        maximum_share = float(policy["maximum_share"])
        if not 0.5 <= maximum_share < 1:
            raise ContractError("parent share limit must be in [0.5, 1)")
        parent_by_node = _ultimate_parent_by_node(data)
        grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
        for route_id, route in data.shipment_routes.items():
            grouped[(route.destination_node_id, route.material_id)].append(route_id)
        model.audit_parent_share = pyo.ConstraintList()
        choice_groups = 0
        for route_ids in grouped.values():
            parents = {
                parent_by_node[data.shipment_routes[route_id].origin_node_id]
                for route_id in route_ids
            }
            if len(parents) < 2:
                continue
            choice_groups += 1
            total = sum(model.shipment_quantity[route_id] for route_id in route_ids)
            for parent_id in sorted(parents):
                parent_total = sum(
                    model.shipment_quantity[route_id]
                    for route_id in route_ids
                    if parent_by_node[
                        data.shipment_routes[route_id].origin_node_id
                    ]
                    == parent_id
                )
                model.audit_parent_share.add(parent_total <= maximum_share * total)
        if choice_groups == 0:
            raise ContractError("parent share policy found no multi-parent choice group")
        return {
            "additional_constraint_count": len(model.audit_parent_share),
            "objective_modified": False,
            "choice_group_count": choice_groups,
            "maximum_share": maximum_share,
        }
    raise ContractError(f"unsupported viability policy type {policy_type}")


def _solver_record(stage: Any) -> dict[str, Any]:
    evidence = stage.evidence
    return {
        "stage": stage.stage,
        "name": stage.name,
        "status": evidence.status.value,
        "solver": evidence.solver_name,
        "solver_version": evidence.solver_version,
        "termination": evidence.raw_termination_condition,
        "runtime_seconds": round(evidence.runtime_seconds, 3),
        "relative_gap": (
            round(evidence.relative_gap, 6)
            if evidence.relative_gap is not None
            else None
        ),
    }


def _value_band(value: float, width: float = 10_000.0) -> dict[str, float]:
    lower = math.floor(value / width) * width
    return {"lower": lower, "upper": lower + width, "width": width}


def _relative_change(left: float, right: float) -> float:
    return abs(right - left) / max(1.0, abs(left))


def _actual_max_parent_share(
    data: ModelData, solution: PhysicalSeedSolution
) -> float:
    parent_by_node = _ultimate_parent_by_node(data)
    eligible: dict[tuple[str, str], set[str]] = defaultdict(set)
    quantities: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for route_id, route in data.shipment_routes.items():
        group = (route.destination_node_id, route.material_id)
        parent = parent_by_node[route.origin_node_id]
        eligible[group].add(parent)
        quantities[group][parent] += solution.shipments[route_id]
    shares: list[float] = []
    for group, parents in eligible.items():
        if len(parents) < 2:
            continue
        total = sum(quantities[group].values())
        if total > 1e-7:
            shares.extend(value / total for value in quantities[group].values())
    return max(shares, default=0.0)


def _approval_share(
    data: ModelData, solution: PhysicalSeedSolution, approval_id: str
) -> float:
    target_routes = [
        route
        for route in data.shipment_routes.values()
        if route.approval_id == approval_id
    ]
    if not target_routes:
        return 0.0
    target = sum(solution.shipments[route.route_id] for route in target_routes)
    receiving = sum(
        solution.shipments[route.route_id]
        for route in data.shipment_routes.values()
        if route.destination_node_id == target_routes[0].destination_node_id
        and route.material_id == target_routes[0].material_id
    )
    return target / receiving if receiving > 1e-7 else 0.0


def _raw_metrics(data: ModelData, solution: PhysicalSeedSolution) -> dict[str, Any]:
    lanes = {row["lane_id"]: row for row in data.rows("shipping_lanes.csv")}
    mode_quantity: dict[str, float] = defaultdict(float)
    expedited = 0.0
    affected_corridors = {"LANE-00081", "LANE-00093", "LANE-00094", "LANE-00095", "LANE-00096"}
    affected_corridor_quantity = 0.0
    for route_id, route in data.shipment_routes.items():
        quantity = solution.shipments[route_id]
        lane = lanes[route.lane_id]
        mode_quantity[lane["transport_mode"]] += quantity
        if lane["expedited_flag"]:
            expedited += quantity
        if route.lane_id in affected_corridors:
            affected_corridor_quantity += quantity
    priority_shortage: dict[str, float] = defaultdict(float)
    priority_served: dict[str, float] = defaultdict(float)
    for key, row in data.demand.items():
        priority_shortage[row["priority_class"]] += solution.shortage[key]
        priority_served[row["priority_class"]] += solution.served[key]
    affected_nodes = {"NODE-0002", "NODE-0005", "NODE-0015", "NODE-0024", "NODE-0027"}
    regional_activity = sum(
        value for (node, _, _), value in solution.source_supply.items() if node in affected_nodes
    ) + sum(
        value
        for (recipe_id, _), value in solution.production.items()
        if data.recipes[recipe_id]["node_id"] in affected_nodes
    )
    return {
        "weighted_shortage": max(0.0, solution.stages[0].objective_value),
        "unweighted_shortage": max(0.0, sum(solution.shortage.values())),
        "physical_seed_proxy_cost": evaluate_physical_seed_proxy_cost(data, solution),
        "total_inventory": sum(solution.closing_inventory.values()),
        "total_shipments": sum(solution.shipments.values()),
        "total_production": sum(solution.production.values()),
        "total_source": sum(solution.source_supply.values()),
        "total_surge": sum(solution.source_surge.values())
        + sum(solution.production_surge.values()),
        "expedited_quantity": expedited,
        "mode_quantity": dict(mode_quantity),
        "max_parent_share": _actual_max_parent_share(data, solution),
        "target_approval_share": _approval_share(data, solution, "APR-00119"),
        "priority_shortage": dict(priority_shortage),
        "priority_served": dict(priority_served),
        "source_node_0005_quantity": sum(
            value
            for (node, _, _), value in solution.source_supply.items()
            if node == "NODE-0005"
        ),
        "affected_corridor_quantity": affected_corridor_quantity,
        "node_0030_production": sum(
            value
            for (recipe_id, _), value in solution.production.items()
            if data.recipes[recipe_id]["node_id"] == "NODE-0030"
        ),
        "regional_affected_node_activity": regional_activity,
    }


def _retained_metrics(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "weighted_shortage": round(raw["weighted_shortage"], 3),
        "unweighted_shortage": round(raw["unweighted_shortage"], 3),
        "physical_seed_proxy_cost_band_eur": _value_band(
            raw["physical_seed_proxy_cost"]
        ),
        "total_inventory": round(raw["total_inventory"], 1),
        "total_shipment_quantity": round(raw["total_shipments"], 1),
        "total_production_quantity": round(raw["total_production"], 1),
        "total_source_quantity": round(raw["total_source"], 1),
        "total_surge_quantity": round(raw["total_surge"], 1),
        "expedited_quantity": round(raw["expedited_quantity"], 1),
        "transport_mode_quantity": {
            key: round(value, 1) for key, value in sorted(raw["mode_quantity"].items())
        },
        "maximum_parent_share": round(raw["max_parent_share"], 4),
        "target_approval_share": round(raw["target_approval_share"], 4),
        "shortage_by_priority": {
            key: round(value, 3)
            for key, value in sorted(raw["priority_shortage"].items())
        },
        "served_by_priority": {
            key: round(value, 1)
            for key, value in sorted(raw["priority_served"].items())
        },
        "scenario_indicators": {
            "source_node_0005_quantity": round(raw["source_node_0005_quantity"], 1),
            "affected_corridor_quantity": round(raw["affected_corridor_quantity"], 1),
            "node_0030_production": round(raw["node_0030_production"], 1),
            "regional_affected_node_activity": round(
                raw["regional_affected_node_activity"], 1
            ),
        },
    }


def run_milp_case(
    dataset_dir: Path,
    dataset_id: str,
    policy: Mapping[str, Any],
    *,
    service_seconds: float,
    economic_seconds: float,
    maximum_stage: int,
) -> CaseResult:
    data = load_model_data(dataset_dir / dataset_id / "data")
    effective_data, data_application = apply_data_policy(data, policy)
    seed_model = build_physical_seed_model(effective_data)
    model_application = apply_model_policy(seed_model, policy)
    if policy["policy_type"] == "DEFAULT":
        model = seed_model.model
        for objective in model.component_objects(pyo.Objective, active=True):
            objective.deactivate()
        quantity_tolerance = effective_data.config["tolerances"]["quantity"]
        zero_tolerance = float(quantity_tolerance["absolute"])
        model.audit_zero_shortage = pyo.Constraint(
            expr=sum(model.shortage[key] for key in model.DEMAND) <= zero_tolerance
        )
        model.audit_feasibility_objective = pyo.Objective(expr=0.0)
        service_evidence = HighsSolverAdapter().solve(
            model,
            time_limit_seconds=service_seconds,
            options={"mip_rel_gap": 0.0, "time_limit": service_seconds},
        )
        model.audit_feasibility_objective.deactivate()
        if service_evidence.has_solution:
            service_value = float(pyo.value(model.stage_1_objective.expr))
            service_lock = zero_tolerance + float(
                quantity_tolerance.get("relative", 0.0)
            ) * abs(service_value)
            initial_stage = ObjectiveStageResult(
                stage=1,
                name="WEIGHTED_SHORTAGE",
                objective_value=service_value,
                lock_tolerance=service_lock,
                evidence=service_evidence,
            )
            solution = solve_physical_seed(
                seed_model,
                time_limit_seconds=economic_seconds,
                maximum_stage=maximum_stage,
                stage_time_limits={2: economic_seconds},
                initial_stages=(initial_stage,),
            )
        else:
            model.del_component(model.audit_zero_shortage)
            model.del_component(model.audit_feasibility_objective)
            solution = solve_physical_seed(
                seed_model,
                time_limit_seconds=service_seconds + economic_seconds,
                maximum_stage=maximum_stage,
                stage_time_limits={1: service_seconds, 2: economic_seconds},
            )
    else:
        solution = solve_physical_seed(
            seed_model,
            time_limit_seconds=service_seconds + economic_seconds,
            maximum_stage=maximum_stage,
            stage_time_limits={1: service_seconds, 2: economic_seconds},
        )
    if not solution.success or len(solution.stages) != maximum_stage:
        fallback_model = build_physical_seed_model(effective_data)
        fallback_application = apply_model_policy(fallback_model, policy)
        fallback = solve_physical_seed(
            fallback_model,
            time_limit_seconds=service_seconds,
            maximum_stage=1,
            stage_time_limits={1: service_seconds},
        )
        if not fallback.success:
            raise RuntimeError(
                f"{dataset_id}/{policy['policy_id']} failed to retain a "
                f"physical witness: {fallback.status.value}"
            )
        proxy_value = evaluate_physical_seed_proxy_cost(effective_data, fallback)
        value_tolerance = effective_data.config["tolerances"]["value"]
        proxy_evidence = SolverEvidence(
            solver_name="author-side plan evaluator",
            solver_version=None,
            status=SolutionStatus.BEST_FOUND,
            raw_termination_condition="economic_seed_stage_not_solved",
            termination_message=(
                "The local-fact proxy objective did not retain an incumbent; "
                "the independently feasible service-stage witness was kept and "
                "its proxy value was evaluated without an optimality claim."
            ),
            runtime_seconds=0.0,
            incumbent_objective=proxy_value,
            best_bound=None,
            absolute_gap=None,
            relative_gap=None,
            iteration_or_node_count=None,
        )
        proxy_stage = ObjectiveStageResult(
            stage=2,
            name="EVALUATED_LOCAL_FACT_SEED_COST",
            objective_value=proxy_value,
            lock_tolerance=float(value_tolerance["absolute"])
            + float(value_tolerance["relative"]) * abs(proxy_value),
            evidence=proxy_evidence,
        )
        solution = replace(
            fallback,
            status=SolutionStatus.BEST_FOUND,
            method_classification=MethodClassification.HEURISTIC,
            method_description=(
                "HiGHS physical service witness with the local-fact selector "
                "evaluated, not optimised"
            ),
            stages=(*fallback.stages, proxy_stage),
            solver_evidence=(*fallback.solver_evidence, proxy_evidence),
        )
        seed_model = fallback_model
        model_application = fallback_application
    validation = validate_physical_solution(effective_data, solution)
    if not validation.passed:
        raise RuntimeError(
            f"{dataset_id}/{policy['policy_id']} has "
            f"{len(validation.violations)} physical violations"
        )
    raw = _raw_metrics(effective_data, solution)
    application = {**data_application, **model_application}
    policy_hash = _json_hash(policy)
    retained = {
        "dataset_id": dataset_id,
        "dataset_sha256": FROZEN_DATASET_HASHES[dataset_id],
        "policy_id": policy["policy_id"],
        "policy_sha256": policy_hash,
        "formulation": "MILP",
        "method_classification": solution.method_classification.value,
        "status": solution.status.value,
        "model_size": {
            "variables": seed_model.model.nvariables(),
            "constraints": seed_model.model.nconstraints(),
        },
        "policy_application": application,
        "stages": [_solver_record(stage) for stage in solution.stages],
        "physical_validation": {
            "passed": validation.passed,
            "checked_equations": validation.checked_equations,
            "maximum_residual": validation.max_residual,
        },
        "aggregate_metrics": _retained_metrics(raw),
        "allocation_retained": False,
    }
    return CaseResult(
        dataset_id=dataset_id,
        policy_id=policy["policy_id"],
        policy_hash=policy_hash,
        model_variables=seed_model.model.nvariables(),
        model_constraints=seed_model.model.nconstraints(),
        policy_application=application,
        solution=solution,
        raw_metrics=raw,
        retained_record=retained,
    )


def classify_default_service(
    dataset_dir: Path,
    cases: Mapping[tuple[str, str], CaseResult],
    *,
    time_limit_seconds: float,
) -> dict[str, dict[str, Any]]:
    classifications: dict[str, dict[str, Any]] = {}
    for dataset_id in DATASET_IDS:
        case = cases[(dataset_id, "PINNED_DEFAULT")]
        service_evidence = case.solution.stages[0].evidence
        if service_evidence.status.value == "globally_optimal":
            zero_shortage_feasible = case.raw_metrics["unweighted_shortage"] <= 1e-4
            classifications[dataset_id] = {
                "classification": (
                    "ZERO_SHORTAGE_FEASIBLE"
                    if zero_shortage_feasible
                    else "ZERO_SHORTAGE_INFEASIBLE"
                ),
                "certified": True,
                "source": "globally classified service stage",
                "solver_status": service_evidence.status.value,
                "termination": service_evidence.raw_termination_condition,
                "runtime_seconds": round(service_evidence.runtime_seconds, 3),
                "runtime_budget_seconds": time_limit_seconds,
                "allocation_retained": False,
            }
            continue

        data = load_model_data(dataset_dir / dataset_id / "data")
        model = build_physical_seed_model(data).model
        for objective in model.component_objects(pyo.Objective, active=True):
            objective.deactivate()
        model.zero_shortage = pyo.Constraint(
            expr=sum(model.shortage[key] for key in model.DEMAND) <= 1e-6
        )
        model.feasibility_objective = pyo.Objective(expr=0.0)
        evidence = HighsSolverAdapter().solve(
            model,
            time_limit_seconds=time_limit_seconds,
            options={"mip_rel_gap": 0.0, "time_limit": time_limit_seconds},
        )
        if evidence.has_solution:
            classification = "ZERO_SHORTAGE_FEASIBLE"
        elif evidence.status.value == "infeasible":
            classification = "ZERO_SHORTAGE_INFEASIBLE"
        else:
            classification = "UNRESOLVED"
        classifications[dataset_id] = {
            "classification": classification,
            "certified": classification != "UNRESOLVED",
            "source": "dedicated zero-shortage MILP feasibility probe",
            "solver_status": evidence.status.value,
            "termination": evidence.raw_termination_condition,
            "runtime_seconds": round(evidence.runtime_seconds, 3),
            "runtime_budget_seconds": time_limit_seconds,
            "allocation_retained": False,
        }
    return classifications


def replay_base_witness(
    dataset_dir: Path,
    base_solution: PhysicalSeedSolution,
) -> dict[str, dict[str, Any]]:
    replays: dict[str, dict[str, Any]] = {}
    for dataset_id in DATASET_IDS[1:]:
        validation = validate_physical_solution(
            load_model_data(dataset_dir / dataset_id / "data"),
            base_solution,
        )
        rules = Counter(violation.rule for violation in validation.violations)
        replays[dataset_id] = {
            "requires_adaptation": not validation.passed,
            "violation_count": len(validation.violations),
            "violation_rules": dict(sorted(rules.items())),
            "maximum_residual": round(validation.max_residual, 6),
            "allocation_retained": False,
        }
    return replays


def _bound_summary(dataset_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    retained: dict[str, Any] = {"datasets": {}}
    raw: dict[str, Any] = {}
    for dataset_id in DATASET_IDS:
        data = load_model_data(dataset_dir / dataset_id / "data")
        bounds = derive_recursive_bounds(data)
        bounds.assert_finite()
        maxima = {
            "quantity": max(bound.quantity_upper for bound in bounds.pools.values()),
            "value": max(bound.value_upper for bound in bounds.pools.values()),
            "unit_cost": max(
                bound.unit_cost_upper for bound in bounds.pools.values()
            ),
        }
        raw[dataset_id] = {"data": data, "bounds": bounds, "maxima": maxima}
        retained["datasets"][dataset_id] = {
            "pool_bound_count": len(bounds.pools),
            "shipment_bound_count": len(bounds.shipment_receipt_value_upper),
            "production_bound_count": len(bounds.production_output_value_upper),
            "maximum_quantity_upper_band": _value_band(maxima["quantity"], 10_000),
            "maximum_value_upper_band": _value_band(maxima["value"], 1_000_000),
            "maximum_unit_cost_upper_band": _value_band(
                maxima["unit_cost"], 1_000_000
            ),
            "all_finite_nonnegative": True,
        }
    retained["status"] = "PASS"
    return retained, raw


def _bound_utilisation(recursive: Any, solution: Any) -> dict[str, float]:
    def maximum_fraction(values: Mapping[Any, float], upper: Mapping[Any, float]) -> float:
        return max(
            (
                values[key] / upper[key]
                for key in values
                if upper.get(key, 0.0) > 1e-9
            ),
            default=0.0,
        )

    pool_quantity_upper = {
        key: bound.quantity_upper for key, bound in recursive.bounds.pools.items()
    }
    pool_value_upper = {
        key: bound.value_upper for key, bound in recursive.bounds.pools.items()
    }
    unit_cost_upper = {
        key: bound.unit_cost_upper for key, bound in recursive.bounds.pools.items()
    }
    return {
        "pool_quantity_derived_envelope_fraction": maximum_fraction(
            solution.pool_quantity, pool_quantity_upper
        ),
        "pool_value_derived_envelope_fraction": maximum_fraction(
            solution.pool_value, pool_value_upper
        ),
        "unit_cost_artificial_bound_fraction": maximum_fraction(
            solution.unit_cost, unit_cost_upper
        ),
        "shipment_dispatch_value_artificial_bound_fraction": maximum_fraction(
            solution.shipment_dispatch_value,
            recursive.bounds.shipment_dispatch_value_upper,
        ),
        "shipment_receipt_value_artificial_bound_fraction": maximum_fraction(
            solution.shipment_receipt_value,
            recursive.bounds.shipment_receipt_value_upper,
        ),
        "production_output_value_artificial_bound_fraction": maximum_fraction(
            solution.production_output_value,
            recursive.bounds.production_output_value_upper,
        ),
    }


def run_recursive_case(
    dataset_dir: Path,
    case: CaseResult,
    policy: Mapping[str, Any],
    *,
    time_limit_seconds: float,
    maximum_stage: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = load_model_data(dataset_dir / case.dataset_id / "data")
    effective_data, _ = apply_data_policy(data, policy)
    recursive = build_recursive_model(effective_data)
    apply_model_policy_to_recursive = policy["policy_type"] in {
        "PARENT_SHARE_LIMIT",
        "EXPEDITED_ELIGIBILITY",
        "SERVICE_WEIGHT_MULTIPLIER",
    }
    if apply_model_policy_to_recursive:
        # The conditioned physical plan already embodies these policy choices.
        # Its explicit recursive model retains the same physical formulation;
        # no second policy constraint is needed after fixing the decisions.
        pass
    solution = solve_recursive_for_physical_plan(
        recursive,
        case.solution,
        time_limit_seconds=time_limit_seconds,
        maximum_stage=maximum_stage,
    )
    validation = validate_recursive_solution(effective_data, solution)
    if not validation.passed:
        details = "; ".join(
            f"{item.rule}/{item.entity_id}: {item.residual:.6g} > {item.tolerance:.6g}"
            for item in validation.violations[:5]
        )
        raise RuntimeError(
            f"{case.dataset_id}/{case.policy_id} has "
            f"{len(validation.violations)} recursive-accounting violations: {details}"
        )
    utilisation = _bound_utilisation(recursive, solution)
    conserved = evaluate_control_selector(
        effective_data, solution, {"measure": "capitalised_plus_opening_total"}
    )
    distributed = evaluate_control_selector(
        effective_data, solution, {"measure": "served_value_total_all"}
    ) + evaluate_control_selector(
        effective_data, solution, {"measure": "terminal_closing_total"}
    )
    stage_2_value = evaluate_control_selector(
        effective_data, solution, {"measure": "stage_2_value"}
    )
    raw = {
        "recursive_total": stage_2_value,
        "capitalised_plus_opening": conserved,
        "conservation_residual": abs(conserved - distributed),
        "bound_utilisation": utilisation,
        "validation": validation,
    }
    artificial_utilisation = {
        key: value for key, value in utilisation.items() if "artificial_bound" in key
    }
    derived_envelope_utilisation = {
        key: value
        for key, value in utilisation.items()
        if "derived_envelope" in key
    }
    retained = {
        "dataset_id": case.dataset_id,
        "dataset_sha256": FROZEN_DATASET_HASHES[case.dataset_id],
        "policy_id": case.policy_id,
        "policy_sha256": case.policy_hash,
        "formulation": "MINLP",
        "method_classification": solution.method_classification.value,
        "method_description": solution.method_description,
        "status": solution.status.value,
        "conditioned_on_feasible_milp_incumbent": True,
        "stages": [_solver_record(stage) for stage in solution.stages],
        "accounting_validation": {
            "passed": validation.passed,
            "checked_equations": validation.checked_equations,
            "maximum_residual": validation.max_residual,
            "global_conservation_residual": raw["conservation_residual"],
        },
        "recursive_total_value_band_eur": _value_band(stage_2_value),
        "maximum_artificial_bound_utilisation": round(
            max(artificial_utilisation.values()), 6
        ),
        "maximum_derived_envelope_utilisation": round(
            max(derived_envelope_utilisation.values()), 6
        ),
        "derived_envelope_note": (
            "Pool quantity and value envelopes are recursively derived physical "
            "ceilings; equality is valid and is not an artificial-bound failure."
        ),
        "bound_utilisation_by_family": {
            key: round(value, 6) for key, value in sorted(utilisation.items())
        },
        "allocation_retained": False,
        "global_optimality_claimed": False,
    }
    return retained, raw


def data_participation() -> dict[str, Any]:
    roles = {
        "planning_calendar.csv": ("MATHEMATICAL_INPUT", "period ordering, dates and arrival boundary"),
        "supplier_organisations.csv": ("CONFIGURATION_EVIDENCE", "ultimate-parent and financial-risk analysis"),
        "network_nodes.csv": ("MATHEMATICAL_INPUT", "pool locations, tier and processing eligibility"),
        "plants.csv": ("MATHEMATICAL_INPUT", "terminal ownership and demand locations"),
        "materials.csv": ("MATHEMATICAL_INPUT", "material sets, units and classifications"),
        "transformation_recipes.csv": ("MATHEMATICAL_INPUT", "production eligibility, yield and setup"),
        "transformation_inputs.csv": ("MATHEMATICAL_INPUT", "bill-of-material coefficients"),
        "material_flow_approvals.csv": ("MATHEMATICAL_INPUT", "route eligibility and approved-share limits"),
        "supply_contracts.csv": ("MATHEMATICAL_INPUT", "MOQ, multiples, handling and commercial activation"),
        "incoterm_rules.csv": ("MATHEMATICAL_INPUT", "freight, insurance and duty responsibility"),
        "import_duty_rates.csv": ("MATHEMATICAL_INPUT", "effective landed-cost duty rates"),
        "source_capacity.csv": ("MATHEMATICAL_INPUT", "period source limits and surge"),
        "transformation_capacity.csv": ("MATHEMATICAL_INPUT", "regular, surge and shared production limits"),
        "shipping_lanes.csv": ("MATHEMATICAL_INPUT", "mode, transit, capacity and freight"),
        "external_source_prices.csv": ("MATHEMATICAL_INPUT", "boundary purchase value"),
        "conversion_costs.csv": ("MATHEMATICAL_INPUT", "conversion, setup, overhead and markup"),
        "cost_allocation_rules.csv": ("MATHEMATICAL_INPUT", "exactly-once cost-ledger treatment"),
        "inventory_policies.csv": ("MATHEMATICAL_INPUT", "storage, holding, terminal policy and epsilon"),
        "opening_inventory.csv": ("MATHEMATICAL_INPUT", "opening quantity and recursive book value"),
        "terminal_demand.csv": ("MATHEMATICAL_INPUT", "demand, priority and service weights"),
        "supplier_performance_history.csv": ("CONFIGURATION_EVIDENCE", "student-derived resilience and reliability rules"),
        "incident_history.csv": ("INTERPRETIVE_AUDIT_EVIDENCE", "disruption hypothesis and explanation context"),
        "disruption_scenarios.csv": ("MATHEMATICAL_INPUT", "selected package identity and run mode"),
        "disruption_impacts.csv": ("MATHEMATICAL_INPUT", "package-local effective capacity, transit, cost and demand"),
        "fx_rates.csv": ("MATHEMATICAL_INPUT", "period currency conversion"),
    }
    if set(roles) != set(EXPECTED_RAW_FILES):
        raise ContractError("data-participation classification does not cover all raw files")
    counts: dict[str, int] = defaultdict(int)
    records = []
    for file_name in EXPECTED_RAW_FILES:
        role, evidence = roles[file_name]
        counts[role] += 1
        records.append({"file": file_name, "role": role, "evidence": evidence})
    return {
        "status": "PASS",
        "file_count": len(records),
        "role_counts": dict(sorted(counts.items())),
        "files": records,
    }


def _material_change(
    metric: str,
    base: float,
    changed: float,
    bands: Mapping[str, float],
) -> bool:
    if "share" in metric:
        return abs(changed - base) >= bands["share_absolute"]
    if "shortage" in metric:
        return abs(changed - base) >= bands["shortage_absolute"]
    if metric == "physical_seed_proxy_cost":
        return _relative_change(base, changed) >= bands["cost_relative"]
    if metric == "total_inventory":
        return _relative_change(base, changed) >= bands["inventory_relative"]
    return abs(changed - base) >= bands["quantity_absolute"]


def _economic_interval(case: CaseResult) -> tuple[float, float] | None:
    """Return the valid objective interval for a minimisation incumbent."""

    evidence = case.solution.stages[1].evidence
    incumbent = evidence.incumbent_objective
    best_bound = evidence.best_bound
    if incumbent is None or best_bound is None:
        return None
    return min(best_bound, incumbent), max(best_bound, incumbent)


def _certified_cost_difference(
    left: CaseResult,
    right: CaseResult,
    bands: Mapping[str, float],
) -> tuple[bool, str]:
    """Reject apparent cost differences that fit inside solver uncertainty."""

    left_interval = _economic_interval(left)
    right_interval = _economic_interval(right)
    if left_interval is None or right_interval is None:
        return False, "an economic objective interval is unavailable"
    left_lower, left_upper = left_interval
    right_lower, right_upper = right_interval
    separation = max(
        0.0,
        right_lower - left_upper,
        left_lower - right_upper,
    )
    scale = max(1.0, min(left_upper, right_upper))
    if separation / scale < bands["cost_relative"]:
        return False, "economic objective intervals overlap or are not materially separated"
    return True, "economic objective intervals are materially disjoint"


def _economic_stage_is_global(case: CaseResult) -> bool:
    return case.solution.stages[1].evidence.status.value == "globally_optimal"


def _scenario_materiality(
    cases: Mapping[tuple[str, str], CaseResult],
    bands: Mapping[str, float],
    scenario_replay: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    base_case = cases[("BASE", "PINNED_DEFAULT")]
    base = base_case.raw_metrics
    metric_map = {
        "SCN-01": (
            "source_node_0005_quantity",
            "total_inventory",
            "physical_seed_proxy_cost",
            "max_parent_share",
            "unweighted_shortage",
        ),
        "SCN-02": (
            "affected_corridor_quantity",
            "expedited_quantity",
            "total_inventory",
            "physical_seed_proxy_cost",
            "unweighted_shortage",
        ),
        "SCN-03": (
            "node_0030_production",
            "target_approval_share",
            "total_inventory",
            "physical_seed_proxy_cost",
            "unweighted_shortage",
        ),
        "SCN-04": (
            "regional_affected_node_activity",
            "max_parent_share",
            "total_inventory",
            "physical_seed_proxy_cost",
            "unweighted_shortage",
        ),
        "SCN-05": (
            "expedited_quantity",
            "total_inventory",
            "physical_seed_proxy_cost",
            "unweighted_shortage",
        ),
    }
    constructs = {
        "SCN-01": "source-capacity bounds and upstream substitution",
        "SCN-02": "lane capacity, transit indexing, mode eligibility and freight",
        "SCN-03": "transformation capacity, alternate approvals and inventory balance",
        "SCN-04": "multi-tier capacity and parent-concentration recourse",
        "SCN-05": "composed supply/logistics impacts and service-priority balance",
    }
    results: dict[str, Any] = {}
    for dataset_id, metrics in metric_map.items():
        changed_case = cases[(dataset_id, "PINNED_DEFAULT")]
        changed = changed_case.raw_metrics
        witnesses = []
        uncertified = []
        replay = scenario_replay[dataset_id]
        if replay["requires_adaptation"]:
            witnesses.append(
                {
                    "metric": "base_witness_scenario_compatibility",
                    "base": "physically_valid",
                    "scenario": "adaptation_required",
                    "violation_count": replay["violation_count"],
                    "violation_rules": replay["violation_rules"],
                    "certification": (
                        "independent physical replay against the replacement dataset"
                    ),
                }
            )
        for metric in metrics:
            left = float(base[metric])
            right = float(changed[metric])
            if not _material_change(metric, left, right, bands):
                continue
            if metric == "physical_seed_proxy_cost":
                certified, reason = _certified_cost_difference(
                    base_case, changed_case, bands
                )
            elif "shortage" in metric:
                certified = (
                    base_case.solution.stages[0].evidence.status.value
                    == "globally_optimal"
                    and changed_case.solution.stages[0].evidence.status.value
                    == "globally_optimal"
                )
                reason = "service objectives are globally classified"
            else:
                certified = _economic_stage_is_global(
                    base_case
                ) and _economic_stage_is_global(changed_case)
                reason = (
                    "aggregate decision difference comes from globally optimal "
                    "economic stages"
                    if certified
                    else "aggregate decision difference is incumbent-only"
                )
            record = {
                "metric": metric,
                "base": round(left, 3),
                "scenario": round(right, 3),
                "relative_change": round(_relative_change(left, right), 4),
                "certification": reason,
            }
            if certified:
                witnesses.append(
                    record
                )
            else:
                uncertified.append(record)
        results[dataset_id] = {
            "passed": bool(witnesses),
            "model_construct": constructs[dataset_id],
            "base_witness_replay": replay,
            "material_witnesses": witnesses,
            "uncertified_incumbent_differences": uncertified,
        }
    return results


def _policy_materiality(
    cases: Mapping[tuple[str, str], CaseResult], bands: Mapping[str, float]
) -> dict[str, Any]:
    comparisons = {
        "resilience": [
            ("BASE", "PARENT_DIVERSITY_58", ("max_parent_share", "physical_seed_proxy_cost", "unweighted_shortage")),
            ("SCN-04", "PARENT_DIVERSITY_58", ("max_parent_share", "physical_seed_proxy_cost", "unweighted_shortage")),
        ],
        "intervention": [
            ("SCN-02", "NO_EXPEDITED_TRANSPORT", ("expedited_quantity", "physical_seed_proxy_cost", "unweighted_shortage")),
            ("SCN-05", "NO_EXPEDITED_TRANSPORT", ("expedited_quantity", "physical_seed_proxy_cost", "unweighted_shortage")),
        ],
        "approval": [
            ("SCN-03", "APPROVAL_SHARE_EXCEPTION", ("target_approval_share", "physical_seed_proxy_cost", "unweighted_shortage")),
        ],
        "service": [
            ("SCN-05", "CRITICAL_SERVICE_SENSITIVITY", ("weighted_shortage", "unweighted_shortage", "physical_seed_proxy_cost")),
        ],
    }
    output: dict[str, Any] = {}
    for capability, probes in comparisons.items():
        probe_records = []
        for dataset_id, policy_id, metrics in probes:
            base_case = cases[(dataset_id, "PINNED_DEFAULT")]
            changed_case = cases[(dataset_id, policy_id)]
            base = base_case.raw_metrics
            changed = changed_case.raw_metrics
            witnesses = []
            uncertified = []
            for metric in metrics:
                left, right = float(base[metric]), float(changed[metric])
                if not _material_change(metric, left, right, bands):
                    continue
                if metric == "physical_seed_proxy_cost":
                    certified, reason = _certified_cost_difference(
                        base_case, changed_case, bands
                    )
                else:
                    certified, reason = True, "direct configured aggregate consequence"
                record = {
                    "metric": metric,
                    "default": round(left, 3),
                    "configured": round(right, 3),
                    "relative_change": round(_relative_change(left, right), 4),
                    "certification": reason,
                }
                if certified:
                    witnesses.append(
                        record
                    )
                else:
                    uncertified.append(record)
            probe_records.append(
                {
                    "dataset_id": dataset_id,
                    "policy_id": policy_id,
                    "passed": bool(witnesses),
                    "material_witnesses": witnesses,
                    "uncertified_incumbent_differences": uncertified,
                }
            )
        output[capability] = {
            "passed": any(record["passed"] for record in probe_records),
            "probes": probe_records,
        }
    approval_case = cases[("SCN-03", "APPROVAL_SHARE_EXCEPTION")]
    output["approval"]["override_applied"] = (
        approval_case.policy_application.get("data_override_count", 0) > 0
        and bool(approval_case.policy_application.get("authority"))
    )
    output["approval"]["passed"] = bool(
        output["approval"]["override_applied"]
        and any(record["passed"] for record in output["approval"]["probes"])
    )
    service_case = cases[("SCN-05", "CRITICAL_SERVICE_SENSITIVITY")]
    service_default = cases[("SCN-05", "PINNED_DEFAULT")]
    service_inactive_because_fully_served = (
        service_default.raw_metrics["unweighted_shortage"] <= 1e-4
        and service_case.raw_metrics["unweighted_shortage"] <= 1e-4
    )
    output["service"]["objective_modified"] = service_case.policy_application.get(
        "objective_modified", False
    )
    output["service"]["inactive_because_fully_served"] = (
        service_inactive_because_fully_served
    )
    output["service"]["passed"] = bool(
        output["service"]["objective_modified"]
        and any(record["passed"] for record in output["service"]["probes"])
    )
    return output


def _opposed_tradeoff(
    cases: Mapping[tuple[str, str], CaseResult], bands: Mapping[str, float]
) -> dict[str, Any]:
    candidates = []
    for dataset_id in ("BASE", "SCN-04"):
        default_case = cases[(dataset_id, "PINNED_DEFAULT")]
        diverse_case = cases[(dataset_id, "PARENT_DIVERSITY_58")]
        default = default_case.raw_metrics
        diverse = diverse_case.raw_metrics
        share_improved = (
            default["max_parent_share"] - diverse["max_parent_share"]
            >= bands["share_absolute"]
        )
        cost_certified, cost_certification = _certified_cost_difference(
            default_case, diverse_case, bands
        )
        service_consequence = (
            diverse["unweighted_shortage"] - default["unweighted_shortage"]
            >= bands["shortage_absolute"]
        )
        economic_or_service_cost = cost_certified or service_consequence
        candidates.append(
            {
                "dataset_id": dataset_id,
                "share_improved": share_improved,
                "economic_or_service_consequence": economic_or_service_cost,
                "default_parent_share": round(default["max_parent_share"], 4),
                "configured_parent_share": round(diverse["max_parent_share"], 4),
                "cost_relative_change": round(
                    _relative_change(
                        default["physical_seed_proxy_cost"],
                        diverse["physical_seed_proxy_cost"]
                    ),
                    4,
                ),
                "cost_certification": cost_certification,
                "shortage_change": round(
                    diverse["unweighted_shortage"] - default["unweighted_shortage"],
                    3,
                ),
                "decision_pair_only": True,
                "global_optimality_claimed": False,
            }
        )
    witness = next(
        (
            candidate
            for candidate in candidates
            if candidate["share_improved"]
            and candidate["economic_or_service_consequence"]
        ),
        None,
    )
    return {"passed": witness is not None, "witness": witness, "candidates": candidates}


def _privacy_scan(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in FORBIDDEN_EVIDENCE_KEYS:
                failures.append(f"{path}.{key}")
            failures.extend(_privacy_scan(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_privacy_scan(child, f"{path}[{index}]"))
    return failures


def _scorecard(
    frozen: Mapping[str, Any],
    cases: Mapping[tuple[str, str], CaseResult],
    service_classifications: Mapping[str, Mapping[str, Any]],
    scenario_replay: Mapping[str, Mapping[str, Any]],
    recursive_records: list[Mapping[str, Any]],
    recursive_raw: Mapping[tuple[str, str], Mapping[str, Any]],
    participation: Mapping[str, Any],
    matrix: Mapping[str, Any],
    unauthorised_rejected: bool,
) -> dict[str, Any]:
    bands = matrix["materiality_bands"]
    scenario = _scenario_materiality(cases, bands, scenario_replay)
    policy = _policy_materiality(cases, bands)
    policy["approval"]["unauthorised_exception_rejected"] = unauthorised_rejected
    policy["approval"]["passed"] = (
        policy["approval"]["passed"] and unauthorised_rejected
    )
    tradeoff = _opposed_tradeoff(cases, bands)
    default_cases = [cases[(dataset_id, "PINNED_DEFAULT")] for dataset_id in DATASET_IDS]
    expected_recursive = {
        (run["dataset_id"], run["policy_id"])
        for run in matrix["recursive_runs"]
    }
    actual_recursive = set(recursive_raw)
    max_artificial_bound_use = max(
        (
            max(
                value
                for key, value in record["bound_utilisation"].items()
                if "artificial_bound" in key
            )
            for record in recursive_raw.values()
        ),
        default=1.0,
    )
    evidence_for_privacy = {
        "milp": [case.retained_record for case in cases.values()],
        "recursive": recursive_records,
        "participation": participation,
    }
    privacy_failures = _privacy_scan(evidence_for_privacy)
    gates = [
        {
            "gate_id": "G1",
            "label": "Frozen identity",
            "passed": set(frozen) == set(DATASET_IDS)
            and all(record["manifest_identity"] for record in frozen.values()),
            "evidence": "six package hashes and identities match the accepted checkpoint",
        },
        {
            "gate_id": "G2",
            "label": "Common explicit MILP formulation",
            "passed": all(case.solution.success for case in default_cases)
            and all(case.retained_record["formulation"] == "MILP" for case in default_cases),
            "evidence": "one builder and two-stage solve path accepted all six packages",
        },
        {
            "gate_id": "G3",
            "label": "Feasibility and service classification",
            "passed": all(
                service_classifications[case.dataset_id]["certified"]
                and case.retained_record["physical_validation"]["passed"]
                for case in default_cases
            )
            and service_classifications["BASE"]["classification"]
            == "ZERO_SHORTAGE_FEASIBLE",
            "evidence": service_classifications,
        },
        {
            "gate_id": "G4",
            "label": "Scenario materiality",
            "passed": all(record["passed"] for record in scenario.values()),
            "evidence": scenario,
        },
        {
            "gate_id": "G5",
            "label": "Configuration sensitivity",
            "passed": all(record["passed"] for record in policy.values()),
            "evidence": policy,
        },
        {
            "gate_id": "G6",
            "label": "Opposed decision trade-off",
            "passed": tradeoff["passed"],
            "evidence": tradeoff,
        },
        {
            "gate_id": "G7",
            "label": "Recursive-cost MINLP viability",
            "passed": actual_recursive == expected_recursive
            and all(record["status"] == "locally_optimal" for record in recursive_records)
            and all(record["accounting_validation"]["passed"] for record in recursive_records),
            "evidence": {
                "expected_cases": sorted("/".join(key) for key in expected_recursive),
                "completed_cases": sorted("/".join(key) for key in actual_recursive),
                "global_optimality_claimed": False,
            },
        },
        {
            "gate_id": "G8",
            "label": "Bounds and accounting",
            "passed": bool(recursive_records)
            and max_artificial_bound_use < 0.999
            and all(
                record["validation"].passed for record in recursive_raw.values()
            ),
            "evidence": {
                "maximum_artificial_bound_utilisation": round(
                    max_artificial_bound_use, 6
                ),
                "derived_pool_envelopes_may_be_exact": True,
                "maximum_accounting_residual": max(
                    (
                        record["accounting_validation"]["maximum_residual"]
                        for record in recursive_records
                    ),
                    default=None,
                ),
            },
        },
        {
            "gate_id": "G9",
            "label": "Data-family usefulness",
            "passed": participation["status"] == "PASS"
            and participation["file_count"] == len(EXPECTED_RAW_FILES),
            "evidence": participation["role_counts"],
        },
        {
            "gate_id": "G10",
            "label": "Accessibility and privacy",
            "passed": not privacy_failures
            and all(
                sum(stage.evidence.runtime_seconds for stage in case.solution.stages)
                <= matrix["solver_budgets"]["milp_service_seconds"]
                + matrix["solver_budgets"]["milp_economic_seconds"]
                + 5
                for case in cases.values()
            )
            and all(
                record["runtime_seconds"] <= record["runtime_budget_seconds"] + 5
                for record in service_classifications.values()
            )
            and all(not record["allocation_retained"] for record in recursive_records),
            "evidence": {
                "privacy_failures": privacy_failures,
                "allocation_retained": False,
                "bounded_runs": True,
            },
        },
    ]
    all_gates_pass = all(gate["passed"] for gate in gates)
    all_default_cases_source = all(
        case.raw_metrics["total_source"] > 1e-6 for case in default_cases
    )
    return {
        "audit_id": matrix["audit_id"],
        "matrix_version": matrix["matrix_version"],
        "status": "PASS" if all_gates_pass else "FAIL",
        "passed_gate_count": sum(gate["passed"] for gate in gates),
        "gate_count": len(gates),
        "gates": gates,
        "calibration_finding": {
            "default_boundary_source_quantity_by_dataset": {
                case.dataset_id: round(case.raw_metrics["total_source"], 3)
                for case in default_cases
            },
            "all_default_cases_use_zero_boundary_supply": all(
                case.raw_metrics["total_source"] <= 1e-6 for case in default_cases
            ),
            "all_default_cases_use_boundary_supply": all_default_cases_source,
            "interpretation": (
                "Boundary replenishment participates in every default case; "
                "scenario replacement and configuration probes exercise the "
                "network without publishing an allocation."
                if all_default_cases_source
                else "Boundary-supply participation is not consistent across all default cases."
            ),
        },
        "controlled_reopen": {
            "required": not all_gates_pass,
            "originating_control": (
                None if all_gates_pass else "failed whole-dataset viability gates"
            ),
            "next_action": (
                "None; the bounded author-side viability audit is complete."
                if all_gates_pass
                else "Review the failed gate evidence before changing data or probe design."
            ),
        },
        "allocation_retained": False,
        "reference_solution_created": False,
    }


def _report(scorecard: Mapping[str, Any], cases: Mapping[tuple[str, str], CaseResult]) -> str:
    defaults = [cases[(dataset_id, "PINNED_DEFAULT")] for dataset_id in DATASET_IDS]
    accepted = scorecard["status"] == "PASS"
    lines = [
        "# CAP-001 Whole-Dataset Viability Audit",
        "",
        "## Outcome",
        "",
        f"Audit status: **{scorecard['status']}** ({scorecard['passed_gate_count']} of {scorecard['gate_count']} gates).",
        "",
        "The audit used explicit MILP and MINLP formulations only. It retained aggregate evidence and did not create a reference allocation, preferred recommendation or application.",
        "",
        "## Owner decision",
        "",
        (
            "The package set passes the bounded author-side viability audit. "
            "This accepts the datasets as sufficiently deep examination inputs; "
            "it does not approve an optimiser or expected answer."
            if accepted
            else "The package set is not accepted for WP7. Review the failed "
            "gate evidence before changing data or probe design."
        ),
        "",
        (
            "No controlled reopen is required."
            if accepted
            else scorecard["controlled_reopen"]["next_action"]
        ),
        "",
        "## Private physical-seed MILP cases",
        "",
        "| Dataset | Service status | Shortage | Seed status | Proxy-cost band (EUR) |",
        "|---|---|---:|---|---:|",
    ]
    for case in defaults:
        stages = case.retained_record["stages"]
        band = case.retained_record["aggregate_metrics"][
            "physical_seed_proxy_cost_band_eur"
        ]
        lines.append(
            f"| {case.dataset_id} | {stages[0]['status']} | "
            f"{case.retained_record['aggregate_metrics']['unweighted_shortage']:.3f} | "
            f"{stages[1]['status']} | {band['lower']:,.0f}–{band['upper']:,.0f} |"
        )
    lines.extend(
        [
            "",
            "## Gate results",
            "",
            "| Gate | Result | Evidence summary |",
            "|---|---|---|",
        ]
    )
    for gate in scorecard["gates"]:
        evidence = gate["evidence"]
        summary = evidence if isinstance(evidence, str) else "See machine-readable scorecard"
        lines.append(
            f"| {gate['gate_id']} — {gate['label']} | "
            f"{'PASS' if gate['passed'] else 'FAIL'} | {summary} |"
        )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "Economic stages may be time-limited and are reported as incumbents with solver gaps. Zero-shortage feasibility, scenario-witness replay and physical/accounting reconciliation are checked independently. No global-optimality claim is made for the bounded decision pairs or the non-convex recursive formulation.",
            "",
            "A cost difference is accepted as material only when the two solver objective intervals are materially disjoint. Scenario materiality is otherwise established by independent physical replay of a valid BASE witness against the complete replacement dataset. Bounded incumbent decision pairs may demonstrate an available trade-off, but not that it is uniquely optimal or unavoidable.",
            "",
            "No row-level orders, shipments, production, inventory, service allocation, pool values or expected student objective are retained.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_evidence(output_dir: Path, files: Mapping[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (output_dir / name).write_text(content, encoding="utf-8")
    records = {
        name: {"sha256": sha256_path(output_dir / name), "bytes": (output_dir / name).stat().st_size}
        for name in sorted(files)
    }
    scorecard = json.loads(files["viability_scorecard.json"])
    manifest = {
        "audit_id": "CAP-001-WHOLE-DATASET-VIABILITY",
        "audit_status": scorecard["status"],
        "passed_gate_count": scorecard["passed_gate_count"],
        "gate_count": scorecard["gate_count"],
        "evidence_files": records,
        "input_package_hashes": FROZEN_DATASET_HASHES,
        "allocation_retained": False,
    }
    (output_dir / "audit_manifest.json").write_text(
        canonical_json(manifest), encoding="utf-8"
    )


def run_audit(
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    policy_path: Path = DEFAULT_POLICY_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    matrix = load_policy_matrix(policy_path)
    policies = _policy_map(matrix)
    frozen = verify_frozen_inputs(dataset_dir)
    print("Frozen package identity: PASS", flush=True)
    bound_retained, _ = _bound_summary(dataset_dir)
    print("Full-scale recursive bounds: PASS", flush=True)
    participation = data_participation()
    cases: dict[tuple[str, str], CaseResult] = {}
    for run in matrix["milp_runs"]:
        key = (run["dataset_id"], run["policy_id"])
        print(f"MILP {key[0]}/{key[1]}: running", flush=True)
        case = run_milp_case(
            dataset_dir,
            key[0],
            policies[key[1]],
            service_seconds=float(
                matrix["solver_budgets"]["milp_service_seconds"]
            ),
            economic_seconds=float(
                matrix["solver_budgets"]["milp_economic_seconds"]
            ),
            maximum_stage=int(matrix["solver_budgets"]["milp_maximum_stage"]),
        )
        cases[key] = case
        print(
            f"MILP {key[0]}/{key[1]}: {case.solution.status.value}; "
            f"shortage={case.raw_metrics['unweighted_shortage']:.3f}",
            flush=True,
        )
    service_classifications = classify_default_service(
        dataset_dir,
        cases,
        time_limit_seconds=float(
            matrix["solver_budgets"]["milp_service_seconds"]
        ),
    )
    for dataset_id, record in service_classifications.items():
        print(
            f"SERVICE {dataset_id}: {record['classification']}",
            flush=True,
        )
    scenario_replay = replay_base_witness(
        dataset_dir,
        cases[("BASE", "PINNED_DEFAULT")].solution,
    )
    for dataset_id, record in scenario_replay.items():
        print(
            f"REPLAY {dataset_id}: "
            f"{'adaptation_required' if record['requires_adaptation'] else 'compatible'}",
            flush=True,
        )
    negative = policies["UNAUTHORISED_EXCEPTION_NEGATIVE"]
    try:
        data = load_model_data(dataset_dir / "SCN-03" / "data")
        apply_data_policy(data, negative)
    except ContractError:
        unauthorised_rejected = True
    else:
        unauthorised_rejected = False
    recursive_records: list[dict[str, Any]] = []
    recursive_raw: dict[tuple[str, str], dict[str, Any]] = {}
    for run in matrix["recursive_runs"]:
        key = (run["dataset_id"], run["policy_id"])
        print(f"MINLP {key[0]}/{key[1]}: running", flush=True)
        retained, raw = run_recursive_case(
            dataset_dir,
            cases[key],
            policies[key[1]],
            time_limit_seconds=float(
                matrix["solver_budgets"]["recursive_conditioned_seconds"]
            ),
            maximum_stage=int(
                matrix["solver_budgets"]["recursive_maximum_stage"]
            ),
        )
        recursive_records.append(retained)
        recursive_raw[key] = raw
        print(
            f"MINLP {key[0]}/{key[1]}: {retained['status']}; "
            f"residual={retained['accounting_validation']['maximum_residual']:.3g}",
            flush=True,
        )
    scorecard = _scorecard(
        frozen,
        cases,
        service_classifications,
        scenario_replay,
        recursive_records,
        recursive_raw,
        participation,
        matrix,
        unauthorised_rejected,
    )
    files = {
        "bound_summary.json": canonical_json(bound_retained),
        "data_participation.json": canonical_json(participation),
        "milp_case_summary.json": canonical_json(
            {
                "case_count": len(cases),
                "cases": [
                    cases[key].retained_record for key in sorted(cases)
                ],
                "allocation_retained": False,
            }
        ),
        "recursive_case_summary.json": canonical_json(
            {
                "case_count": len(recursive_records),
                "cases": recursive_records,
                "allocation_retained": False,
                "global_optimality_claimed": False,
            }
        ),
        "viability_scorecard.json": canonical_json(scorecard),
        "WHOLE_DATASET_VIABILITY_REPORT.md": _report(scorecard, cases),
    }
    _write_evidence(output_dir, files)
    print(
        f"Whole-dataset viability audit: {scorecard['status']} "
        f"({scorecard['passed_gate_count']}/{scorecard['gate_count']} gates)",
        flush=True,
    )
    return scorecard


def check_evidence(
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    policy_path: Path = DEFAULT_POLICY_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[str, ...]:
    failures: list[str] = []
    try:
        verify_frozen_inputs(dataset_dir)
        matrix = load_policy_matrix(policy_path)
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        return (str(exc),)
    manifest_path = output_dir / "audit_manifest.json"
    if not manifest_path.is_file():
        return ("audit manifest is missing",)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("input_package_hashes") != FROZEN_DATASET_HASHES:
        failures.append("audit manifest package hashes do not match frozen inputs")
    if set(manifest.get("evidence_files", {})) != set(EVIDENCE_FILES):
        failures.append("audit manifest evidence-file set is incomplete")
    for name in EVIDENCE_FILES:
        path = output_dir / name
        if not path.is_file():
            failures.append(f"missing evidence file {name}")
            continue
        expected = manifest["evidence_files"].get(name, {}).get("sha256")
        if sha256_path(path) != expected:
            failures.append(f"evidence hash mismatch for {name}")
    scorecard_path = output_dir / "viability_scorecard.json"
    if scorecard_path.is_file():
        scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
        gates = scorecard.get("gates", [])
        passed = sum(bool(gate.get("passed")) for gate in gates)
        if scorecard.get("status") not in {"PASS", "FAIL"}:
            failures.append("stored viability scorecard has an invalid decision status")
        if scorecard.get("gate_count") != 10 or len(gates) != 10:
            failures.append("stored viability scorecard does not contain ten gates")
        if scorecard.get("passed_gate_count") != passed:
            failures.append("stored viability scorecard gate count is inconsistent")
        if scorecard.get("status") != ("PASS" if passed == 10 else "FAIL"):
            failures.append("stored viability scorecard decision is inconsistent")
        if manifest.get("audit_status") != scorecard.get("status"):
            failures.append("audit manifest decision differs from the scorecard")
        privacy_failures = _privacy_scan(scorecard)
        failures.extend(f"private allocation key retained at {path}" for path in privacy_failures)
    participation_path = output_dir / "data_participation.json"
    if participation_path.is_file():
        participation = json.loads(participation_path.read_text(encoding="utf-8"))
        if {record["file"] for record in participation.get("files", [])} != set(
            EXPECTED_RAW_FILES
        ):
            failures.append("data-participation evidence does not cover 25 raw files")
    case_path = output_dir / "milp_case_summary.json"
    if case_path.is_file():
        case_data = json.loads(case_path.read_text(encoding="utf-8"))
        expected_cases = {
            (run["dataset_id"], run["policy_id"]) for run in matrix["milp_runs"]
        }
        actual_cases = {
            (case["dataset_id"], case["policy_id"])
            for case in case_data.get("cases", [])
        }
        if actual_cases != expected_cases:
            failures.append("stored MILP case set does not match the policy matrix")
        privacy_failures = _privacy_scan(case_data)
        failures.extend(f"private allocation key retained at {path}" for path in privacy_failures)
    recursive_path = output_dir / "recursive_case_summary.json"
    if recursive_path.is_file():
        recursive_data = json.loads(recursive_path.read_text(encoding="utf-8"))
        expected_cases = {
            (run["dataset_id"], run["policy_id"])
            for run in matrix["recursive_runs"]
        }
        actual_cases = {
            (case["dataset_id"], case["policy_id"])
            for case in recursive_data.get("cases", [])
        }
        if actual_cases != expected_cases:
            failures.append("stored MINLP case set does not match the policy matrix")
        privacy_failures = _privacy_scan(recursive_data)
        failures.extend(f"private allocation key retained at {path}" for path in privacy_failures)
    return tuple(failures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="execute solver probes and write aggregate evidence")
    parser.add_argument("--check", action="store_true", help="validate retained evidence without rerunning solvers")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    if args.run == args.check:
        parser.error("choose exactly one of --run or --check")
    if args.run:
        run_audit(args.dataset_dir, args.policy, args.output_dir)
        return 0
    failures = check_evidence(args.dataset_dir, args.policy, args.output_dir)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    scorecard = json.loads(
        (args.output_dir / "viability_scorecard.json").read_text(encoding="utf-8")
    )
    print(
        "Whole-dataset viability evidence is current; "
        f"audit decision {scorecard['status']} "
        f"({scorecard['passed_gate_count']}/{scorecard['gate_count']} gates)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
