"""Validate and profile the generated CAP-001 structural network."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tooling.contract_runtime import (
    canonical_json,
    coerce_csv_value,
    load_config,
    sha256_path,
    validate_csv_file,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NETWORK_DIR = ROOT / "generated" / "network"
STRUCTURAL_FILES = (
    "supplier_organisations.csv",
    "network_nodes.csv",
    "plants.csv",
    "materials.csv",
    "transformation_recipes.csv",
    "transformation_inputs.csv",
    "material_flow_approvals.csv",
)
TIER_RANK = {"TIER_4": 4, "TIER_3": 3, "TIER_2": 2, "TIER_1": 1, "PLANT": 0}
TIER_OUTPUT_STAGE = {
    "TIER_4": "BOUNDARY_RAW",
    "TIER_3": "PROCESSED",
    "TIER_2": "SUBASSEMBLY",
    "TIER_1": "TERMINAL",
}
EXPECTED_RECIPE_INPUT_STAGE = {
    "TIER_3": "BOUNDARY_RAW",
    "TIER_2": "PROCESSED",
    "TIER_1": "SUBASSEMBLY",
}


@dataclass(frozen=True)
class Assessment:
    scorecard: dict[str, Any]
    lineage_witnesses: dict[str, Any]
    dependency_witnesses: dict[str, Any]
    report: str
    diagram: str

    @property
    def passed(self) -> bool:
        return self.scorecard["status"] == "PASS"


def _issue(issues: list[dict[str, Any]], code: str, message: str, entities: Iterable[str] = ()) -> None:
    issues.append({"code": code, "message": message, "entities": sorted(set(entities))})


def load_tables(data_dir: Path, config: Mapping[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    if config is None:
        config = load_config()
    tables: dict[str, list[dict[str, Any]]] = {}
    for file_name in STRUCTURAL_FILES:
        path = data_dir / file_name
        validate_csv_file(path, config["raw_contracts"][file_name])
        fields = config["raw_contracts"][file_name]["columns"]
        fields_by_name = {field["name"]: field for field in fields}
        with path.open(newline="", encoding="utf-8") as handle:
            rows = []
            for row in csv.DictReader(handle):
                rows.append({name: coerce_csv_value(value, fields_by_name[name]) for name, value in row.items()})
        tables[file_name] = rows
    return tables


def _duplicates(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> list[str]:
    values = [tuple(row[field] for field in fields) for row in rows]
    counts = Counter(values)
    return ["/".join(str(part) for part in value) for value, count in counts.items() if count > 1]


def _find_cycle(adjacency: Mapping[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        if node in visiting:
            start = stack.index(node)
            return [*stack[start:], node]
        if node in visited:
            return []
        visiting.add(node)
        stack.append(node)
        for child in sorted(adjacency.get(node, set())):
            cycle = visit(child)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return []

    for node in sorted(set(adjacency) | {child for children in adjacency.values() for child in children}):
        cycle = visit(node)
        if cycle:
            return cycle
    return []


def _components(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> list[list[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    remaining = set(nodes)
    components: list[list[str]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        component: set[str] = set()
        while queue:
            node = queue.popleft()
            if node in component:
                continue
            component.add(node)
            queue.extend(sorted(adjacency.get(node, set()) - component))
        remaining -= component
        components.append(sorted(component))
    return sorted(components, key=lambda item: (-len(item), item))


def _ultimate_group(supplier: str, parents: Mapping[str, str | None]) -> str:
    seen: set[str] = set()
    current = supplier
    while parents.get(current) is not None and current not in seen:
        seen.add(current)
        current = parents[current] or current
    return current


def _collect_derivation_nodes(derivation: Mapping[str, Any]) -> set[str]:
    nodes = {derivation["node_id"]} if "node_id" in derivation else set()
    if "seller_node_id" in derivation:
        nodes.add(derivation["seller_node_id"])
    if "buyer_node_id" in derivation:
        nodes.add(derivation["buyer_node_id"])
    for child in derivation.get("inputs", []):
        nodes.update(_collect_derivation_nodes(child))
    if "source" in derivation:
        nodes.update(_collect_derivation_nodes(derivation["source"]))
    return nodes


def _metric(
    metric_id: str,
    label: str,
    value: int | float,
    threshold: str,
    passed: bool,
    *,
    numerator: int | float | None = None,
    denominator: int | float | None = None,
    witnesses: Iterable[str] = (),
    failures: Iterable[str] = (),
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "metric_id": metric_id,
        "label": label,
        "value": value,
        "threshold": threshold,
        "passed": passed,
        "witnesses": sorted(set(witnesses)),
        "failures": sorted(set(failures)),
    }
    if numerator is not None:
        result["numerator"] = numerator
    if denominator is not None:
        result["denominator"] = denominator
    return result


def assess_tables(
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    config: Mapping[str, Any] | None = None,
    data_checksums: Mapping[str, str] | None = None,
) -> Assessment:
    if config is None:
        config = load_config()
    issues: list[dict[str, Any]] = []
    organisations = list(tables["supplier_organisations.csv"])
    nodes = list(tables["network_nodes.csv"])
    plants = list(tables["plants.csv"])
    materials = list(tables["materials.csv"])
    recipes = list(tables["transformation_recipes.csv"])
    recipe_inputs = list(tables["transformation_inputs.csv"])
    approvals = list(tables["material_flow_approvals.csv"])

    primary_keys = {
        "supplier_organisations.csv": (organisations, ("supplier_id",)),
        "network_nodes.csv": (nodes, ("node_id",)),
        "plants.csv": (plants, ("plant_id",)),
        "materials.csv": (materials, ("material_id",)),
        "transformation_recipes.csv": (recipes, ("recipe_id",)),
        "transformation_inputs.csv": (recipe_inputs, ("recipe_id", "input_sequence")),
        "material_flow_approvals.csv": (approvals, ("approval_id",)),
    }
    for file_name, (rows, fields) in primary_keys.items():
        duplicate_keys = _duplicates(rows, fields)
        if duplicate_keys:
            _issue(issues, "DUPLICATE_PRIMARY_KEY", f"{file_name} contains duplicate primary keys", duplicate_keys)

    org_by_id = {row["supplier_id"]: row for row in organisations}
    node_by_id = {row["node_id"]: row for row in nodes}
    material_by_id = {row["material_id"]: row for row in materials}
    plant_by_id = {row["plant_id"]: row for row in plants}
    inputs_by_recipe: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in recipe_inputs:
        inputs_by_recipe[row["recipe_id"]].append(row)

    for organisation in organisations:
        parent = organisation["parent_group_id"]
        if parent is not None and parent not in org_by_id:
            _issue(issues, "UNKNOWN_PARENT_GROUP", "Supplier parent does not exist", [organisation["supplier_id"], parent])
        if parent == organisation["supplier_id"]:
            _issue(issues, "SELF_PARENT", "Supplier cannot be its own parent", [parent])
    parent_adjacency: dict[str, set[str]] = defaultdict(set)
    for organisation in organisations:
        if organisation["parent_group_id"] in org_by_id:
            parent_adjacency[organisation["supplier_id"]].add(organisation["parent_group_id"])
    parent_cycle = _find_cycle(parent_adjacency)
    if parent_cycle:
        _issue(issues, "PARENT_CYCLE", "Supplier parent hierarchy contains a cycle", parent_cycle)

    expected_plant_names = {row["name"] for row in config["business"]["plants"]}
    actual_plant_names = {row["plant_name"] for row in plants}
    if actual_plant_names != expected_plant_names or len(plants) != 4:
        _issue(issues, "PLANT_SET", "The four controlled plants are not represented exactly", actual_plant_names ^ expected_plant_names)

    active_nodes = [row for row in nodes if row["active_flag"]]
    active_orgs = [row for row in organisations if row["active_flag"]]
    active_materials = [row for row in materials if row["active_flag"]]
    active_recipes = [row for row in recipes if row["active_flag"]]
    active_node_ids = {row["node_id"] for row in active_nodes}
    active_material_ids = {row["material_id"] for row in active_materials}
    active_recipe_ids = {row["recipe_id"] for row in active_recipes}
    active_approvals = [
        row for row in approvals
        if row["approval_status"] == "APPROVED" and row["valid_from_period"] <= "P12" and row["valid_to_period"] >= "P01"
    ]

    target_scale = config["network"]["target_scale"]
    for tier, scale_key in (("TIER_1", "tier_1_nodes"), ("TIER_2", "tier_2_nodes"), ("TIER_3", "tier_3_nodes"), ("TIER_4", "tier_4_nodes")):
        count = sum(row["node_tier"] == tier for row in active_nodes)
        limits = target_scale[scale_key]
        if not limits["minimum"] <= count <= limits["maximum"]:
            _issue(issues, "TIER_SCALE", f"{tier} node count {count} is outside {limits['minimum']}–{limits['maximum']}", [tier])
    scale_counts = {
        "supplier_organisations": len(active_orgs),
        "materials": len(active_materials),
        "terminal_materials": sum(row["terminal_material_flag"] for row in active_materials),
        "recipes": len(active_recipes),
        "approvals": len(approvals),
    }
    for scale_key, count in scale_counts.items():
        limits = target_scale[scale_key]
        if not limits["minimum"] <= count <= limits["maximum"]:
            _issue(issues, "ENTITY_SCALE", f"{scale_key} count {count} is outside {limits['minimum']}–{limits['maximum']}", [scale_key])

    for node in nodes:
        supplier = node["supplier_id"]
        if node["node_type"] == "PLANT":
            if supplier is not None or node["node_tier"] != "PLANT" or node["processing_capability_flag"] or node["external_boundary_flag"]:
                _issue(issues, "PLANT_NODE_SEMANTICS", "Plant-node flags are inconsistent", [node["node_id"]])
            if node["node_id"] not in plant_by_id:
                _issue(issues, "PLANT_ROW_MISSING", "Plant node lacks a plants.csv row", [node["node_id"]])
        else:
            if supplier not in org_by_id:
                _issue(issues, "NODE_OWNER", "Supplier node has no valid owner", [node["node_id"], str(supplier)])
            if node["node_tier"] == "PLANT":
                _issue(issues, "SUPPLIER_TIER", "Supplier site is marked as a plant", [node["node_id"]])
            expected_boundary = node["node_tier"] == "TIER_4"
            expected_processing = node["node_tier"] in {"TIER_3", "TIER_2", "TIER_1"}
            if node["external_boundary_flag"] != expected_boundary or node["processing_capability_flag"] != expected_processing:
                _issue(issues, "NODE_CAPABILITY", "Node boundary or processing capability is inconsistent with its tier", [node["node_id"]])
    for plant in plants:
        node = node_by_id.get(plant["plant_id"])
        if node is None or node["node_type"] != "PLANT" or node["node_name"] != plant["plant_name"]:
            _issue(issues, "PLANT_NODE_LINK", "Plant row does not resolve to its matching plant node", [plant["plant_id"]])

    for material in materials:
        terminal = material["material_stage"] == "TERMINAL"
        boundary = material["material_stage"] == "BOUNDARY_RAW"
        if material["terminal_material_flag"] != terminal:
            _issue(issues, "TERMINAL_FLAG", "Terminal flag does not match material stage", [material["material_id"]])
        if material["external_price_eligible_flag"] != boundary:
            _issue(issues, "EXTERNAL_PRICE_FLAG", "External-price eligibility does not match the boundary stage", [material["material_id"]])
        if material["material_stage"] == "PLANT_READY":
            _issue(issues, "PLANT_READY_RESERVED", "PLANT_READY is reserved and must not be instantiated", [material["material_id"]])

    group_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    recipe_material_adjacency: dict[str, set[str]] = defaultdict(set)
    for recipe in active_recipes:
        node = node_by_id.get(recipe["node_id"])
        output = material_by_id.get(recipe["output_material_id"])
        recipe_id = recipe["recipe_id"]
        input_rows = sorted(inputs_by_recipe.get(recipe_id, []), key=lambda row: row["input_sequence"])
        if node is None or node["node_id"] not in active_node_ids or not node["processing_capability_flag"]:
            _issue(issues, "RECIPE_NODE", "Recipe does not resolve to an active processing node", [recipe_id, recipe["node_id"]])
            continue
        if output is None or output["material_id"] not in active_material_ids:
            _issue(issues, "RECIPE_OUTPUT", "Recipe output does not resolve to an active material", [recipe_id, recipe["output_material_id"]])
            continue
        expected_output = TIER_OUTPUT_STAGE.get(node["node_tier"])
        if output["material_stage"] != expected_output:
            _issue(issues, "RECIPE_OUTPUT_STAGE", "Recipe output stage is inconsistent with its node tier", [recipe_id])
        if not input_rows:
            _issue(issues, "RECIPE_INPUT_MISSING", "Active recipe has no inputs", [recipe_id])
        sequences = [row["input_sequence"] for row in input_rows]
        if sequences != list(range(1, len(input_rows) + 1)):
            _issue(issues, "INPUT_SEQUENCE", "Recipe input sequence is not contiguous from one", [recipe_id])
        for input_row in input_rows:
            input_material = material_by_id.get(input_row["input_material_id"])
            if input_material is None or input_material["material_id"] not in active_material_ids:
                _issue(issues, "RECIPE_INPUT", "Recipe input does not resolve to an active material", [recipe_id, input_row["input_material_id"]])
                continue
            if input_material["material_stage"] != EXPECTED_RECIPE_INPUT_STAGE[node["node_tier"]]:
                _issue(issues, "RECIPE_INPUT_STAGE", "Recipe input stage is inconsistent with its node tier", [recipe_id, input_material["material_id"]])
            recipe_material_adjacency[input_material["material_id"]].add(output["material_id"])
        if recipe["recipe_group_id"] is not None:
            group_rows[recipe["recipe_group_id"]].append(recipe)

    for group_id, rows in group_rows.items():
        node_outputs = {(row["node_id"], row["output_material_id"]) for row in rows}
        modes = {row["activation_mode"] for row in rows}
        if len(rows) < 2 or len(node_outputs) != 1 or len(modes) != 1:
            _issue(issues, "RECIPE_GROUP", "Alternative recipe group must contain at least two consistent alternatives", [group_id])

    recipe_cycle = _find_cycle(recipe_material_adjacency)
    if recipe_cycle:
        _issue(issues, "RECIPE_CYCLE", "Material recipe dependencies contain a cycle", recipe_cycle)

    approved_triples = _duplicates(active_approvals, ("seller_node_id", "buyer_node_id", "material_id"))
    if approved_triples:
        _issue(issues, "DUPLICATE_APPROVAL", "Usable seller/buyer/material approvals are duplicated", approved_triples)

    node_adjacency: dict[str, set[str]] = defaultdict(set)
    state_adjacency: dict[str, set[str]] = defaultdict(set)
    shorter_approvals: list[Mapping[str, Any]] = []
    for approval in active_approvals:
        seller = node_by_id.get(approval["seller_node_id"])
        buyer = node_by_id.get(approval["buyer_node_id"])
        material = material_by_id.get(approval["material_id"])
        if seller is None or buyer is None or material is None:
            _issue(issues, "APPROVAL_REFERENCE", "Approval contains an unknown node or material", [approval["approval_id"]])
            continue
        if seller["node_id"] not in active_node_ids or buyer["node_id"] not in active_node_ids or material["material_id"] not in active_material_ids:
            _issue(issues, "APPROVAL_INACTIVE_REFERENCE", "Usable approval references an inactive entity", [approval["approval_id"]])
        rank_difference = TIER_RANK[seller["node_tier"]] - TIER_RANK[buyer["node_tier"]]
        if rank_difference <= 0:
            _issue(issues, "APPROVAL_DIRECTION", "Approval does not move strictly downstream", [approval["approval_id"]])
        elif rank_difference > 1:
            shorter_approvals.append(approval)
        expected_stage = TIER_OUTPUT_STAGE.get(seller["node_tier"])
        if material["material_stage"] != expected_stage:
            _issue(issues, "APPROVAL_MATERIAL_STAGE", "Approval material is inconsistent with its seller tier", [approval["approval_id"]])
        node_adjacency[seller["node_id"]].add(buyer["node_id"])
        seller_state = f"{seller['node_id']}|{material['material_id']}"
        buyer_state = f"{buyer['node_id']}|{material['material_id']}"
        state_adjacency[seller_state].add(buyer_state)
    node_cycle = _find_cycle(node_adjacency)
    if node_cycle:
        _issue(issues, "NODE_CYCLE", "Approved node graph contains a cycle", node_cycle)
    for recipe in active_recipes:
        output_state = f"{recipe['node_id']}|{recipe['output_material_id']}"
        for input_row in inputs_by_recipe.get(recipe["recipe_id"], []):
            state_adjacency[f"{recipe['node_id']}|{input_row['input_material_id']}"] .add(output_state)
    state_cycle = _find_cycle(state_adjacency)
    if state_cycle:
        _issue(issues, "STATE_CYCLE", "Node/material state graph contains a cycle", state_cycle)

    approval_by_transition: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    approvals_by_seller_state: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    approvals_by_buyer_state: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in active_approvals:
        transition = (approval["seller_node_id"], approval["buyer_node_id"], approval["material_id"])
        approval_by_transition[transition] = approval
        approvals_by_seller_state[(approval["seller_node_id"], approval["material_id"])].append(approval)
        approvals_by_buyer_state[(approval["buyer_node_id"], approval["material_id"])].append(approval)

    reachable: set[tuple[str, str]] = set()
    provenance: dict[tuple[str, str], dict[str, Any]] = {}
    for approval in active_approvals:
        seller = node_by_id.get(approval["seller_node_id"])
        material = material_by_id.get(approval["material_id"])
        if seller and material and seller["node_tier"] == "TIER_4" and material["external_price_eligible_flag"]:
            state = (seller["node_id"], material["material_id"])
            reachable.add(state)
            provenance.setdefault(state, {"kind": "boundary", "node_id": state[0], "material_id": state[1]})

    changed = True
    while changed:
        changed = False
        for approval in sorted(active_approvals, key=lambda row: row["approval_id"]):
            source = (approval["seller_node_id"], approval["material_id"])
            destination = (approval["buyer_node_id"], approval["material_id"])
            if source in reachable and destination not in reachable:
                reachable.add(destination)
                provenance[destination] = {
                    "kind": "transport",
                    "approval_id": approval["approval_id"],
                    "seller_node_id": source[0],
                    "buyer_node_id": destination[0],
                    "material_id": source[1],
                    "source": provenance[source],
                }
                changed = True
        for recipe in sorted(active_recipes, key=lambda row: row["recipe_id"]):
            input_states = [(recipe["node_id"], row["input_material_id"]) for row in sorted(inputs_by_recipe.get(recipe["recipe_id"], []), key=lambda row: row["input_sequence"])]
            output_state = (recipe["node_id"], recipe["output_material_id"])
            if input_states and all(state in reachable for state in input_states) and output_state not in reachable:
                reachable.add(output_state)
                provenance[output_state] = {
                    "kind": "transformation",
                    "recipe_id": recipe["recipe_id"],
                    "node_id": recipe["node_id"],
                    "output_material_id": recipe["output_material_id"],
                    "inputs": [provenance[state] for state in input_states],
                }
                changed = True

    terminal_materials = sorted((row for row in active_materials if row["terminal_material_flag"]), key=lambda row: row["material_id"])
    plant_ids = sorted(plant_by_id)
    target_states = {
        (plant_id, material["material_id"])
        for plant_id in plant_ids
        for material in terminal_materials
        if (plant_id, material["material_id"]) in reachable
    }
    useful_states = set(target_states)
    changed = True
    while changed:
        changed = False
        for approval in active_approvals:
            source = (approval["seller_node_id"], approval["material_id"])
            destination = (approval["buyer_node_id"], approval["material_id"])
            if destination in useful_states and source in reachable and source not in useful_states:
                useful_states.add(source)
                changed = True
        for recipe in active_recipes:
            output_state = (recipe["node_id"], recipe["output_material_id"])
            input_states = [(recipe["node_id"], row["input_material_id"]) for row in inputs_by_recipe.get(recipe["recipe_id"], [])]
            if output_state in useful_states and input_states and all(state in reachable for state in input_states):
                for state in input_states:
                    if state not in useful_states:
                        useful_states.add(state)
                        changed = True

    parents = {row["supplier_id"]: row["parent_group_id"] for row in organisations}
    node_owner = {row["node_id"]: row["supplier_id"] for row in nodes}
    terminals_by_state: dict[tuple[str, str], set[str]] = defaultdict(set)
    for state in target_states:
        terminals_by_state[state].add(state[1])
    changed = True
    while changed:
        changed = False
        for approval in active_approvals:
            source = (approval["seller_node_id"], approval["material_id"])
            destination = (approval["buyer_node_id"], approval["material_id"])
            if source not in reachable:
                continue
            additions = terminals_by_state[destination] - terminals_by_state[source]
            if additions:
                terminals_by_state[source].update(additions)
                changed = True
        for recipe in active_recipes:
            output_state = (recipe["node_id"], recipe["output_material_id"])
            input_states = [
                (recipe["node_id"], row["input_material_id"])
                for row in inputs_by_recipe.get(recipe["recipe_id"], [])
            ]
            if not input_states or not all(state in reachable for state in input_states):
                continue
            for state in input_states:
                additions = terminals_by_state[output_state] - terminals_by_state[state]
                if additions:
                    terminals_by_state[state].update(additions)
                    changed = True

    approval_coverage: dict[str, set[str]] = {}
    for approval in active_approvals:
        source = (approval["seller_node_id"], approval["material_id"])
        destination = (approval["buyer_node_id"], approval["material_id"])
        approval_coverage[approval["approval_id"]] = (
            set(terminals_by_state[destination]) if source in reachable else set()
        )
    recipe_coverage: dict[str, set[str]] = {}
    for recipe in active_recipes:
        input_states = [
            (recipe["node_id"], row["input_material_id"])
            for row in inputs_by_recipe.get(recipe["recipe_id"], [])
        ]
        recipe_coverage[recipe["recipe_id"]] = (
            set(terminals_by_state[(recipe["node_id"], recipe["output_material_id"])])
            if input_states and all(state in reachable for state in input_states)
            else set()
        )
    node_coverage = {node["node_id"]: set() for node in active_nodes}
    material_coverage = {material["material_id"]: set() for material in active_materials}
    for approval in active_approvals:
        coverage = approval_coverage[approval["approval_id"]]
        node_coverage[approval["seller_node_id"]].update(coverage)
        node_coverage[approval["buyer_node_id"]].update(coverage)
        material_coverage[approval["material_id"]].update(coverage)
    for recipe in active_recipes:
        coverage = recipe_coverage[recipe["recipe_id"]]
        node_coverage[recipe["node_id"]].update(coverage)
        material_coverage[recipe["output_material_id"]].update(coverage)
        for input_row in inputs_by_recipe.get(recipe["recipe_id"], []):
            material_coverage[input_row["input_material_id"]].update(coverage)
    organisation_coverage = {organisation["supplier_id"]: set() for organisation in active_orgs}
    for node, coverage in node_coverage.items():
        owner = node_owner[node]
        if owner is not None:
            organisation_coverage[owner].update(coverage)
    changed = True
    while changed:
        changed = False
        for supplier, coverage in list(organisation_coverage.items()):
            parent = parents.get(supplier)
            if parent in organisation_coverage:
                additions = coverage - organisation_coverage[parent]
                if additions:
                    organisation_coverage[parent].update(additions)
                    changed = True

    participating_approval_ids = {entity for entity, coverage in approval_coverage.items() if coverage}
    participating_recipe_ids = {entity for entity, coverage in recipe_coverage.items() if coverage}
    participating_node_ids = {entity for entity, coverage in node_coverage.items() if coverage}
    participating_material_ids = {entity for entity, coverage in material_coverage.items() if coverage}
    participating_org_ids = {entity for entity, coverage in organisation_coverage.items() if coverage}
    participation_index = {
        "definition": "Each entity maps to every terminal material for which the entity can occur in a complete structurally reachable derivation.",
        "entities": {
            "organisations": {entity: sorted(coverage) for entity, coverage in sorted(organisation_coverage.items())},
            "nodes": {entity: sorted(coverage) for entity, coverage in sorted(node_coverage.items())},
            "materials": {entity: sorted(coverage) for entity, coverage in sorted(material_coverage.items())},
            "recipes": {entity: sorted(coverage) for entity, coverage in sorted(recipe_coverage.items())},
            "approvals": {entity: sorted(coverage) for entity, coverage in sorted(approval_coverage.items())},
        },
    }

    terminal_witnesses: dict[str, Any] = {}
    full_lineage_terminals: set[str] = set()
    combination_counts: dict[str, int] = {}
    t1_producer_counts: dict[str, int] = {}
    plant_eligibility: dict[str, set[str]] = {}
    terminal_eligibility_by_plant: dict[str, set[str]] = {plant: set() for plant in plant_ids}
    common_upstream: dict[str, Any] = {}
    parent_dependencies: dict[str, Any] = {}
    regional_dependencies: dict[str, Any] = {}
    organisation_diverse: set[str] = set()

    for material in terminal_materials:
        terminal = material["material_id"]
        producer_recipes = [
            recipe for recipe in active_recipes
            if recipe["output_material_id"] == terminal
            and node_by_id.get(recipe["node_id"], {}).get("node_tier") == "TIER_1"
            and (recipe["node_id"], terminal) in reachable
        ]
        producer_nodes = sorted({recipe["node_id"] for recipe in producer_recipes})
        t1_producer_counts[terminal] = len(producer_nodes)
        combinations: list[dict[str, Any]] = []
        eligible_plants: set[str] = set()
        upstream_by_producer: dict[str, set[str]] = defaultdict(set)
        upstream_owners: set[str] = set()
        for producer_node in producer_nodes:
            plant_approvals = sorted(
                (
                    approval for approval in approvals_by_seller_state[(producer_node, terminal)]
                    if node_by_id[approval["buyer_node_id"]]["node_tier"] == "PLANT"
                ),
                key=lambda row: row["approval_id"],
            )
            eligible_plants.update(approval["buyer_node_id"] for approval in plant_approvals)
            for recipe in producer_recipes:
                if recipe["node_id"] != producer_node:
                    continue
                for input_row in inputs_by_recipe[recipe["recipe_id"]]:
                    for approval in approvals_by_buyer_state[(producer_node, input_row["input_material_id"])]:
                        upstream_by_producer[producer_node].add(approval["seller_node_id"])
                        owner = node_owner[approval["seller_node_id"]]
                        if owner is not None:
                            upstream_owners.add(owner)
            if plant_approvals:
                state = (producer_node, terminal)
                derivation = provenance[state]
                receipt = plant_approvals[0]
                derivation_nodes = _collect_derivation_nodes(derivation)
                tiers = {node_by_id[node]["node_tier"] for node in derivation_nodes}
                tiers.add("PLANT")
                owner = node_owner[producer_node]
                upstream_suppliers = {
                    node_owner[node]
                    for node in derivation_nodes
                    if node_by_id[node]["node_tier"] in {"TIER_4", "TIER_3", "TIER_2"}
                    and node_owner[node] is not None
                }
                combinations.append(
                    {
                        "terminal_producer_node_id": producer_node,
                        "operating_supplier_id": owner,
                        "plant_id": receipt["buyer_node_id"],
                        "receipt_approval_id": receipt["approval_id"],
                        "covered_tiers": sorted(tiers, key=lambda tier: -TIER_RANK[tier]),
                        "upstream_operating_supplier_ids": sorted(upstream_suppliers),
                        "derivation": derivation,
                    }
                )
        plant_eligibility[terminal] = eligible_plants
        for plant in eligible_plants:
            terminal_eligibility_by_plant[plant].add(terminal)
        full_combinations = [
            combo for combo in combinations
            if set(combo["covered_tiers"]) == {"TIER_4", "TIER_3", "TIER_2", "TIER_1", "PLANT"}
        ]
        if full_combinations:
            full_lineage_terminals.add(terminal)
        qualifying_pair: tuple[dict[str, Any], dict[str, Any]] | None = None
        for first_index, first in enumerate(full_combinations):
            for second in full_combinations[first_index + 1:]:
                if (
                    first["terminal_producer_node_id"] != second["terminal_producer_node_id"]
                    and first["upstream_operating_supplier_ids"] != second["upstream_operating_supplier_ids"]
                ):
                    qualifying_pair = (first, second)
                    break
            if qualifying_pair is not None:
                break
        combination_count = 2 if qualifying_pair is not None else 1 if full_combinations else 0
        combination_counts[terminal] = combination_count

        common_nodes = set.intersection(*(upstream_by_producer[node] for node in producer_nodes)) if len(producer_nodes) >= 2 else set()
        if common_nodes:
            common_upstream[terminal] = {
                "terminal_material_id": terminal,
                "tier_1_choices": producer_nodes,
                "shared_upstream_nodes": sorted(common_nodes),
                "affected_plants": sorted(eligible_plants),
            }
        groups: dict[str, set[str]] = defaultdict(set)
        for owner in upstream_owners:
            groups[_ultimate_group(owner, parents)].add(owner)
        shared_groups = {group: sorted(members) for group, members in groups.items() if len(members) >= 2}
        if shared_groups:
            parent_dependencies[terminal] = {
                "terminal_material_id": terminal,
                "shared_parent_groups": shared_groups,
                "affected_plants": sorted(eligible_plants),
            }

        sources_by_region_by_producer: dict[str, dict[str, set[str]]] = {}
        for producer, source_nodes in upstream_by_producer.items():
            sources_by_region: dict[str, set[str]] = defaultdict(set)
            for source_node in source_nodes:
                sources_by_region[node_by_id[source_node]["region_code"]].add(source_node)
            sources_by_region_by_producer[producer] = sources_by_region
        common_regions = (
            set.intersection(*(set(regions) for regions in sources_by_region_by_producer.values()))
            if len(sources_by_region_by_producer) >= 2
            else set()
        )
        regional_witnesses: dict[str, dict[str, list[str]]] = {}
        for region in common_regions:
            nodes_by_producer = {
                producer: sources_by_region_by_producer[producer][region]
                for producer in producer_nodes
            }
            if not set.intersection(*nodes_by_producer.values()) and len(set.union(*nodes_by_producer.values())) >= 2:
                regional_witnesses[region] = {
                    producer: sorted(source_nodes)
                    for producer, source_nodes in nodes_by_producer.items()
                }
        if regional_witnesses:
            regional_dependencies[terminal] = {
                "terminal_material_id": terminal,
                "regions": regional_witnesses,
                "affected_plants": sorted(eligible_plants),
            }

        producer_groups = {_ultimate_group(node_owner[node], parents) for node in producer_nodes if node_owner[node] is not None}
        upstream_groups = {_ultimate_group(owner, parents) for owner in upstream_owners}
        if len(producer_groups) >= 2 and len(upstream_groups) >= 2:
            organisation_diverse.add(terminal)
        terminal_witnesses[terminal] = {
            "material_name": material["material_name"],
            "criticality_class": material["criticality_class"],
            "eligible_plants": sorted(eligible_plants),
            "combination_count": combination_count,
            "combinations": list(qualifying_pair) if qualifying_pair is not None else full_combinations[:1],
        }

    receiving_pools: dict[tuple[str, str], set[str]] = defaultdict(set)
    approvals_by_receiving_pool: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for approval in active_approvals:
        pool = (approval["buyer_node_id"], approval["material_id"])
        receiving_pools[pool].add(approval["seller_node_id"])
        approvals_by_receiving_pool[pool].append(approval)
    for (buyer, material), pool_approvals in approvals_by_receiving_pool.items():
        available_share = sum(
            approval["maximum_approved_share"] if approval["maximum_approved_share"] is not None else 1.0
            for approval in pool_approvals
        )
        if available_share < 1.0 - 1e-12:
            _issue(
                issues,
                "APPROVAL_SHARE_CAP",
                "Approval share caps cannot cover the receiving pool",
                [buyer, material, *(approval["approval_id"] for approval in pool_approvals)],
            )
    multi_sourced = {pool: sellers for pool, sellers in receiving_pools.items() if len(sellers) >= 2}
    multi_source_by_level: dict[str, list[str]] = defaultdict(list)
    for (buyer, material), sellers in multi_sourced.items():
        level = node_by_id[buyer]["node_tier"]
        multi_source_by_level[level].append(f"{buyer}|{material}")

    owned_nodes: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for node in active_nodes:
        if node["supplier_id"] is not None:
            owned_nodes[node["supplier_id"]].append(node)
    multi_site_orgs = {supplier for supplier, owned in owned_nodes.items() if len(owned) >= 2}
    multi_tier_orgs = {supplier for supplier, owned in owned_nodes.items() if len({node["node_tier"] for node in owned}) >= 2}
    group_members: dict[str, set[str]] = defaultdict(set)
    for supplier in owned_nodes:
        group_members[_ultimate_group(supplier, parents)].add(supplier)
    qualifying_parent_groups = {group for group, members in group_members.items() if len(members) >= 2 and any(parents.get(member) is not None for member in members)}

    active_node_components = _components(active_node_ids, ((approval["seller_node_id"], approval["buyer_node_id"]) for approval in active_approvals))
    entity_breakdown = {
        "organisations": {"participating": len(participating_org_ids & {row["supplier_id"] for row in active_orgs}), "active": len(active_orgs)},
        "nodes": {"participating": len(participating_node_ids & active_node_ids), "active": len(active_nodes)},
        "materials": {"participating": len(participating_material_ids & active_material_ids), "active": len(active_materials)},
        "recipes": {"participating": len(participating_recipe_ids), "active": len(active_recipes)},
        "approvals": {"participating": len(participating_approval_ids), "active": len(active_approvals)},
    }
    participating_total = sum(value["participating"] for value in entity_breakdown.values())
    active_total = sum(value["active"] for value in entity_breakdown.values())
    orphan_ids = []
    orphan_ids.extend(sorted({row["supplier_id"] for row in active_orgs} - participating_org_ids))
    orphan_ids.extend(sorted(active_node_ids - participating_node_ids))
    orphan_ids.extend(sorted(active_material_ids - participating_material_ids))
    orphan_ids.extend(sorted(active_recipe_ids - participating_recipe_ids))
    orphan_ids.extend(sorted({row["approval_id"] for row in active_approvals} - participating_approval_ids))

    hidden_terminals = set(common_upstream) | set(parent_dependencies) | set(regional_dependencies)
    hidden_plants = {
        plant
        for terminal in hidden_terminals
        for plant in plant_eligibility.get(terminal, set())
    }
    shorter_terminal_ids: set[str] = set()
    shorter_ids = {row["approval_id"] for row in shorter_approvals}
    if shorter_ids:
        for terminal, witness in terminal_witnesses.items():
            encoded = json.dumps(witness, sort_keys=True)
            if any(approval_id in encoded for approval_id in shorter_ids):
                shorter_terminal_ids.add(terminal)
    sole_shorter = {
        terminal for terminal in shorter_terminal_ids
        if not any(not any(approval_id in json.dumps(combo, sort_keys=True) for approval_id in shorter_ids) for combo in terminal_witnesses[terminal]["combinations"])
    }

    multi_input_recipes = {recipe_id for recipe_id in active_recipe_ids if len(inputs_by_recipe.get(recipe_id, [])) >= 2}
    blendable_groups = {group for group, rows in group_rows.items() if rows and rows[0]["activation_mode"] == "BLENDABLE"}
    exclusive_groups = {group for group, rows in group_rows.items() if rows and rows[0]["activation_mode"] == "EXCLUSIVE"}
    high_critical = {row["material_id"] for row in terminal_materials if row["criticality_class"] in {"HIGH", "CRITICAL"}}
    dependency_plant_coverage = sorted(hidden_plants)

    metrics = [
        _metric("weak_connectivity", "Weakly connected components in the active node graph", len(active_node_components), "exactly 1", len(active_node_components) == 1, failures=[",".join(component) for component in active_node_components[1:]]),
        _metric("entity_participation", "Active structural entities participating in a terminal lineage", participating_total / active_total if active_total else 0, "100%", participating_total == active_total, numerator=participating_total, denominator=active_total, failures=orphan_ids),
        _metric("full_lineage_coverage", "Terminal materials with a full Tier-4-to-plant lineage", len(full_lineage_terminals) / len(terminal_materials) if terminal_materials else 0, "100%", len(full_lineage_terminals) == len(terminal_materials), numerator=len(full_lineage_terminals), denominator=len(terminal_materials), witnesses=full_lineage_terminals, failures={row["material_id"] for row in terminal_materials} - full_lineage_terminals),
        _metric("broader_combinations", "Minimum broader sourcing combinations per terminal material", min(combination_counts.values(), default=0), "at least 2", bool(combination_counts) and min(combination_counts.values()) >= 2, witnesses=[terminal for terminal, count in combination_counts.items() if count >= 2], failures=[terminal for terminal, count in combination_counts.items() if count < 2]),
        _metric("critical_tier1_producers", "Minimum Tier-1 producer nodes for HIGH or CRITICAL terminal materials", min((t1_producer_counts.get(terminal, 0) for terminal in high_critical), default=0), "at least 2", bool(high_critical) and all(t1_producer_counts.get(terminal, 0) >= 2 for terminal in high_critical), failures=[terminal for terminal in high_critical if t1_producer_counts.get(terminal, 0) < 2]),
        _metric("plant_eligibility", "Minimum plants eligible to receive each terminal material", min((len(value) for value in plant_eligibility.values()), default=0), "at least 2", bool(plant_eligibility) and all(len(value) >= 2 for value in plant_eligibility.values()), failures=[terminal for terminal, value in plant_eligibility.items() if len(value) < 2]),
        _metric("terminal_eligibility", "Minimum terminal materials eligible at each plant", min((len(value) for value in terminal_eligibility_by_plant.values()), default=0), "at least 3", all(len(value) >= 3 for value in terminal_eligibility_by_plant.values()), failures=[plant for plant, value in terminal_eligibility_by_plant.items() if len(value) < 3]),
        _metric("multi_source_levels", "Receiving levels with at least one multi-sourced pool", len({level for level in ("TIER_3", "TIER_2", "TIER_1", "PLANT") if multi_source_by_level[level]}), "all 4 levels", all(multi_source_by_level[level] for level in ("TIER_3", "TIER_2", "TIER_1", "PLANT")), witnesses=[level for level in ("TIER_3", "TIER_2", "TIER_1", "PLANT") if multi_source_by_level[level]]),
        _metric("multi_source_share", "Share of non-boundary receiving node/material pairs that are multi-sourced", len(multi_sourced) / len(receiving_pools) if receiving_pools else 0, "at least 20%", bool(receiving_pools) and len(multi_sourced) / len(receiving_pools) >= 0.20, numerator=len(multi_sourced), denominator=len(receiving_pools)),
        _metric("multi_input_recipes", "Share of active recipes with multiple inputs", len(multi_input_recipes) / len(active_recipes) if active_recipes else 0, "at least 20%", bool(active_recipes) and len(multi_input_recipes) / len(active_recipes) >= 0.20, numerator=len(multi_input_recipes), denominator=len(active_recipes), witnesses=multi_input_recipes),
        _metric("alternative_recipe_groups", "Alternative recipe groups", len(group_rows), "at least 4, including 2 blendable and 2 exclusive", len(group_rows) >= 4 and len(blendable_groups) >= 2 and len(exclusive_groups) >= 2, witnesses=group_rows, failures=[] if len(blendable_groups) >= 2 and len(exclusive_groups) >= 2 else [f"blendable={len(blendable_groups)}", f"exclusive={len(exclusive_groups)}"]),
        _metric("multi_site_organisations", "Multi-site operating supplier organisations", len(multi_site_orgs), "at least 4", len(multi_site_orgs) >= 4, witnesses=multi_site_orgs),
        _metric("multi_tier_organisations", "Operating suppliers represented at more than one tier", len(multi_tier_orgs), "at least 2", len(multi_tier_orgs) >= 2, witnesses=multi_tier_orgs),
        _metric("parent_groups", "Parent groups containing at least two operating suppliers", len(qualifying_parent_groups), "at least 2", len(qualifying_parent_groups) >= 2, witnesses=qualifying_parent_groups),
        _metric("common_upstream_dependencies", "Common-upstream dependency motifs", len(common_upstream), "at least 2", len(common_upstream) >= 2, witnesses=common_upstream),
        _metric("parent_group_dependencies", "Parent-group dependency motifs", len(parent_dependencies), "at least 2", len(parent_dependencies) >= 2, witnesses=parent_dependencies),
        _metric("regional_dependencies", "Regional dependency motifs using distinct upstream sites", len(regional_dependencies), "at least 2", len(regional_dependencies) >= 2, witnesses=regional_dependencies),
        _metric("dependency_terminal_coverage", "Terminal materials covered by hidden dependencies", len(hidden_terminals), "at least 3", len(hidden_terminals) >= 3, witnesses=hidden_terminals),
        _metric("dependency_plant_coverage", "Plants covered by hidden dependencies", len(hidden_plants), "at least 2", len(hidden_plants) >= 2, witnesses=dependency_plant_coverage),
        _metric("organisation_diverse_alternatives", "Terminal materials with an organisation-diverse alternative", len(organisation_diverse), "at least 2", len(organisation_diverse) >= 2, witnesses=organisation_diverse),
        _metric("apparent_choice_common_dependency", "Terminal materials with downstream choice and a common upstream dependency", len(common_upstream), "at least 2", len(common_upstream) >= 2, witnesses=common_upstream),
        _metric("shorter_alternatives", "Share of terminal materials using a declared shorter alternative", len(shorter_terminal_ids) / len(terminal_materials) if terminal_materials else 0, "no more than 25%; never the sole lineage", bool(terminal_materials) and len(shorter_terminal_ids) / len(terminal_materials) <= 0.25 and not sole_shorter, numerator=len(shorter_terminal_ids), denominator=len(terminal_materials), witnesses=shorter_terminal_ids, failures=sole_shorter),
        _metric("duplicate_approvals", "Duplicate usable seller/buyer/material approvals", len(approved_triples), "0", not approved_triples, failures=approved_triples),
        _metric("orphan_entities", "Orphan active structural entities", len(orphan_ids), "0", not orphan_ids, failures=orphan_ids),
        _metric("graph_cycles", "Node, material-state or recipe dependency cycles", int(bool(node_cycle)) + int(bool(state_cycle)) + int(bool(recipe_cycle)), "0", not node_cycle and not state_cycle and not recipe_cycle, failures=[*node_cycle, *state_cycle, *recipe_cycle]),
    ]

    status = "PASS" if not issues and all(metric["passed"] for metric in metrics) else "FAIL"
    counts = {
        "supplier_organisations": len(organisations),
        "supplier_nodes": sum(row["node_type"] == "SUPPLIER_SITE" for row in nodes),
        "plants": len(plants),
        "materials": len(materials),
        "terminal_materials": len(terminal_materials),
        "recipes": len(recipes),
        "recipe_inputs": len(recipe_inputs),
        "approvals": len(approvals),
        "usable_approvals": len(active_approvals),
    }
    scorecard = {
        "assessment": "CAP-001 network structure",
        "configuration_id": config["configuration_id"],
        "configuration_version": config["configuration_version"],
        "status": status,
        "counts": counts,
        "data_checksums": dict(sorted((data_checksums or {}).items())),
        "entity_participation": entity_breakdown,
        "metrics": metrics,
        "issues": sorted(issues, key=lambda item: (item["code"], item["message"], item["entities"])),
    }
    lineage_witnesses = {
        "definition": "Each retained combination differs by Tier-1 producer and includes a complete recursive derivation for every selected recipe input.",
        "terminal_materials": terminal_witnesses,
        "participation_index": participation_index,
    }
    dependency_witnesses = {
        "common_upstream": common_upstream,
        "parent_group": parent_dependencies,
        "regional": regional_dependencies,
        "multi_sourced_receiving_pools": {
            level: sorted(multi_source_by_level[level])
            for level in ("TIER_3", "TIER_2", "TIER_1", "PLANT")
        },
    }
    report = _render_report(scorecard, terminal_witnesses, common_upstream, parent_dependencies, regional_dependencies)
    diagram = _render_diagram(nodes, active_approvals)
    return Assessment(scorecard, lineage_witnesses, dependency_witnesses, report, diagram)


def _render_report(
    scorecard: Mapping[str, Any],
    terminal_witnesses: Mapping[str, Any],
    common_upstream: Mapping[str, Any],
    parent_dependencies: Mapping[str, Any],
    regional_dependencies: Mapping[str, Any],
) -> str:
    lines = [
        "# CAP-001 Network Structure Report",
        "",
        f"Assessment status: **{scorecard['status']}**",
        "",
        "This report describes structural possibility only. Contracts, lanes, costs,",
        "capacity, demand and scenarios are deliberately outside this assessment.",
        "",
        "## Entity counts",
        "",
        "| Entity | Count |",
        "|---|---:|",
    ]
    for name, count in scorecard["counts"].items():
        lines.append(f"| {name.replace('_', ' ').title()} | {count} |")
    lines.extend(["", "## Depth scorecard", "", "| Metric | Result | Threshold | Status |", "|---|---:|---:|:---:|"])
    for metric in scorecard["metrics"]:
        value = metric["value"]
        rendered_value = f"{value:.1%}" if isinstance(value, float) and 0 <= value <= 1 else str(value)
        lines.append(f"| {metric['label']} | {rendered_value} | {metric['threshold']} | {'PASS' if metric['passed'] else 'FAIL'} |")
    lines.extend(["", "## Terminal lineage summary", "", "| Terminal material | Tier-1 combinations | Eligible plants |", "|---|---:|---:|"])
    for terminal, witness in terminal_witnesses.items():
        lines.append(f"| {terminal} — {witness['material_name']} | {witness['combination_count']} | {len(witness['eligible_plants'])} |")
    lines.extend(
        [
            "",
            "## Deliberate dependency structure",
            "",
            f"- Common-upstream motifs: {len(common_upstream)} terminal materials.",
            f"- Parent-group motifs: {len(parent_dependencies)} terminal materials.",
            f"- Region-only motifs using distinct sites: {len(regional_dependencies)} terminal materials.",
            "- Machine-readable witnesses identify the affected choices, upstream nodes,",
            "  parent groups and plants.",
            "",
            "## Interpretation boundary",
            "",
            "A passing result proves that the structural data has lineage, alternatives and",
            "discoverable dependency. It does not prove that an alternative has adequate",
            "capacity, attractive economics or useful scenario behaviour; those properties",
            "must be established when the remaining dataset is generated and calibrated.",
        ]
    )
    if scorecard["issues"]:
        lines.extend(["", "## Validation issues", ""])
        for issue in scorecard["issues"]:
            lines.append(f"- `{issue['code']}`: {issue['message']} ({', '.join(issue['entities'])})")
    return "\n".join(lines) + "\n"


def _render_diagram(nodes: Sequence[Mapping[str, Any]], approvals: Sequence[Mapping[str, Any]]) -> str:
    lines = ["flowchart LR"]
    for tier in ("TIER_4", "TIER_3", "TIER_2", "TIER_1", "PLANT"):
        lines.append(f"  subgraph {tier}[{tier.replace('_', ' ').title()}]")
        for node in sorted((row for row in nodes if row["active_flag"] and row["node_tier"] == tier), key=lambda row: row["node_id"]):
            label = node["node_name"].replace('"', "'")
            lines.append(f"    {node['node_id'].replace('-', '_')}[\"{node['node_id']}<br/>{label}\"]")
        lines.append("  end")
    pair_counts = Counter(
        (row["seller_node_id"], row["buyer_node_id"])
        for row in approvals
        if row["approval_status"] == "APPROVED"
    )
    for (seller, buyer), count in sorted(pair_counts.items()):
        lines.append(f"  {seller.replace('-', '_')} -->|\"{count} material approval{'s' if count != 1 else ''}\"| {buyer.replace('-', '_')}")
    return "\n".join(lines) + "\n"


def assess_directory(data_dir: Path) -> Assessment:
    config = load_config()
    tables = load_tables(data_dir, config)
    checksums = {file_name: sha256_path(data_dir / file_name) for file_name in STRUCTURAL_FILES}
    return assess_tables(tables, config=config, data_checksums=checksums)


def render_evidence(assessment: Assessment) -> dict[str, str]:
    return {
        "network_depth_scorecard.json": canonical_json(assessment.scorecard),
        "lineage_witnesses.json": canonical_json(assessment.lineage_witnesses),
        "dependency_witnesses.json": canonical_json(assessment.dependency_witnesses),
        "NETWORK_STRUCTURE_REPORT.md": assessment.report,
        "network_overview.mmd": assessment.diagram,
    }


def write_evidence(output_dir: Path, assessment: Assessment) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for file_name, content in render_evidence(assessment).items():
        (output_dir / file_name).write_text(content, encoding="utf-8", newline="")


def check_evidence(output_dir: Path, assessment: Assessment) -> list[str]:
    expected = render_evidence(assessment)
    drift = [
        file_name
        for file_name, content in expected.items()
        if not (output_dir / file_name).is_file() or (output_dir / file_name).read_text(encoding="utf-8") != content
    ]
    actual = {path.name for path in output_dir.iterdir() if path.is_file()} if output_dir.is_dir() else set()
    drift.extend(sorted(actual - set(expected)))
    return sorted(set(drift))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_NETWORK_DIR / "data")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_NETWORK_DIR / "evidence")
    parser.add_argument("--check", action="store_true", help="fail if committed evidence differs")
    args = parser.parse_args(argv)
    assessment = assess_directory(args.data_dir.resolve())
    if args.check:
        drift = check_evidence(args.output_dir.resolve(), assessment)
        if drift:
            print("Network evidence drift: " + ", ".join(drift), file=sys.stderr)
            return 1
    else:
        write_evidence(args.output_dir.resolve(), assessment)
    print(
        f"Network structure assessment {assessment.scorecard['status']}: "
        f"{len(assessment.scorecard['metrics'])} metrics, "
        f"{len(assessment.scorecard['issues'])} validation issues."
    )
    return 0 if assessment.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
