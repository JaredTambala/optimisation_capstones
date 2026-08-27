"""Generate the miniature fixture's derived accounting artefacts.

These comprise the private control-total selector definitions, student-facing
expected-reconciliation files, private reference-solution answer key, and
generated accounting walkthrough.

Mirrors the `build_contract_artifacts.py --check` pattern: `planned_artifacts`
builds an in-memory artefact set from the fixture's own data (never from a
separately-typed answer key), `write_artifacts` writes it, `check_artifacts`
diffs it against disk for drift detection.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, Mapping

from tooling.contract_runtime import canonical_json, load_config, tolerance_pair
from tooling.fixture_reconciler import (
    Indices,
    RUN_ID,
    Valuation,
    capitalised_total,
    ledger_component_total,
    load_fixture_inputs,
    opening_book_value_total,
    value_plan,
)


ROOT = Path(__file__).resolve().parents[1]
STUDENT_FIXTURE_ROOT = ROOT / "student_release/CAP-001-tier-n-release/data/miniature_fixture"
PRIVATE_FIXTURE_ROOT = ROOT / "capstones/CAP-001/miniature_fixture"
STUDENT_WALKTHROUGH = ROOT / "student_release/CAP-001-tier-n-release/reference/miniature_fixture/ACCOUNTING_WALKTHROUGH.md"


def _csv_bytes(header: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(["" if row[c] is None else row[c] for c in header])
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


LEDGER_COMPONENTS = (
    "EXTERNAL_PURCHASE", "FREIGHT", "DUTY", "INSURANCE", "FIXED_ORDER", "FIXED_SHIPMENT",
    "CONVERSION", "SETUP", "OVERHEAD", "SURGE", "MARKUP", "HOLDING", "ACTIVATION", "SHORTAGE",
)


def build_control_total_definitions(valuation: Valuation, idx: Indices, inputs) -> list[dict[str, Any]]:
    """Enumerate every control total mechanically from the resolved fixture
    rather than hand-typing entity IDs — the entities themselves come from
    the authored data, so this stays a faithful, tier-agnostic derivation."""

    definitions: list[dict[str, Any]] = []
    seq = [0]

    def add(description: str, selector: Mapping[str, Any], unit: str, kind: str) -> None:
        seq[0] += 1
        absolute, relative = tolerance_pair(idx.config, kind)
        definitions.append({
            "control_total_id": f"CT-{seq[0]:03d}",
            "description": description,
            "selector": dict(selector),
            "unit": unit,
            "absolute_tolerance": absolute,
            "relative_tolerance": relative,
        })

    boundary_nodes = sorted({
        (node_id, material_id) for (node_id, material_id, period_id) in valuation.pools
        if valuation.pools[(node_id, material_id, period_id)].boundary_quantity > 0
    })
    for node_id, material_id in boundary_nodes:
        period_id = next(p for (n, m, p) in valuation.pools if n == node_id and m == material_id
                          and valuation.pools[(n, m, p)].boundary_quantity > 0)
        selector_base = {"node_id": node_id, "material_id": material_id, "period_id": period_id}
        add(f"{node_id} boundary origination quantity", {"measure": "pool_quantity", **selector_base}, "units", "quantity")
        add(f"{node_id} boundary origination value", {"measure": "pool_value", **selector_base}, "EUR", "value")
        add(f"{node_id} boundary origination unit cost", {"measure": "pool_unit_cost", **selector_base}, "EUR/unit", "unit_cost")

    boundary_node_ids = {n for n, _ in boundary_nodes}
    for leg in sorted(valuation.legs, key=lambda l: l.lane_id):
        if leg.origin_node_id in boundary_node_ids:
            add(f"{leg.lane_id} boundary receipt value ({leg.origin_node_id}->{leg.destination_node_id})",
                {"measure": "leg_receipt_value", "lane_id": leg.lane_id}, "EUR", "value")

    tier3_input_pools = sorted({
        (e.node_id, c.material_id) for e in valuation.transformations for c in e.consumption
        if idx.nodes[e.node_id]["node_tier"] == "TIER_3"
    })
    for node_id, material_id in tier3_input_pools:
        period_id = next(e.period_id for e in valuation.transformations if e.node_id == node_id)
        selector_base = {"node_id": node_id, "material_id": material_id, "period_id": period_id}
        add(f"{node_id} Tier-3 input pool quantity ({material_id})", {"measure": "pool_quantity", **selector_base}, "units", "quantity")
        add(f"{node_id} Tier-3 input pool value ({material_id})", {"measure": "pool_value", **selector_base}, "EUR", "value")
        add(f"{node_id} Tier-3 input pool unit cost ({material_id})", {"measure": "pool_unit_cost", **selector_base}, "EUR/unit", "unit_cost")

    for event in sorted([e for e in valuation.transformations if idx.nodes[e.node_id]["node_tier"] == "TIER_3"], key=lambda e: e.recipe_id):
        selector_base = {"node_id": event.node_id, "material_id": event.output_material_id, "period_id": event.period_id}
        add(f"{event.node_id} Tier-3 transformation output value ({event.recipe_id})", {"measure": "pool_value", **selector_base}, "EUR", "value")
        add(f"{event.node_id} Tier-3 transformation output unit cost ({event.recipe_id})", {"measure": "pool_unit_cost", **selector_base}, "EUR/unit", "unit_cost")

    tier3_node_ids = {n for n in idx.nodes if idx.nodes[n]["node_tier"] == "TIER_3"}
    for leg in sorted(valuation.legs, key=lambda l: l.lane_id):
        if leg.origin_node_id in tier3_node_ids:
            add(f"{leg.lane_id} Tier-3-to-Tier-2 receipt value ({leg.origin_node_id}->{leg.destination_node_id})",
                {"measure": "leg_receipt_value", "lane_id": leg.lane_id}, "EUR", "value")

    tier2_input_pools = sorted({
        (e.node_id, c.material_id) for e in valuation.transformations for c in e.consumption
        if idx.nodes[e.node_id]["node_tier"] == "TIER_2"
    })
    for node_id, material_id in tier2_input_pools:
        period_id = next(e.period_id for e in valuation.transformations if e.node_id == node_id)
        selector_base = {"node_id": node_id, "material_id": material_id, "period_id": period_id}
        add(f"{node_id} Tier-2 input pool quantity ({material_id})", {"measure": "pool_quantity", **selector_base}, "units", "quantity")
        add(f"{node_id} Tier-2 input pool value ({material_id})", {"measure": "pool_value", **selector_base}, "EUR", "value")
        add(f"{node_id} Tier-2 input pool unit cost ({material_id})", {"measure": "pool_unit_cost", **selector_base}, "EUR/unit", "unit_cost")

    for event in sorted([e for e in valuation.transformations if idx.nodes[e.node_id]["node_tier"] == "TIER_2"], key=lambda e: e.recipe_id):
        selector_base = {"node_id": event.node_id, "material_id": event.output_material_id, "period_id": event.period_id}
        add(f"{event.node_id} Tier-2 transformation output value ({event.recipe_id})", {"measure": "pool_value", **selector_base}, "EUR", "value")
        add(f"{event.node_id} Tier-2 transformation output unit cost ({event.recipe_id})", {"measure": "pool_unit_cost", **selector_base}, "EUR/unit", "unit_cost")

    tier2_node_ids = {n for n in idx.nodes if idx.nodes[n]["node_tier"] == "TIER_2"}
    for leg in sorted(valuation.legs, key=lambda l: l.lane_id):
        if leg.origin_node_id in tier2_node_ids:
            add(f"{leg.lane_id} Tier-2-to-plant receipt value ({leg.origin_node_id}->{leg.destination_node_id})",
                {"measure": "leg_receipt_value", "lane_id": leg.lane_id}, "EUR", "value")

    plant_ids = sorted(n for n in idx.nodes if idx.nodes[n]["node_type"] == "PLANT")
    first_demand_period = min(p for (_, _, p), row in idx.terminal_demand.items() if row["demand_quantity"] > 0)
    plant_material = next(m for (n, m, p) in idx.terminal_demand if p == first_demand_period)
    for plant_id in plant_ids:
        selector_base = {"node_id": plant_id, "material_id": plant_material, "period_id": first_demand_period}
        add(f"{plant_id} plant pool quantity", {"measure": "pool_quantity", **selector_base}, "units", "quantity")
        add(f"{plant_id} plant pool value", {"measure": "pool_value", **selector_base}, "EUR", "value")
        add(f"{plant_id} plant pool unit cost", {"measure": "pool_unit_cost", **selector_base}, "EUR/unit", "unit_cost")

    demand_periods = sorted({p for (n, m, p) in valuation.pools if n in plant_ids and valuation.pools[(n, m, p)].served_quantity > 0})
    for plant_id in plant_ids:
        for period_id in demand_periods:
            add(f"{plant_id} served value at {period_id}",
                {"measure": "served_value", "node_id": plant_id, "material_id": plant_material, "period_id": period_id},
                "EUR", "value")
        add(f"{plant_id} total served value across all demand periods",
            {"measure": "served_value_total", "node_id": plant_id, "material_id": plant_material}, "EUR", "value")

    last_period = valuation.periods[-1]
    terminal_closing_pools = sorted(
        (n, m) for (n, m, p) in valuation.pools if p == last_period and valuation.pools[(n, m, p)].closing_value > 0
    )
    for node_id, material_id in terminal_closing_pools:
        add(f"{node_id} terminal-period closing inventory value ({material_id})",
            {"measure": "closing_value", "node_id": node_id, "material_id": material_id, "period_id": last_period},
            "EUR", "value")

    for component in LEDGER_COMPONENTS:
        add(f"Ledger total for {component}", {"measure": "ledger_component_total", "component": component}, "EUR", "value")

    add("Total served value across all plants and demand periods", {"measure": "served_value_total_all"}, "EUR", "value")
    add("Total terminal-period closing inventory value across all nodes", {"measure": "terminal_closing_total"}, "EUR", "value")
    add("Total non-capitalised cost (HOLDING + ACTIVATION + SHORTAGE)", {"measure": "noncapitalised_total"}, "EUR", "value")
    add("Stage-2 value before non-capitalised cost", {"measure": "stage_2_value"}, "EUR", "value")
    add("Value-conservation identity: total capitalised cost plus opening book value",
        {"measure": "capitalised_plus_opening_total"}, "EUR", "value")

    return definitions


def _evaluate_all(valuation: Valuation, definitions: list[Mapping[str, Any]], inputs) -> list[dict[str, Any]]:
    from tooling.fixture_reconciler import evaluate_selector

    rows = []
    for definition in definitions:
        selector = definition["selector"]
        if selector["measure"] == "served_value_total_all":
            recomputed = sum(p.served_value for p in valuation.pools.values())
        elif selector["measure"] == "capitalised_plus_opening_total":
            recomputed = capitalised_total(valuation) + opening_book_value_total(inputs)
        else:
            recomputed = evaluate_selector(valuation, selector, inputs)
        rows.append({
            "control_total_id": definition["control_total_id"],
            "description": definition["description"],
            "expected_value": round(recomputed, 7),
            "unit": definition["unit"],
            "absolute_tolerance": definition["absolute_tolerance"],
            "relative_tolerance": definition["relative_tolerance"],
        })
    return rows


def planned_artifacts(data_dir: Path | None = None) -> dict[Path, bytes]:
    config = load_config()
    if data_dir is None:
        data_dir = STUDENT_FIXTURE_ROOT / "inputs"
    inputs = load_fixture_inputs(data_dir, config)
    idx = Indices(inputs)
    valuation = value_plan(inputs)
    definitions = build_control_total_definitions(valuation, idx, inputs)
    control_total_rows = _evaluate_all(valuation, definitions, inputs)
    control_totals_header = ["control_total_id", "description", "expected_value", "unit", "absolute_tolerance", "relative_tolerance"]

    artifacts: dict[Path, bytes] = {}
    control_totals_csv = _csv_bytes(control_totals_header, control_total_rows)

    artifacts[STUDENT_FIXTURE_ROOT / "fixture_control_totals.csv"] = control_totals_csv
    artifacts[STUDENT_FIXTURE_ROOT / "expected_reconciliation/fixture_control_totals.csv"] = control_totals_csv
    artifacts[PRIVATE_FIXTURE_ROOT / "fixture_control_totals.csv"] = control_totals_csv
    artifacts[PRIVATE_FIXTURE_ROOT / "expected_reconciliation/fixture_control_totals.csv"] = control_totals_csv
    artifacts[PRIVATE_FIXTURE_ROOT / "control_total_definitions.json"] = _json_bytes(definitions)

    # Private reference_solution answer key for verify-mode (claimed-solution checking).
    artifacts.update(_reference_solution_artifacts(valuation, idx))
    artifacts[STUDENT_WALKTHROUGH] = _accounting_walkthrough(valuation, idx, control_total_rows)
    return artifacts


def _reference_solution_artifacts(valuation: Valuation, idx: Indices) -> dict[Path, bytes]:
    inv_header = [
        "node_id", "material_id", "period_id", "opening_quantity_units", "opening_value_eur",
        "receipt_value_eur", "production_value_eur", "pool_quantity_units", "pool_value_eur",
        "pool_unit_cost_eur_per_unit", "outflow_value_eur", "closing_quantity_units", "closing_value_eur",
    ]
    inv_rows = []
    for key in sorted(valuation.pools):
        p = valuation.pools[key]
        outflow_value = sum(c.value for c in p.consumption) + sum(l.origin_unit_cost * l.quantity for l in p.dispatch_legs) + p.served_value
        inv_rows.append({
            "node_id": p.node_id, "material_id": p.material_id, "period_id": p.period_id,
            "opening_quantity_units": round(p.opening_quantity, 7), "opening_value_eur": round(p.opening_value, 7),
            "receipt_value_eur": round(sum(l.receipt_value for l in p.receipt_legs) + p.boundary_value, 7),
            "production_value_eur": round(sum(e.output_value for e in p.production_events), 7),
            "pool_quantity_units": round(p.pool_quantity, 7), "pool_value_eur": round(p.pool_value, 7),
            "pool_unit_cost_eur_per_unit": round(p.unit_cost, 7), "outflow_value_eur": round(outflow_value, 7),
            "closing_quantity_units": round(p.closing_quantity, 7), "closing_value_eur": round(p.closing_value, 7),
        })

    prod_header = ["recipe_id", "node_id", "period_id", "output_material_id", "output_quantity_units",
                   "input_value_eur", "conversion_eur", "setup_eur", "overhead_eur", "markup_rate", "markup_eur", "output_value_eur"]
    prod_rows = [{
        "recipe_id": e.recipe_id, "node_id": e.node_id, "period_id": e.period_id,
        "output_material_id": e.output_material_id, "output_quantity_units": round(e.output_quantity, 7),
        "input_value_eur": round(e.input_value, 7), "conversion_eur": round(e.conversion_eur, 7),
        "setup_eur": round(e.setup_eur, 7), "overhead_eur": round(e.overhead_eur, 7),
        "markup_rate": e.markup_rate, "markup_eur": round(e.markup_eur, 7), "output_value_eur": round(e.output_value, 7),
    } for e in sorted(valuation.transformations, key=lambda e: (e.period_id, e.recipe_id))]

    ship_header = ["lane_id", "approval_id", "contract_id", "origin_node_id", "destination_node_id", "material_id",
                   "dispatch_period_id", "arrival_period_id", "quantity_units", "dispatched_value_eur",
                   "freight_eur", "duty_eur", "insurance_eur", "fixed_shipment_eur", "fixed_order_eur", "receipt_value_eur"]
    ship_rows = [{
        "lane_id": l.lane_id, "approval_id": l.approval_id, "contract_id": l.contract_id,
        "origin_node_id": l.origin_node_id, "destination_node_id": l.destination_node_id, "material_id": l.material_id,
        "dispatch_period_id": l.dispatch_period_id, "arrival_period_id": l.arrival_period_id,
        "quantity_units": round(l.quantity, 7), "dispatched_value_eur": round(l.dispatched_value, 7),
        "freight_eur": round(l.freight_eur, 7), "duty_eur": round(l.duty_eur, 7), "insurance_eur": round(l.insurance_eur, 7),
        "fixed_shipment_eur": round(l.fixed_shipment_eur, 7), "fixed_order_eur": round(l.fixed_order_eur, 7),
        "receipt_value_eur": round(l.receipt_value, 7),
    } for l in sorted(valuation.legs, key=lambda l: (l.dispatch_period_id, l.lane_id))]

    demand_header = ["plant_id", "material_id", "period_id", "demand_quantity_units", "served_quantity_units",
                     "served_value_eur", "unit_cost_eur_per_unit", "closing_quantity_units", "closing_value_eur"]
    demand_rows = []
    for key in sorted(valuation.pools):
        p = valuation.pools[key]
        if idx.nodes[p.node_id]["node_type"] != "PLANT":
            continue
        demand_row = idx.terminal_demand.get(key)
        demand_rows.append({
            "plant_id": p.node_id, "material_id": p.material_id, "period_id": p.period_id,
            "demand_quantity_units": demand_row["demand_quantity"] if demand_row else 0.0,
            "served_quantity_units": round(p.served_quantity, 7), "served_value_eur": round(p.served_value, 7),
            "unit_cost_eur_per_unit": round(p.unit_cost, 7), "closing_quantity_units": round(p.closing_quantity, 7),
            "closing_value_eur": round(p.closing_value, 7),
        })

    base = PRIVATE_FIXTURE_ROOT / "reference_solution"
    return {
        base / "inventory_cost_rollforward.csv": _csv_bytes(inv_header, inv_rows),
        base / "production.csv": _csv_bytes(prod_header, prod_rows),
        base / "shipments.csv": _csv_bytes(ship_header, ship_rows),
        base / "demand_service.csv": _csv_bytes(demand_header, demand_rows),
    }


def _accounting_walkthrough(valuation: Valuation, idx: Indices, control_total_rows: list[dict[str, Any]]) -> bytes:
    lines: list[str] = []
    lines.append("# CAP-001 Miniature Fixture — Accounting Walkthrough")
    lines.append("")
    lines.append(
        "Generated from the authored fixture by `python -m tooling.build_fixture_reconciliation`. "
        "Do not edit directly — every number here is the reconciler's own recomputed output."
    )
    lines.append("")
    lines.append("## 1. Purpose and how to use it")
    lines.append("")
    lines.append(
        "This fixture is the miniature, fully hand-checkable proof that weighted-average pooling, "
        "transformation valuation and receipt capitalisation work before you attempt the full recursive "
        "model. Run `python -m tooling.validate_fixture` against the supplied raw fixture-input directory "
        "before moving on to the full dataset. This command validates and revalues the input fixture; it is "
        "not a validator for submitted model-output files."
    )
    lines.append("")
    lines.append("## 2. What the fixture is")
    lines.append("")
    lines.append(
        "Five periods (P01–P05), three supplier tiers (Tier 4, Tier 3, Tier 2) plus three Asterion plants, "
        "connected by fifteen approved arcs. Sourcing, transformation output and dispatch quantities are all "
        "pinned by data (matched minimum-order-quantity, order-multiple and lane-capacity fields, and "
        "zero-storage fan-out origins), so the fixture has exactly one feasible physical realisation — it is "
        "an accounting oracle, not an optimisation exercise."
    )
    lines.append("")
    lines.append("## 3. Which inputs carry signal")
    lines.append("")
    lines.append(
        "`network_nodes`, `materials`, `transformation_recipes`, `transformation_inputs`, "
        "`material_flow_approvals`, `supply_contracts`, `shipping_lanes`, `external_source_prices`, "
        "`source_capacity`, `transformation_capacity`, `conversion_costs`, `cost_allocation_rules`, "
        "`inventory_policies`, `opening_inventory`, `terminal_demand`, `incoterm_rules`, `import_duty_rates` "
        "and `fx_rates` all directly determine a control total. `supplier_organisations`, "
        "`supplier_performance_history`, `incident_history`, `disruption_scenarios`, `disruption_impacts`, "
        "and `plants` are present because every raw contract must exist for the fixture to validate, but none "
        "of their fields feed the BASE reconciliation — `disruption_impacts` "
        "in particular describes an inactive stress scenario, not BASE."
    )
    lines.append("")
    lines.append("## 4. The accounting rules, in dependency order")
    lines.append("")
    lines.append("4.1 Pool grain is `(node_id, material_id, period_id)`.")
    lines.append("4.2 Opening inventory enters the pool at its book value, exactly as configured.")
    lines.append("4.3 Quantity roll-forward: `pool_quantity = opening + receipts + production`.")
    lines.append("4.4 Value roll-forward: `pool_value = opening_value + receipt_value + production_value`.")
    lines.append(
        "4.5 Weighted-average unit cost: `pool_value = unit_cost * pool_quantity`; when `pool_quantity = 0`, "
        "`unit_cost` is fixed to exactly `0`, never left undefined."
    )
    lines.append(
        "4.6 Common-outflow-cost rule: every outflow from a pool in a period — closing inventory, dispatch, "
        "consumption, service — uses that pool's one unit cost. No outflow may be priced differently from "
        "another leaving the same pool."
    )
    lines.append(
        "4.7 Receipt valuation: `receipt_value = dispatched_value + freight + duty + insurance + fixed_shipment "
        "+ fixed_order`, where each addition is included only if its cost-allocation rule is capitalised AND "
        "(for freight/fixed-shipment/duty/insurance) the arc's Incoterm makes the buyer responsible for it."
    )
    lines.append(
        "4.8 Transformation valuation: markup is applied once, to the eligible base (input value plus "
        "conversion, setup and overhead where each is marked markup-eligible) — never to freight, duty, "
        "insurance or fixed costs, which already entered the pool upstream and re-enter only via input value."
    )
    lines.append("4.9 Closing inventory retains value at every node, not only at plants.")
    lines.append(
        "4.10 Stage-2 assembly: `stage_2_value = total served value across every plant and demand period + "
        "total closing inventory value at every node in the terminal period + non-capitalised cost (zero here)`."
    )
    lines.append("")
    lines.append("## 5. The worked walk-through")
    lines.append("")
    lines.append("| Control total | Value |")
    lines.append("|---|---:|")
    for row in control_total_rows:
        lines.append(f"| {row['description']} | {row['unit']} {row['expected_value']:.7f} |" if isinstance(row['expected_value'], float) else f"| {row['description']} | {row['unit']} {row['expected_value']} |")
    lines.append("")
    lines.append("## 6. The reconciliation identities and tolerance convention")
    lines.append("")
    lines.append(
        "Every identity in §4 is checked with `tolerance = max(absolute, relative * max(|lhs|, |rhs|))`, "
        "using the absolute/relative pairs in the configuration's `tolerances` block "
        "(quantity 1e-5 / 1e-7, value 1e-3 / 1e-7, unit cost 1e-5 / 1e-7). The strongest single check is "
        "value conservation: total capitalised cost injected across the whole network plus opening book "
        "value must equal total served value plus total terminal closing value, exactly."
    )
    lines.append("")
    lines.append("## 7. Nine ways this goes wrong")
    lines.append("")
    lines.append(
        "- **Omitted cost** — a capitalised addition (freight, duty, fixed order, fixed shipment) is dropped "
        "from a receipt. Caught by the receipt-value identity, and propagates into every downstream pool."
    )
    lines.append(
        "- **Double count** — a cost already capitalised upstream is capitalised again downstream. Caught "
        "by pool value conservation."
    )
    lines.append(
        "- **Wrong markup base** — a receipt-stage cost is wrongly marked markup-eligible, or a transformation "
        "cost wrongly excluded. Caught by the transformation-value identity."
    )
    lines.append(
        "- **Inconsistent outflow cost** — two outflows from the same pool in the same period are priced "
        "differently. Caught by the common-outflow-cost identity."
    )
    lines.append(
        "- **Value loss** — a closing value is understated with no matching outflow to explain the gap. "
        "Caught by pool value conservation."
    )
    lines.append(
        "- **Artificial dilution** — a pool's quantity is inflated without matching value, to depress its "
        "unit cost. Caught by the bilinear unit-cost identity together with quantity roll-forward."
    )
    lines.append(
        "- **Zero-pool error** — a pool with zero quantity is left with nonzero value. Caught by the "
        "zero-pool-value identity."
    )
    lines.append(
        "- **Infeasible flow** — an approval is suspended, breaking a required physical path. The engine "
        "raises an error rather than silently reporting a wrong number."
    )
    lines.append(
        "- **Deliberate shortage** — terminal demand exceeds the quantity available at a plant. Caught by "
        "the published plant-service control total because served quantity and value fall below BASE."
    )
    lines.append("")
    lines.append("## 8. Validate the fixture inputs")
    lines.append("")
    lines.append(
        "Run `python -m tooling.validate_fixture --data-dir <fixture-input-directory>`. The directory must "
        "contain all 25 raw fixture CSVs. The command reconstructs the reference valuation and compares it "
        "with the published reconciliation artefacts. Claimed model-output validation is a separate control "
        "and is not implemented by this command."
    )
    lines.append("")
    lines.append("## 9. What is deliberately not here")
    lines.append("")
    lines.append(
        "No main-case reference results, private bounds, objective ranges, generator seeds or solver "
        "settings appear anywhere in this document or in the fixture's student-visible files. Absence here "
        "is by design, not oversight."
    )
    lines.append("")
    lines.append("## 10. Provenance")
    lines.append("")
    lines.append(f"Generated from configuration version `{idx.config['configuration_version']}`. Do not edit directly.")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def write_artifacts(artifacts: Mapping[Path, bytes]) -> None:
    for path, content in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def check_artifacts(artifacts: Mapping[Path, bytes]) -> list[str]:
    errors = []
    for path, expected in artifacts.items():
        if not path.exists():
            errors.append(f"missing generated artefact: {path}")
            continue
        actual = path.read_bytes()
        if actual != expected:
            errors.append(f"generated artefact drifted: {path}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    artifacts = planned_artifacts(args.data_dir)
    if args.check:
        errors = check_artifacts(artifacts)
        if errors:
            for error in errors:
                print(error, file=__import__("sys").stderr)
            return 1
        print(f"Fixture-derived artefacts are current ({len(artifacts)} files).")
        return 0
    write_artifacts(artifacts)
    print(f"Generated {len(artifacts)} fixture-derived artefacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
