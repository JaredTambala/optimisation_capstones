"""Tests for deterministic commercial generation and independent assessment."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

from tooling.assess_commercial_data import assess_tables, load_tables
from tooling.contract_runtime import load_config


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "generator" / "generate_commercial_data.py"
NETWORK_DIR = ROOT / "generated" / "network"
SPEC = importlib.util.spec_from_file_location("cap001_commercial_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


def _network():
    return GENERATOR.load_network()


def _candidate():
    return copy.deepcopy(GENERATOR.build_candidate())


def _lineage():
    return json.loads((NETWORK_DIR / "evidence" / "lineage_witnesses.json").read_text())


def _assessment(candidate):
    return assess_tables(
        _network(),
        candidate.tables,
        price_build_up={"rows": candidate.external_price_build_up},
        lineage_witnesses=_lineage(),
    )


def _metric(assessment, metric_id: str):
    return next(metric for metric in assessment.scorecard["metrics"] if metric["metric_id"] == metric_id)


def _issue_codes(assessment) -> set[str]:
    return {issue["code"] for issue in assessment.scorecard["issues"]}


def test_generated_candidate_passes_all_commercial_gates() -> None:
    assessment = _assessment(_candidate())
    assert assessment.passed
    assert assessment.scorecard["issues"] == []
    assert all(metric["passed"] for metric in assessment.scorecard["metrics"])
    assert _metric(assessment, "fixed_variable_crossovers")["value"] >= 4
    assert _metric(assessment, "terminal_witness_coverage")["value"] == 8


def test_written_candidate_conforms_to_eight_contracts(tmp_path: Path) -> None:
    GENERATOR.write_files(tmp_path)
    _, commercial = load_tables(NETWORK_DIR, tmp_path, load_config())
    assert {name: len(rows) for name, rows in commercial.items()} == {
        "supply_contracts.csv": 138,
        "incoterm_rules.csv": 6,
        "import_duty_rates.csv": 138,
        "shipping_lanes.csv": 116,
        "external_source_prices.csv": 396,
        "conversion_costs.csv": 624,
        "cost_allocation_rules.csv": 47,
        "fx_rates.csv": 216,
    }
    assert "pricing_method" not in commercial["supply_contracts.csv"][0]


def test_generation_is_byte_reproducible_and_seed_sensitive() -> None:
    first = GENERATOR.render_files(26022027)
    second = GENERATOR.render_files(26022027)
    changed = GENERATOR.render_files(26022028)
    assert first == second
    assert first["data/incoterm_rules.csv"] == changed["data/incoterm_rules.csv"]
    assert first["data/fx_rates.csv"] != changed["data/fx_rates.csv"]
    assert first["data/conversion_costs.csv"] != changed["data/conversion_costs.csv"]


def test_nonboundary_external_price_is_rejected() -> None:
    candidate = _candidate()
    network = _network()
    nodes = {row["node_id"]: row for row in network["network_nodes.csv"]}
    approvals = {row["approval_id"]: row for row in network["material_flow_approvals.csv"]}
    internal_contract = next(
        row
        for row in candidate.tables["supply_contracts.csv"]
        if not nodes[approvals[row["approval_id"]]["seller_node_id"]]["external_boundary_flag"]
    )
    approval = approvals[internal_contract["approval_id"]]
    extra = copy.deepcopy(candidate.tables["external_source_prices.csv"][0])
    extra.update({"contract_id": internal_contract["contract_id"], "material_id": approval["material_id"]})
    candidate.tables["external_source_prices.csv"].append(extra)
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "NONBOUNDARY_EXTERNAL_PRICE" in _issue_codes(assessment)


def test_missing_contract_and_lane_fail_with_explicit_coverage_issues() -> None:
    candidate = _candidate()
    removed_contract = candidate.tables["supply_contracts.csv"].pop()
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "CONTRACT_COVERAGE" in _issue_codes(assessment)
    assert removed_contract["approval_id"] in assessment.scorecard["issues"][0]["entities"]

    candidate = _candidate()
    removed_lane = next(row for row in candidate.tables["shipping_lanes.csv"] if not row["expedited_flag"])
    pair = (removed_lane["origin_node_id"], removed_lane["destination_node_id"])
    candidate.tables["shipping_lanes.csv"] = [
        row
        for row in candidate.tables["shipping_lanes.csv"]
        if (row["origin_node_id"], row["destination_node_id"]) != pair
    ]
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "LANE_COVERAGE" in _issue_codes(assessment)


def test_cost_rule_tie_and_invalid_markup_base_are_rejected() -> None:
    candidate = _candidate()
    duplicate = copy.deepcopy(candidate.tables["cost_allocation_rules.csv"][0])
    duplicate["cost_rule_id"] = "COST-9999"
    candidate.tables["cost_allocation_rules.csv"].append(duplicate)
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert {"COST_RULE_GLOBAL_COVERAGE", "COST_RULE_PRECEDENCE_TIE"} <= _issue_codes(assessment)

    candidate = _candidate()
    freight = next(row for row in candidate.tables["cost_allocation_rules.csv"] if row["cost_component"] == "FREIGHT")
    freight["markup_eligible_flag"] = True
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "MARKUP_BASE" in _issue_codes(assessment)


def test_missing_duty_and_incompatible_pair_incoterms_are_rejected() -> None:
    candidate = _candidate()
    candidate.tables["import_duty_rates.csv"].pop()
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "DUTY_COVERAGE" in _issue_codes(assessment)

    candidate = _candidate()
    network = _network()
    approvals = {row["approval_id"]: row for row in network["material_flow_approvals.csv"]}
    pairs = {}
    for contract in candidate.tables["supply_contracts.csv"]:
        approval = approvals[contract["approval_id"]]
        pairs.setdefault((approval["seller_node_id"], approval["buyer_node_id"]), []).append(contract)
    shared_pair = next(rows for rows in pairs.values() if len(rows) >= 2)
    shared_pair[0]["incoterm_code"] = "EXW"
    shared_pair[1]["incoterm_code"] = "DDP"
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "PAIR_INCOTERM_CONFLICT" in _issue_codes(assessment)


def test_candidate_does_not_emit_derived_intermediate_costs() -> None:
    assert "baseline_standard_costs.csv" not in _candidate().tables


def test_buyer_borne_cost_embedded_in_boundary_quote_is_rejected() -> None:
    candidate = _candidate()
    terms = {row["incoterm_code"]: row for row in candidate.tables["incoterm_rules.csv"]}
    build_up = next(
        row
        for row in candidate.external_price_build_up
        if terms[row["incoterm_code"]]["buyer_pays_main_carriage"]
    )
    build_up["components_eur_per_unit"]["seller_main_carriage"] = 1.0
    build_up["quoted_unit_price_eur"] += 1.0
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert "SELLER_COMPONENT_DUPLICATION" in _issue_codes(assessment)


def test_removing_fixed_order_differences_removes_required_crossovers() -> None:
    candidate = _candidate()
    for contract in candidate.tables["supply_contracts.csv"]:
        contract["fixed_order_cost"] = 0.0
    assessment = _assessment(candidate)
    assert not assessment.passed
    assert _metric(assessment, "fixed_variable_crossovers")["value"] < 4
