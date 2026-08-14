"""Independently validate that the CAP-001 miniature fixture reconciles.

Mirrors `tooling/validate_wp1.py`'s pattern: an ordered sequence of checks,
each raising `ContractError` on failure, run via `python -m
tooling.validate_fixture`.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from tooling.contract_runtime import ContractError, load_config, tolerance_pair, within_tolerance
from tooling.build_fixture_reconciliation import (
    PRIVATE_FIXTURE_ROOT,
    STUDENT_FIXTURE_ROOT,
    _evaluate_all,
    build_control_total_definitions,
)
from tooling.fixture_reconciler import (
    Indices,
    capitalised_total,
    identity_rows,
    load_fixture_inputs,
    opening_book_value_total,
    value_plan,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_fixture(data_dir: Path | None = None) -> dict[str, Any]:
    config = load_config()
    inputs_dir = data_dir if data_dir is not None else STUDENT_FIXTURE_ROOT / "inputs"

    inputs = load_fixture_inputs(inputs_dir, config)
    idx = Indices(inputs)
    valuation = value_plan(inputs)

    # 1. Fixture manifest matches disk.
    import json

    manifest = json.loads((STUDENT_FIXTURE_ROOT / "fixture_manifest.json").read_bytes())
    _require(manifest["period_count"] == len(idx.periods), "fixture_manifest period_count does not match planning_calendar")
    supplier_tiers = {idx.nodes[n]["node_tier"] for n in idx.nodes if idx.nodes[n]["node_type"] == "SUPPLIER_SITE"}
    _require(
        manifest["supplier_tier_count"] == len(supplier_tiers),
        f"fixture_manifest supplier_tier_count {manifest['supplier_tier_count']} != distinct supplier tiers {supplier_tiers}",
    )

    # 2. Check global value conservation before any finer-grained accounting
    # identity or published control total.
    last_period = valuation.periods[-1]
    capitalised_plus_opening = capitalised_total(valuation) + opening_book_value_total(inputs)
    served_plus_terminal_closing = (
        sum(pool.served_value for pool in valuation.pools.values())
        + sum(
            pool.closing_value
            for pool in valuation.pools.values()
            if pool.period_id == last_period
        )
    )
    value_absolute, value_relative = tolerance_pair(config, "value")
    _require(
        within_tolerance(
            capitalised_plus_opening,
            served_plus_terminal_closing,
            value_absolute,
            value_relative,
        ),
        "value conservation failed: capitalised cost plus opening book value "
        f"{capitalised_plus_opening} != served value plus terminal closing value "
        f"{served_plus_terminal_closing}",
    )

    # 3. Every finer-grained reconciliation identity passes.
    rows = identity_rows(valuation, config, inputs)
    failing = [r["equation_id"] for r in rows if not r["pass_flag"]]
    _require(not failing, f"reconciliation identities failed: {failing}")

    # 4. Recomputed control totals match the published expected values.
    definitions = build_control_total_definitions(valuation, idx, inputs)
    recomputed_rows = {r["control_total_id"]: r for r in _evaluate_all(valuation, definitions, inputs)}
    expected_rows = {
        r["control_total_id"]: r
        for r in _read_csv(STUDENT_FIXTURE_ROOT / "expected_reconciliation/fixture_control_totals.csv")
    }
    _require(set(recomputed_rows) == set(expected_rows), "control-total ID set differs from the published file")
    mismatched = []
    for control_total_id, recomputed in recomputed_rows.items():
        published = expected_rows[control_total_id]
        if not within_tolerance(
            recomputed["expected_value"], float(published["expected_value"]),
            recomputed["absolute_tolerance"], recomputed["relative_tolerance"],
        ):
            mismatched.append((control_total_id, recomputed["expected_value"], published["expected_value"]))
    _require(not mismatched, f"control totals diverged from published values: {mismatched}")

    stage_2 = next(r for r in recomputed_rows.values() if r["description"].startswith("Stage-2 value"))
    conservation = next(r for r in recomputed_rows.values() if r["description"].startswith("Value-conservation identity"))
    _require(
        within_tolerance(
            stage_2["expected_value"],
            conservation["expected_value"],
            value_absolute,
            value_relative,
        ),
        "value-conservation identity does not equal the Stage-2 total",
    )

    return {
        "raw_rows": sum(len(rows_) for rows_ in inputs.tables.values()),
        "pools": len(valuation.pools),
        "active_pools": len([p for p in valuation.pools.values() if p.pool_quantity > 0]),
        "transformations": len(valuation.transformations),
        "shipment_legs": len(valuation.legs),
        "equation_rows": len(rows),
        "control_totals": len(recomputed_rows),
        "max_absolute_residual": max((r["absolute_residual"] for r in rows), default=0.0),
        "stage_2_value": served_plus_terminal_closing,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        summary = validate_fixture(args.data_dir)
    except (ContractError, OSError, ValueError) as exc:
        print(f"Fixture validation failed: {exc}", file=__import__("sys").stderr)
        return 1
    print("Fixture validation passed:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
