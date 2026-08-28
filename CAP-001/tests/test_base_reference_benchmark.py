from __future__ import annotations

import json

from tooling.build_base_reference_benchmark import (
    CONTRACT_FILE,
    PRIVATE_ROOT,
    PUBLIC_ROOT,
    REQUIRED_FILES,
    check_files,
)


def test_base_reference_benchmark_replays_and_validates_independently() -> None:
    assert check_files() == ()


def test_public_and_private_benchmark_copies_are_identical() -> None:
    assert {path.name for path in PUBLIC_ROOT.iterdir()} == set(REQUIRED_FILES)
    assert {path.name for path in PRIVATE_ROOT.iterdir()} == set(REQUIRED_FILES)
    for name in REQUIRED_FILES:
        assert (PUBLIC_ROOT / name).read_bytes() == (PRIVATE_ROOT / name).read_bytes()


def test_benchmark_is_calibration_evidence_not_model_input_or_exact_answer() -> None:
    contract = json.loads((PUBLIC_ROOT / CONTRACT_FILE).read_text(encoding="utf-8"))
    assert contract["dataset_id"] == "BASE"
    assert contract["method_classification"] == "HEURISTIC"
    assert contract["global_optimality_claimed"] is False
    assert contract["allocation_uniqueness_claimed"] is False
    assert contract["exact_allocation_match_required"] is False
    assert contract["solution_is_model_input"] is False
    assert contract["independent_validation"]["physical"]["passed"] is True
    assert (
        contract["independent_validation"]["recursive_accounting"]["passed"]
        is True
    )
    assert len(contract["objective_stages"]) == 2
    assert all(
        stage["reproduction_upper_bound"] >= stage["reference_value"]
        for stage in contract["objective_stages"]
    )
