"""Build and verify the public CAP-001 BASE reference incumbent.

The retained incumbent is calibration evidence, not a model input or an
optimality target. Generation uses a private local-fact physical-seed MILP and
then solves the exact recursive value equations for that integer plan. The
result is honestly classified as a heuristic MINLP incumbent and is replayed by
independent validators before publication.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from cap001_model.physical_seed import build_physical_seed_model, solve_physical_seed
from cap001_model.contracts import MethodClassification
from cap001_model.data import ModelData, load_model_data
from cap001_model.recursive import (
    RecursiveSolution,
    build_recursive_model,
    solve_recursive_for_physical_plan,
)
from cap001_model.recursive_validation import (
    _component_totals,
    validate_recursive_solution,
)
from cap001_model.solution_bundle import (
    read_solution_bundle,
    solution_bundle_payload,
)
from cap001_model.validation import validate_physical_solution
from tooling.contract_runtime import (
    CONFIG_PATH,
    ROOT,
    canonical_json,
    load_config,
    sha256_bytes,
    sha256_path,
)


DATASET_ROOT = ROOT / "generated/datasets/BASE"
PUBLIC_ROOT = ROOT / "student_release/CAP-001-tier-n-release/reference/base_benchmark"
PRIVATE_ROOT = ROOT / "reference/base_benchmark"
SOLUTION_FILE = "reference_solution.json"
CONTRACT_FILE = "benchmark_contract.json"
NOTES_FILE = "BENCHMARK_NOTES.md"
MANIFEST_FILE = "benchmark_manifest.json"
REQUIRED_FILES = (SOLUTION_FILE, CONTRACT_FILE, NOTES_FILE, MANIFEST_FILE)


def _dataset_manifest() -> Mapping[str, Any]:
    return json.loads(
        (DATASET_ROOT / "dataset_manifest.json").read_text(encoding="utf-8")
    )


def solve_reference(data: ModelData) -> RecursiveSolution:
    """Produce the declared two-phase heuristic reference incumbent."""

    seed = solve_physical_seed(
        build_physical_seed_model(data),
        time_limit_seconds=720,
        maximum_stage=2,
        stage_time_limits={1: 180.0, 2: 540.0},
    )
    if not seed.success:
        raise RuntimeError(
            "BASE physical-seed MILP did not retain a feasible integer plan: "
            f"{seed.status.value}"
        )
    physical = validate_physical_solution(data, seed)
    if not physical.passed:
        raise RuntimeError(
            f"BASE physical seed failed {len(physical.violations)} checks"
        )
    solution = solve_recursive_for_physical_plan(
        build_recursive_model(data),
        seed,
        time_limit_seconds=300,
        maximum_stage=2,
    )
    solution = replace(
        solution,
        method_classification=MethodClassification.HEURISTIC,
        method_description=(
            "Declared two-phase heuristic around the explicit recursive MINLP: "
            "HiGHS solves a local-fact physical-seed MILP, then IPOPT solves the "
            "exact recursive value equations with the retained integer plan fixed; "
            "global optimality and allocation uniqueness are not claimed"
        ),
    )
    accounting = validate_recursive_solution(data, solution)
    if not accounting.passed:
        raise RuntimeError(
            f"BASE reference failed {len(accounting.violations)} accounting checks"
        )
    return solution


def _metrics(data: ModelData, solution: RecursiveSolution) -> dict[str, Any]:
    final_period = data.periods[-1]
    demand_quantity = sum(row["demand_quantity"] for row in data.demand.values())
    served_quantity = sum(solution.served.values())
    shortage_quantity = sum(solution.shortage.values())
    weighted_shortage = sum(
        data.demand[key]["service_weight"] * value
        for key, value in solution.shortage.items()
    )
    components = _component_totals(data, solution)
    return {
        "demand_quantity": demand_quantity,
        "served_quantity": served_quantity,
        "shortage_quantity": shortage_quantity,
        "service_rate": served_quantity / demand_quantity,
        "weighted_shortage": weighted_shortage,
        "terminal_served_value_eur": sum(solution.served_value.values()),
        "terminal_closing_inventory_quantity": sum(
            value
            for (_, _, period), value in solution.closing_inventory.items()
            if period == final_period
        ),
        "terminal_closing_inventory_value_eur": sum(
            value
            for (_, _, period), value in solution.closing_value.items()
            if period == final_period
        ),
        "total_source_quantity": sum(solution.source_supply.values()),
        "total_shipment_quantity": sum(solution.shipments.values()),
        "total_production_quantity": sum(solution.production.values()),
        "active_contracts": sum(
            1 for value in solution.contract_active.values() if value > 0.5
        ),
        "active_shipments": sum(
            1 for value in solution.shipment_active.values() if value > 0.5
        ),
        "active_production_runs": sum(
            1 for value in solution.production_active.values() if value > 0.5
        ),
        "component_totals_eur": components,
    }


def _contract(data: ModelData, solution: RecursiveSolution) -> dict[str, Any]:
    config = data.config
    dataset = _dataset_manifest()
    physical = validate_physical_solution(data, solution)
    accounting = validate_recursive_solution(data, solution)
    stages = [
        {
            "stage": stage.stage,
            "name": stage.name,
            "reference_value": stage.objective_value,
            "model_lock_tolerance": stage.lock_tolerance,
            "status": stage.evidence.status.value,
        }
        for stage in solution.stages
    ]
    stage_1 = stages[0]
    stage_2 = stages[1]
    quantity = config["tolerances"]["quantity"]
    value = config["tolerances"]["value"]
    stage_1["reproduction_upper_bound"] = (
        stage_1["reference_value"]
        + quantity["absolute"]
        + quantity["relative"] * abs(stage_1["reference_value"])
    )
    stage_2["reproduction_upper_bound"] = (
        stage_2["reference_value"] * 1.01
        + value["absolute"]
        + value["relative"] * abs(stage_2["reference_value"])
    )
    return {
        "benchmark_id": "CAP-001-BASE-REFERENCE-001",
        "benchmark_version": "1.0.0",
        "dataset_id": "BASE",
        "dataset_version": config["versions"]["data"],
        "dataset_sha256": dataset["dataset_sha256"],
        "configuration_id": config["configuration_id"],
        "configuration_version": config["configuration_version"],
        "configuration_sha256": sha256_path(CONFIG_PATH),
        "model_version": config["versions"]["model"],
        "formulation_class": solution.formulation_class.value,
        "method_classification": solution.method_classification.value,
        "method_description": solution.method_description,
        "status": solution.status.value,
        "global_optimality_claimed": False,
        "allocation_uniqueness_claimed": False,
        "exact_allocation_match_required": False,
        "solution_is_model_input": False,
        "objective_stages": stages,
        "metrics": _metrics(data, solution),
        "independent_validation": {
            "physical": {
                "passed": physical.passed,
                "checked_equations": physical.checked_equations,
                "maximum_residual": physical.max_residual,
            },
            "recursive_accounting": {
                "passed": accounting.passed,
                "checked_equations": accounting.checked_equations,
                "maximum_residual": accounting.max_residual,
            },
        },
        "reproduction_contract": {
            "required": True,
            "physical_validation_required": True,
            "recursive_accounting_validation_required": True,
            "stage_1_rule": "candidate_value <= reproduction_upper_bound",
            "stage_2_rule": (
                "when stage 1 passes, candidate_value <= reproduction_upper_bound; "
                "a stronger valid value also passes"
            ),
            "aggregate_difference_rule": (
                "material sourcing, production, logistics or inventory differences "
                "must be explained; they are not automatic failure"
            ),
            "controlled_tolerances": config["tolerances"],
        },
    }


def _notes(contract: Mapping[str, Any]) -> str:
    metrics = contract["metrics"]
    stages = contract["objective_stages"]
    return f"""# CAP-001 BASE Reference Benchmark

This directory contains a solved, independently validated BASE reference
incumbent. It is calibration evidence, not business input data, a prescribed
implementation, a unique allocation or a globally optimal answer.

## Pinned identity

- Dataset: `BASE` / `{contract['dataset_sha256']}`
- Configuration: `{contract['configuration_version']}` / `{contract['configuration_sha256']}`
- Model version: `{contract['model_version']}`
- Formulation: `{contract['formulation_class']}`
- Method: `{contract['method_classification']}`
- Status: `{contract['status']}`

## Reference controls

- Stage 1 weighted shortage: `{stages[0]['reference_value']:.10g}`
- Stage 1 reproduction ceiling: `{stages[0]['reproduction_upper_bound']:.10g}`
- Stage 2 recursive value and non-capitalised cost: `{stages[1]['reference_value']:.10g}`
- Stage 2 reproduction ceiling: `{stages[1]['reproduction_upper_bound']:.10g}`
- Served quantity: `{metrics['served_quantity']:.10g}` of `{metrics['demand_quantity']:.10g}`
- Service rate: `{metrics['service_rate']:.8%}`
- Independent physical checks: `{contract['independent_validation']['physical']['checked_equations']}`
- Maximum physical residual: `{contract['independent_validation']['physical']['maximum_residual']:.10g}`
- Independent recursive-accounting checks: `{contract['independent_validation']['recursive_accounting']['checked_equations']}`
- Maximum recursive-accounting residual: `{contract['independent_validation']['recursive_accounting']['maximum_residual']:.10g}`

## Required interpretation

`reference_solution.json` retains the complete incumbent decisions and value
state for replay. A candidate must reproduce the published service, accounting
and objective-quality controls under the pinned BASE data and configuration.
The candidate does not have to copy the retained allocation. A different plan
passes when it is independently valid, meets the published objective-quality
rules and explains material aggregate differences.

The reference method is deliberately disclosed as a heuristic: a private
local-fact physical-seed MILP produces an integer plan, then the exact recursive
value equations are solved for that plan. No synthetic intermediate-cost table
is used and no global-optimality claim is made. The `locally_optimal` status
describes the fixed-plan nonlinear value-equation solve; it is not an
optimality claim for the retained allocation.
"""


def planned_files(solution: RecursiveSolution, data: ModelData) -> dict[str, bytes]:
    solution_bytes = canonical_json(solution_bundle_payload(solution)).encode("utf-8")
    contract = _contract(data, solution)
    contract_bytes = canonical_json(contract).encode("utf-8")
    notes_bytes = _notes(contract).encode("utf-8")
    files = {
        SOLUTION_FILE: solution_bytes,
        CONTRACT_FILE: contract_bytes,
        NOTES_FILE: notes_bytes,
    }
    manifest = {
        "benchmark_id": contract["benchmark_id"],
        "benchmark_version": contract["benchmark_version"],
        "dataset_sha256": contract["dataset_sha256"],
        "configuration_sha256": contract["configuration_sha256"],
        "files": {
            name: {"sha256": sha256_bytes(content), "bytes": len(content)}
            for name, content in sorted(files.items())
        },
    }
    files[MANIFEST_FILE] = canonical_json(manifest).encode("utf-8")
    return files


def write_files(files: Mapping[str, bytes]) -> None:
    for root in (PUBLIC_ROOT, PRIVATE_ROOT):
        root.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (root / name).write_bytes(content)


def check_files() -> tuple[str, ...]:
    failures: list[str] = []
    for root in (PUBLIC_ROOT, PRIVATE_ROOT):
        if not root.is_dir():
            failures.append(f"{root}: benchmark directory is missing")
            continue
        if {path.name for path in root.iterdir() if path.is_file()} != set(
            REQUIRED_FILES
        ):
            failures.append(f"{root}: benchmark file set differs")
            continue
        manifest = json.loads((root / MANIFEST_FILE).read_text(encoding="utf-8"))
        for name, record in manifest["files"].items():
            if sha256_path(root / name) != record["sha256"]:
                failures.append(f"{root / name}: hash mismatch")
    if failures:
        return tuple(failures)
    data = load_model_data(DATASET_ROOT / "data")
    solution = read_solution_bundle(PUBLIC_ROOT / SOLUTION_FILE)
    physical = validate_physical_solution(data, solution)
    accounting = validate_recursive_solution(data, solution)
    if not physical.passed:
        failures.append("reference solution fails independent physical validation")
    if not accounting.passed:
        failures.append("reference solution fails independent recursive validation")
    expected = planned_files(solution, data)
    for root in (PUBLIC_ROOT, PRIVATE_ROOT):
        for name, content in expected.items():
            if (root / name).read_bytes() != content:
                failures.append(f"{root / name}: content differs from replay")
    return tuple(failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--refresh-from-retained-solution",
        action="store_true",
        help="revalidate the retained solution and refresh only its publication controls",
    )
    args = parser.parse_args(argv)
    if args.check:
        failures = check_files()
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print("BASE reference benchmark replay and independent validation passed.")
        return 0
    if args.refresh_from_retained_solution:
        data = load_model_data(DATASET_ROOT / "data")
        solution = read_solution_bundle(PRIVATE_ROOT / SOLUTION_FILE)
        physical = validate_physical_solution(data, solution)
        accounting = validate_recursive_solution(data, solution)
        if not physical.passed or not accounting.passed:
            raise RuntimeError(
                "retained solution cannot be republished against the current BASE dataset"
            )
        write_files(planned_files(solution, data))
        print(f"Refreshed validated BASE benchmark controls in {PUBLIC_ROOT}.")
        return 0
    data = load_model_data(DATASET_ROOT / "data")
    solution = solve_reference(data)
    write_files(planned_files(solution, data))
    print(f"Wrote validated BASE reference benchmark to {PUBLIC_ROOT}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
