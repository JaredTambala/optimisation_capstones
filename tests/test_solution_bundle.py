from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest

from cap001_model.physical_seed import build_physical_seed_model, solve_physical_seed
from cap001_model.data import load_model_data
from cap001_model.recursive import build_recursive_model, solve_recursive_for_physical_plan
from cap001_model.recursive_validation import validate_recursive_solution
from cap001_model.solution_bundle import (
    read_solution_bundle,
    solution_bundle_payload,
    write_solution_bundle,
)
from cap001_model.validation import validate_physical_solution


FIXTURE_INPUTS = Path("capstones/CAP-001/miniature_fixture/inputs")


def _canonical_solution():
    data = load_model_data(FIXTURE_INPUTS)
    physical = solve_physical_seed(build_physical_seed_model(data))
    solution = solve_recursive_for_physical_plan(
        build_recursive_model(data), physical
    )
    return data, solution


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_solution_bundle_round_trip_needs_no_live_model(tmp_path: Path) -> None:
    data, solution = _canonical_solution()
    path = tmp_path / "recursive_solution.json"
    write_solution_bundle(path, solution)
    loaded = read_solution_bundle(path)

    assert "pyomo" not in inspect.getsource(read_solution_bundle)
    assert loaded == solution
    assert validate_physical_solution(data, loaded).passed
    assert validate_recursive_solution(data, loaded).passed


def test_solution_bundle_corruption_fails_for_the_intended_reason(
    tmp_path: Path,
) -> None:
    data, solution = _canonical_solution()
    original = solution_bundle_payload(solution)

    quantity_payload = copy.deepcopy(original)
    quantity_payload["decisions"]["shipments"][0]["quantity"] += 1.0
    quantity_path = tmp_path / "bad_quantity.json"
    _write_payload(quantity_path, quantity_payload)
    quantity_result = validate_physical_solution(
        data, read_solution_bundle(quantity_path)
    )
    assert any(
        violation.rule in {"ORDER_MULTIPLE", "POOL_QUANTITY_BALANCE"}
        for violation in quantity_result.violations
    )

    value_payload = copy.deepcopy(original)
    value_payload["decisions"]["pool_value"][0]["value_eur"] += 1.0
    value_path = tmp_path / "bad_value.json"
    _write_payload(value_path, value_payload)
    value_result = validate_recursive_solution(data, read_solution_bundle(value_path))
    assert any(
        violation.rule in {"POOL_UNIT_COST", "POOL_VALUE_ROLLFORWARD"}
        for violation in value_result.violations
    )

    unit_cost_payload = copy.deepcopy(original)
    active_pool = next(
        row
        for row in unit_cost_payload["decisions"]["unit_cost"]
        if row["value_eur_per_unit"] > 0
    )
    active_pool["value_eur_per_unit"] += 1.0
    unit_cost_path = tmp_path / "bad_unit_cost.json"
    _write_payload(unit_cost_path, unit_cost_payload)
    unit_cost_result = validate_recursive_solution(
        data, read_solution_bundle(unit_cost_path)
    )
    assert any(
        violation.rule == "POOL_UNIT_COST"
        for violation in unit_cost_result.violations
    )

    status_payload = copy.deepcopy(original)
    status_payload["status"] = "invented_success"
    status_path = tmp_path / "bad_status.json"
    _write_payload(status_path, status_payload)
    with pytest.raises(ValueError, match="metadata is invalid"):
        read_solution_bundle(status_path)
