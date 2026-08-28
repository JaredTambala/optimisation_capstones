"""Deterministic serialization for independently validated solver results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from cap001_model.contracts import (
    FormulationClass,
    MethodClassification,
    ObjectiveStageResult,
    SolutionStatus,
    SolverEvidence,
)
from cap001_model.recursive import RecursiveSolution


_FORMAT_VERSION = "1.0.0"
_LAYOUTS = {
    "source_supply": (("node_id", "material_id", "period_id"), "quantity"),
    "source_regular": (("node_id", "material_id", "period_id"), "quantity"),
    "source_surge": (("node_id", "material_id", "period_id"), "quantity"),
    "shipments": (("route_id",), "quantity"),
    "shipment_active": (("route_id",), "value"),
    "shipment_lots": (("route_id",), "value"),
    "contract_active": (("contract_id",), "value"),
    "production": (("recipe_id", "period_id"), "quantity"),
    "production_regular": (("recipe_id", "period_id"), "quantity"),
    "production_surge": (("recipe_id", "period_id"), "quantity"),
    "production_active": (("recipe_id", "period_id"), "value"),
    "closing_inventory": (("node_id", "material_id", "period_id"), "quantity"),
    "served": (("node_id", "material_id", "period_id"), "quantity"),
    "shortage": (("node_id", "material_id", "period_id"), "quantity"),
    "pool_quantity": (("node_id", "material_id", "period_id"), "quantity"),
    "pool_value": (("node_id", "material_id", "period_id"), "value_eur"),
    "unit_cost": (
        ("node_id", "material_id", "period_id"),
        "value_eur_per_unit",
    ),
    "closing_value": (("node_id", "material_id", "period_id"), "value_eur"),
    "served_value": (("node_id", "material_id", "period_id"), "value_eur"),
    "shipment_dispatch_value": (("route_id",), "value_eur"),
    "shipment_receipt_value": (("route_id",), "value_eur"),
    "production_input_value": (
        ("recipe_id", "material_id", "period_id"),
        "value_eur",
    ),
    "production_output_value": (("recipe_id", "period_id"), "value_eur"),
}


def _encode_mapping(
    values: Mapping[Any, float], key_fields: tuple[str, ...], value_field: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_key, value in sorted(values.items()):
        key = raw_key if isinstance(raw_key, tuple) else (raw_key,)
        if len(key) != len(key_fields):
            raise ValueError(f"invalid key {raw_key!r} for {key_fields}")
        row = dict(zip(key_fields, key, strict=True))
        row[value_field] = float(value)
        rows.append(row)
    return rows


def _decode_mapping(
    rows: Any, key_fields: tuple[str, ...], value_field: str, section: str
) -> dict[Any, float]:
    if not isinstance(rows, list):
        raise ValueError(f"{section} must be an array")
    expected_fields = set(key_fields) | {value_field}
    values: dict[Any, float] = {}
    for position, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != expected_fields:
            raise ValueError(f"{section}[{position}] has invalid fields")
        parts = tuple(str(row[field]) for field in key_fields)
        key: Any = parts[0] if len(parts) == 1 else parts
        if key in values:
            raise ValueError(f"{section} contains duplicate key {key!r}")
        try:
            values[key] = float(row[value_field])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{section}[{position}].{value_field} is not numeric"
            ) from exc
    return values


def _evidence_to_dict(evidence: SolverEvidence) -> dict[str, Any]:
    return {
        "solver_name": evidence.solver_name,
        "solver_version": evidence.solver_version,
        "status": evidence.status.value,
        "raw_termination_condition": evidence.raw_termination_condition,
        "termination_message": evidence.termination_message,
        "runtime_seconds": evidence.runtime_seconds,
        "incumbent_objective": evidence.incumbent_objective,
        "best_bound": evidence.best_bound,
        "absolute_gap": evidence.absolute_gap,
        "relative_gap": evidence.relative_gap,
        "iteration_or_node_count": evidence.iteration_or_node_count,
    }


def _evidence_from_dict(value: Any, position: int) -> SolverEvidence:
    if not isinstance(value, dict):
        raise ValueError(f"solver_evidence[{position}] must be an object")
    try:
        return SolverEvidence(
            solver_name=str(value["solver_name"]),
            solver_version=(
                None
                if value["solver_version"] is None
                else str(value["solver_version"])
            ),
            status=SolutionStatus(value["status"]),
            raw_termination_condition=str(value["raw_termination_condition"]),
            termination_message=str(value["termination_message"]),
            runtime_seconds=float(value["runtime_seconds"]),
            incumbent_objective=(
                None
                if value["incumbent_objective"] is None
                else float(value["incumbent_objective"])
            ),
            best_bound=(
                None if value["best_bound"] is None else float(value["best_bound"])
            ),
            absolute_gap=(
                None
                if value["absolute_gap"] is None
                else float(value["absolute_gap"])
            ),
            relative_gap=(
                None
                if value["relative_gap"] is None
                else float(value["relative_gap"])
            ),
            iteration_or_node_count=(
                None
                if value["iteration_or_node_count"] is None
                else int(value["iteration_or_node_count"])
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"solver_evidence[{position}] is invalid: {exc}") from exc


def solution_bundle_payload(solution: RecursiveSolution) -> dict[str, Any]:
    """Create a stable plain-data representation with no model references."""

    stages = [
        {
            "stage": stage.stage,
            "name": stage.name,
            "objective_value": stage.objective_value,
            "lock_tolerance": stage.lock_tolerance,
            "evidence_index": position,
        }
        for position, stage in enumerate(solution.stages)
    ]
    decisions = {
        name: _encode_mapping(getattr(solution, name), key_fields, value_field)
        for name, (key_fields, value_field) in _LAYOUTS.items()
    }
    return {
        "format_version": _FORMAT_VERSION,
        "status": solution.status.value,
        "formulation_class": solution.formulation_class.value,
        "method_classification": solution.method_classification.value,
        "method_description": solution.method_description,
        "stages": stages,
        "solver_evidence": [
            _evidence_to_dict(evidence) for evidence in solution.solver_evidence
        ],
        "decisions": decisions,
    }


def write_solution_bundle(path: Path, solution: RecursiveSolution) -> None:
    """Write a deterministic result bundle suitable for a fresh-process check."""

    payload = solution_bundle_payload(solution)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_solution_bundle(path: Path) -> RecursiveSolution:
    """Load a result bundle without constructing or importing a Pyomo model."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load solution bundle {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("format_version") != _FORMAT_VERSION:
        raise ValueError("unsupported or missing solution bundle format_version")
    decisions = payload.get("decisions")
    if not isinstance(decisions, dict) or set(decisions) != set(_LAYOUTS):
        raise ValueError("solution bundle decision sections are incomplete or unknown")
    evidence = tuple(
        _evidence_from_dict(value, position)
        for position, value in enumerate(payload.get("solver_evidence", []))
    )
    if not evidence:
        raise ValueError("solution bundle has no solver evidence")
    stages: list[ObjectiveStageResult] = []
    try:
        for value in payload["stages"]:
            evidence_index = int(value["evidence_index"])
            stages.append(
                ObjectiveStageResult(
                    stage=int(value["stage"]),
                    name=str(value["name"]),
                    objective_value=float(value["objective_value"]),
                    lock_tolerance=float(value["lock_tolerance"]),
                    evidence=evidence[evidence_index],
                )
            )
        status = SolutionStatus(payload["status"])
        formulation = FormulationClass(payload["formulation_class"])
        classification = MethodClassification(payload["method_classification"])
        description = str(payload["method_description"])
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"solution bundle metadata is invalid: {exc}") from exc
    decoded = {
        name: _decode_mapping(decisions[name], key_fields, value_field, name)
        for name, (key_fields, value_field) in _LAYOUTS.items()
    }
    return RecursiveSolution(
        status=status,
        formulation_class=formulation,
        method_classification=classification,
        method_description=description,
        stages=tuple(stages),
        solver_evidence=evidence,
        **decoded,
    )
