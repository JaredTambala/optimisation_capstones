from __future__ import annotations

import copy
import csv
import json
import shutil
import time
from pathlib import Path

import pytest

from tooling.contract_runtime import ContractError, load_config, tolerance_pair, within_tolerance
from tooling.build_fixture_reconciliation import (
    PRIVATE_FIXTURE_ROOT,
    STUDENT_FIXTURE_ROOT,
    _evaluate_all,
    build_control_total_definitions,
    check_artifacts,
    planned_artifacts,
)
from tooling.fixture_reconciler import (
    EQUATION_FAMILIES,
    Indices,
    identity_rows,
    load_fixture_inputs,
    value_plan,
)
from tooling.validate_fixture import validate_fixture


FIXTURE_INPUTS = STUDENT_FIXTURE_ROOT / "inputs"
NEGATIVE_VARIANTS_ROOT = PRIVATE_FIXTURE_ROOT / "negative_variants"
INPUT_VARIANT_SLUGS = ("omitted-cost", "wrong-markup-base", "zero-pool-error", "infeasible-flow", "deliberate-shortage")
CLAIMED_VARIANT_SLUGS = ("double-count", "inconsistent-outflow-cost", "value-loss", "artificial-dilution")
ALL_VARIANT_SLUGS = INPUT_VARIANT_SLUGS + CLAIMED_VARIANT_SLUGS


# --------------------------------------------------------------------------- main fixture


def test_fixture_inputs_validate_and_are_read_only() -> None:
    config = load_config()
    from tooling.contract_runtime import validate_raw_data_directory

    counts = validate_raw_data_directory(FIXTURE_INPUTS, config)
    assert len(counts) == 25
    assert sum(counts.values()) == 336


def test_fixture_manifest_matches_disk() -> None:
    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    idx = Indices(inputs)
    manifest = json.loads((STUDENT_FIXTURE_ROOT / "fixture_manifest.json").read_bytes())
    assert manifest["period_count"] == 5 == len(idx.periods)
    supplier_tiers = {idx.nodes[n]["node_tier"] for n in idx.nodes if idx.nodes[n]["node_type"] == "SUPPLIER_SITE"}
    assert supplier_tiers == {"TIER_4", "TIER_3", "TIER_2"}
    assert manifest["supplier_tier_count"] == 3 == len(supplier_tiers)


def test_published_control_totals_are_reproduced() -> None:
    """The published control totals are decimal roundings of non-terminating
    rationals (e.g. 410*... /... yields 5.1714286), so exact equality is
    arithmetically impossible, not merely inconvenient. within_tolerance
    reads config["tolerances"] rather than inventing its own margin, so the
    tolerance stays a controlled, ADR-governed value."""

    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    idx = Indices(inputs)
    valuation = value_plan(inputs)
    definitions = build_control_total_definitions(valuation, idx, inputs)
    recomputed = {r["control_total_id"]: r for r in _evaluate_all(valuation, definitions, inputs)}

    with (STUDENT_FIXTURE_ROOT / "expected_reconciliation/fixture_control_totals.csv").open(newline="", encoding="utf-8") as handle:
        published = {row["control_total_id"]: row for row in csv.DictReader(handle)}

    assert set(recomputed) == set(published)
    mismatched = []
    for control_total_id, row in recomputed.items():
        expected_value = float(published[control_total_id]["expected_value"])
        if not within_tolerance(row["expected_value"], expected_value, row["absolute_tolerance"], row["relative_tolerance"]):
            mismatched.append((control_total_id, row["expected_value"], expected_value))
    assert mismatched == []


HEADLINE_TOTALS = (
    ("CT-022", 150.0, "quantity"),
    ("CT-023", 402.0, "value"),
    ("CT-024", 2.68, "unit_cost"),
    ("CT-035", 540.0, "value"),
    ("CT-084", 33.8, "value"),
    ("CT-057", 5.1714286, "unit_cost"),
    ("CT-058", 1122.0, "value"),
    ("CT-060", 731.5, "value"),
    ("CT-085", 32.0, "value"),
    ("CT-068", 20.1, "unit_cost"),
    ("CT-071", 20.675, "unit_cost"),
    ("CT-074", 22.1, "unit_cost"),
    ("CT-101", 2073.0, "value"),
    ("CT-102", 166.3, "value"),
    ("CT-104", 2239.3, "value"),
)


def test_headline_totals_match_delivery_plan() -> None:
    """Spot-check the 15 headline figures published in
    CAP-001_DELIVERY_AND_ASSESSMENT_PLAN.md's miniature-fixture acceptance
    section directly, independent of the generated fixture_control_totals.csv
    file."""

    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    idx = Indices(inputs)
    valuation = value_plan(inputs)
    definitions = build_control_total_definitions(valuation, idx, inputs)
    recomputed = {r["control_total_id"]: r for r in _evaluate_all(valuation, definitions, inputs)}
    for control_total_id, expected_value, kind in HEADLINE_TOTALS:
        absolute, relative = tolerance_pair(config, kind)
        actual = recomputed[control_total_id]["expected_value"]
        assert within_tolerance(actual, expected_value, absolute, relative), (control_total_id, actual, expected_value)


def test_value_conservation_identity_holds() -> None:
    """The single strongest acceptance check: total capitalised cost injected
    plus opening book value must equal total served value plus total
    terminal closing value, exactly. Checked independently of the
    fixture_control_totals.csv file so it cannot be defeated by a stale or
    miscomputed expected-value row."""

    from tooling.fixture_reconciler import capitalised_total, opening_book_value_total

    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    valuation = value_plan(inputs)
    last_period = valuation.periods[-1]
    served_total = sum(p.served_value for p in valuation.pools.values())
    terminal_closing_total = sum(p.closing_value for p in valuation.pools.values() if p.period_id == last_period)
    lhs = capitalised_total(valuation) + opening_book_value_total(inputs)
    rhs = served_total + terminal_closing_total
    absolute, relative = tolerance_pair(config, "value")
    assert within_tolerance(lhs, rhs, absolute, relative)
    assert within_tolerance(rhs, 2239.3, absolute, relative)


def test_every_reconciliation_row_passes() -> None:
    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    valuation = value_plan(inputs)
    rows = identity_rows(valuation, config, inputs)
    failing = [r["equation_id"] for r in rows if not r["pass_flag"]]
    assert failing == []


def test_reconciliation_coverage_is_complete() -> None:
    """Guards against a reconciler that 'passes' only by emitting nothing."""

    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    valuation = value_plan(inputs)
    rows = identity_rows(valuation, config, inputs)
    assert len(rows) > 600
    families_present = {r["equation_family"] for r in rows}
    assert families_present == set(EQUATION_FAMILIES)


def test_generated_fixture_artifacts_are_current() -> None:
    assert check_artifacts(planned_artifacts()) == []


def test_walkthrough_matches_fixture_validator_scope() -> None:
    walkthrough = (
        STUDENT_FIXTURE_ROOT.parent.parent
        / "reference/miniature_fixture/ACCOUNTING_WALKTHROUGH.md"
    ).read_text(encoding="utf-8")
    assert "## 7. Nine ways this goes wrong" in walkthrough
    assert "**Deliberate shortage**" in walkthrough
    assert "--data-dir <fixture-input-directory>" in walkthrough
    assert "not implemented by this command" in walkthrough


def test_full_fixture_validation_passes() -> None:
    summary = validate_fixture(FIXTURE_INPUTS)
    assert summary["control_totals"] == 105
    assert summary["max_absolute_residual"] < 1e-6


def test_fixture_reconciles_within_runtime_budget() -> None:
    config = load_config()
    budget = config["runtime_budgets"]["miniature_fixture_seconds"]
    start = time.perf_counter()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    valuation = value_plan(inputs)
    identity_rows(valuation, config, inputs)
    elapsed = time.perf_counter() - start
    assert elapsed < budget
    # Deterministic work-proxy: the real regression guard against an
    # accidental complexity blow-up, with zero timing flake. Observed count
    # at implementation time was well under 400; 2000 gives ample headroom.
    assert valuation.operation_count < 2000


# --------------------------------------------------------------------------- negative variants


def _load_manifest(slug: str) -> dict:
    return json.loads((NEGATIVE_VARIANTS_ROOT / slug / "variant_manifest.json").read_bytes())


def _materialise_mutated_inputs(tmp_path: Path, mutation: dict) -> Path:
    target_dir = tmp_path / "inputs"
    shutil.copytree(FIXTURE_INPUTS, target_dir)
    file_path = target_dir / mutation["file"]
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        rows = list(reader)
    matched = 0
    for row in rows:
        if all(row[key] == value for key, value in mutation["match"].items()):
            row[mutation["column"]] = mutation["new_value"]
            matched += 1
    assert matched == 1, f"expected exactly one matching row for {mutation}, found {matched}"
    with file_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    return target_dir


@pytest.mark.parametrize("slug", INPUT_VARIANT_SLUGS)
def test_input_negative_variant_fails_for_intended_reason(slug: str, tmp_path: Path) -> None:
    manifest = _load_manifest(slug)
    config = load_config()
    mutated_dir = _materialise_mutated_inputs(tmp_path, manifest["mutation"])
    detection = manifest["expected_detection"]

    if detection["channel"] == "STRUCTURAL_REJECTION":
        with pytest.raises(ContractError, match=detection["message_contains"]):
            inputs = load_fixture_inputs(mutated_dir, config)
            value_plan(inputs)
        return

    inputs = load_fixture_inputs(mutated_dir, config)
    valuation = value_plan(inputs)

    if detection["channel"] == "CONTROL_TOTAL":
        idx = Indices(inputs)
        definitions = build_control_total_definitions(valuation, idx, inputs)
        recomputed = {r["control_total_id"]: r for r in _evaluate_all(valuation, definitions, inputs)}
        with (STUDENT_FIXTURE_ROOT / "expected_reconciliation/fixture_control_totals.csv").open(newline="", encoding="utf-8") as handle:
            published = {row["control_total_id"]: row for row in csv.DictReader(handle)}
        control_total_id = detection["primary_control_total_id"]
        actual = recomputed[control_total_id]["expected_value"]
        expected = float(published[control_total_id]["expected_value"])
        residual = abs(actual - expected)
        assert residual >= detection["min_absolute_residual"], (
            f"{slug}: expected a material divergence at {control_total_id}, got residual {residual}"
        )
        return

    if detection["channel"] == "INTERNAL_INVARIANT":
        rows = identity_rows(valuation, config, inputs)
        failing_by_family = {}
        for row in rows:
            if not row["pass_flag"]:
                failing_by_family.setdefault(row["equation_family"], []).append(row)
        for family in detection["equation_families"]:
            assert family in failing_by_family, f"{slug}: expected {family} to fail, but it passed"
            worst = max(r["absolute_residual"] for r in failing_by_family[family])
            assert worst >= detection["min_absolute_residual"]
        return

    raise AssertionError(f"unsupported detection channel: {detection['channel']}")


def _mutate_claimed_valuation(valuation, mutation: dict):
    mutated = copy.deepcopy(valuation)
    if "pool_key" in mutation:
        key = tuple(mutation["pool_key"])
        pool = mutated.pools[key]
        if "delta_from_leg_receipt_value" in mutation:
            leg = next(l for l in mutated.legs if l.lane_id == mutation["delta_from_leg_receipt_value"])
            pool.pool_value += leg.receipt_value
        else:
            setattr(pool, mutation["field"], mutation["new_value"])
    elif "leg_lane_id" in mutation:
        leg = next(l for l in mutated.legs if l.lane_id == mutation["leg_lane_id"])
        setattr(leg, mutation["field"], mutation["new_value"])
    else:
        raise AssertionError(f"unsupported claimed-solution mutation shape: {mutation}")
    return mutated


@pytest.mark.parametrize("slug", CLAIMED_VARIANT_SLUGS)
def test_claimed_negative_variant_fails_for_intended_reason(slug: str) -> None:
    """These four classes describe a claimed/submitted solution that is
    internally inconsistent, not a bad input file — a from-scratch
    recomputation is invariant to them by construction, so they are tested
    by mutating the resolved Valuation directly (the same object a claimed-
    solution loader would produce) and re-running identity_rows against it."""

    manifest = _load_manifest(slug)
    config = load_config()
    inputs = load_fixture_inputs(FIXTURE_INPUTS, config)
    valuation = value_plan(inputs)
    mutated = _mutate_claimed_valuation(valuation, manifest["mutation"])
    rows = identity_rows(mutated, config, inputs)

    detection = manifest["expected_detection"]
    assert detection["channel"] == "INTERNAL_INVARIANT"
    failing_by_family: dict[str, list] = {}
    for row in rows:
        if not row["pass_flag"]:
            failing_by_family.setdefault(row["equation_family"], []).append(row)
    for family in detection["equation_families"]:
        assert family in failing_by_family, f"{slug}: expected {family} to fail, but it passed"
        worst = max(r["absolute_residual"] for r in failing_by_family[family])
        assert worst >= detection["min_absolute_residual"]


def test_all_nine_failure_classes_are_covered() -> None:
    manifests = [_load_manifest(slug) for slug in ALL_VARIANT_SLUGS]
    failure_classes = {m["failure_class"] for m in manifests}
    assert failure_classes == {
        "OMITTED_COST", "DOUBLE_COUNT", "WRONG_MARKUP_BASE", "INCONSISTENT_OUTFLOW_COST",
        "VALUE_LOSS", "ARTIFICIAL_DILUTION", "ZERO_POOL_ERROR", "INFEASIBLE_FLOW", "DELIBERATE_SHORTAGE",
    }
    assert len(manifests) == 9
