"""Tests for structural network generation and independent assessment."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

from tooling.assess_network_structure import assess_tables, load_tables
from tooling.contract_runtime import load_config


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "generator" / "generate_network.py"
SPEC = importlib.util.spec_from_file_location("cap001_network_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


def _dataset():
    return copy.deepcopy(GENERATOR.build_dataset())


def _metric(assessment, metric_id: str):
    return next(metric for metric in assessment.scorecard["metrics"] if metric["metric_id"] == metric_id)


def _issue_codes(assessment) -> set[str]:
    return {issue["code"] for issue in assessment.scorecard["issues"]}


def test_generated_network_passes_all_depth_gates() -> None:
    assessment = assess_tables(_dataset())
    assert assessment.passed
    assert assessment.scorecard["issues"] == []
    assert all(metric["passed"] for metric in assessment.scorecard["metrics"])
    participation = assessment.lineage_witnesses["participation_index"]["entities"]
    assert all(terminals for entity_type in participation.values() for terminals in entity_type.values())


def test_written_network_conforms_to_all_seven_contracts(tmp_path: Path) -> None:
    GENERATOR.write_files(tmp_path)
    tables = load_tables(tmp_path / "data", load_config())
    assert {name: len(rows) for name, rows in tables.items()} == {
        "supplier_organisations.csv": 22,
        "network_nodes.csv": 38,
        "plants.csv": 4,
        "materials.csv": 36,
        "transformation_recipes.csv": 52,
        "transformation_inputs.csv": 67,
        "material_flow_approvals.csv": 138,
    }


def test_generation_is_byte_reproducible_and_seed_sensitive() -> None:
    first = GENERATOR.render_files(17012027)
    second = GENERATOR.render_files(17012027)
    changed = GENERATOR.render_files(17012028)
    assert first == second
    assert first["data/materials.csv"] == changed["data/materials.csv"]
    assert first["data/network_nodes.csv"] != changed["data/network_nodes.csv"]
    assert first["data/transformation_recipes.csv"] != changed["data/transformation_recipes.csv"]


def test_cycle_is_rejected() -> None:
    tables = _dataset()
    original = tables["material_flow_approvals.csv"][0]
    reversed_approval = copy.deepcopy(original)
    reversed_approval["approval_id"] = "APR-99999"
    reversed_approval["seller_node_id"], reversed_approval["buyer_node_id"] = (
        original["buyer_node_id"],
        original["seller_node_id"],
    )
    tables["material_flow_approvals.csv"].append(reversed_approval)
    assessment = assess_tables(tables)
    assert not assessment.passed
    assert {"APPROVAL_DIRECTION", "NODE_CYCLE", "STATE_CYCLE"} <= _issue_codes(assessment)


def test_orphan_material_is_rejected() -> None:
    tables = _dataset()
    orphan = copy.deepcopy(tables["materials.csv"][12])
    orphan["material_id"] = "MAT-9999"
    orphan["material_name"] = "Unconnected Processed Material"
    tables["materials.csv"].append(orphan)
    assessment = assess_tables(tables)
    assert not assessment.passed
    assert "MAT-9999" in _metric(assessment, "orphan_entities")["failures"]


def test_terminal_without_plant_receipts_fails_full_lineage_gate() -> None:
    tables = _dataset()
    nodes = {row["node_id"]: row for row in tables["network_nodes.csv"]}
    tables["material_flow_approvals.csv"] = [
        row
        for row in tables["material_flow_approvals.csv"]
        if not (row["material_id"] == "MAT-0029" and nodes[row["buyer_node_id"]]["node_tier"] == "PLANT")
    ]
    assessment = assess_tables(tables)
    assert not assessment.passed
    assert "MAT-0029" in _metric(assessment, "full_lineage_coverage")["failures"]


def test_duplicate_rows_do_not_create_superficial_multi_sourcing() -> None:
    tables = _dataset()
    duplicate = copy.deepcopy(tables["material_flow_approvals.csv"][0])
    duplicate["approval_id"] = "APR-99999"
    tables["material_flow_approvals.csv"].append(duplicate)
    assessment = assess_tables(tables)
    assert not assessment.passed
    assert "DUPLICATE_APPROVAL" in _issue_codes(assessment)
    assert not _metric(assessment, "duplicate_approvals")["passed"]


def test_share_caps_can_cover_every_receiving_pool() -> None:
    tables = _dataset()
    approvals_by_pool = {}
    for approval in tables["material_flow_approvals.csv"]:
        approvals_by_pool.setdefault((approval["buyer_node_id"], approval["material_id"]), []).append(approval)
    for approvals in approvals_by_pool.values():
        available_share = sum(
            approval["maximum_approved_share"] if approval["maximum_approved_share"] is not None else 1.0
            for approval in approvals
        )
        assert available_share >= 1.0
        if len(approvals) == 1:
            assert approvals[0]["maximum_approved_share"] is None


def test_inadequate_share_cap_is_rejected() -> None:
    tables = _dataset()
    pool_counts = {}
    for approval in tables["material_flow_approvals.csv"]:
        pool = (approval["buyer_node_id"], approval["material_id"])
        pool_counts[pool] = pool_counts.get(pool, 0) + 1
    single_source = next(
        approval
        for approval in tables["material_flow_approvals.csv"]
        if pool_counts[(approval["buyer_node_id"], approval["material_id"])] == 1
    )
    single_source["maximum_approved_share"] = 0.75
    assessment = assess_tables(tables)
    assert not assessment.passed
    assert "APPROVAL_SHARE_CAP" in _issue_codes(assessment)
