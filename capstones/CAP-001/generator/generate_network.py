#!/usr/bin/env python3
"""Generate the deterministic CAP-001 structural supply network."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import random
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.contract_runtime import canonical_json, load_config, sha256_bytes  # noqa: E402


DEFAULT_OUTPUT_DIR = ROOT / "capstones" / "CAP-001" / "generated" / "network"
DEFAULT_MASTER_SEED = 17012027
STRUCTURAL_FILES = (
    "supplier_organisations.csv",
    "network_nodes.csv",
    "plants.csv",
    "materials.csv",
    "transformation_recipes.csv",
    "transformation_inputs.csv",
    "material_flow_approvals.csv",
)


COUNTRY_PROFILES = (
    ("GB", "EUROPE_WEST", "Europe/London", "GBP", 52.48, -1.89),
    ("DE", "EUROPE_CENTRAL", "Europe/Berlin", "EUR", 51.51, 7.46),
    ("PL", "EUROPE_CENTRAL", "Europe/Warsaw", "PLN", 50.26, 19.02),
    ("ES", "EUROPE_SOUTH", "Europe/Madrid", "EUR", 41.65, -0.89),
    ("FR", "EUROPE_WEST", "Europe/Paris", "EUR", 45.76, 4.84),
    ("CZ", "EUROPE_CENTRAL", "Europe/Prague", "CZK", 49.20, 16.61),
    ("IT", "EUROPE_SOUTH", "Europe/Rome", "EUR", 45.46, 9.19),
    ("NL", "EUROPE_WEST", "Europe/Amsterdam", "EUR", 51.92, 4.48),
    ("SE", "EUROPE_NORTH", "Europe/Stockholm", "SEK", 57.71, 11.97),
    ("RO", "EUROPE_EAST", "Europe/Bucharest", "RON", 45.75, 21.23),
    ("TR", "EUROPE_SOUTH", "Europe/Istanbul", "TRY", 40.99, 29.03),
    ("MA", "AFRICA_NORTH", "Africa/Casablanca", "MAD", 33.57, -7.59),
    ("IN", "ASIA_SOUTH", "Asia/Kolkata", "INR", 19.08, 72.88),
    ("VN", "ASIA_SOUTHEAST", "Asia/Ho_Chi_Minh", "VND", 10.82, 106.63),
    ("MY", "ASIA_SOUTHEAST", "Asia/Kuala_Lumpur", "MYR", 3.14, 101.69),
    ("KR", "ASIA_EAST", "Asia/Seoul", "KRW", 37.57, 126.98),
    ("JP", "ASIA_EAST", "Asia/Tokyo", "JPY", 35.68, 139.77),
    ("US", "AMERICAS_NORTH", "America/Chicago", "USD", 41.88, -87.63),
    ("MX", "AMERICAS_NORTH", "America/Mexico_City", "MXN", 20.67, -103.35),
    ("CA", "AMERICAS_NORTH", "America/Toronto", "CAD", 43.65, -79.38),
    ("BR", "AMERICAS_SOUTH", "America/Sao_Paulo", "BRL", -23.55, -46.63),
    ("ZA", "AFRICA_SOUTH", "Africa/Johannesburg", "ZAR", -26.20, 28.05),
)

SUPPLIER_NAMES = (
    "Northstar Material Systems",
    "Bluehaven Industrial Group",
    "Redwood Technical Materials",
    "Vantage Component Holdings",
    "Silverline Process Industries",
    "Harbourlight Engineered Products",
    "Juniper Motion Materials",
    "Stonebridge Control Components",
    "Cobalt Ridge Manufacturing",
    "Meridian Electromechanical",
    "Pioneer Insulation Systems",
    "Clearwater Connector Works",
    "Ironvale Precision Materials",
    "Westmere Industrial Ceramics",
    "Aster Peak Semiconductor Materials",
    "Orchard Gate Alloy Products",
    "Beacon Field Sensor Materials",
    "Summit Arc Technical Products",
    "Copperleaf Industrial Supply",
    "Granite Bay Motion Systems",
    "Highland Circuit Materials",
    "Riverbend Engineered Supply",
)

RAW_MATERIALS = (
    "Copper Foil Stock",
    "Electrical Steel Sheet",
    "Silicon Substrate",
    "Rare-Earth Magnet Alloy",
    "Polymer Resin Feedstock",
    "Ceramic Insulator Feedstock",
    "Aluminium Billet",
    "Bearing Steel Stock",
    "Power Semiconductor Wafer",
    "Optical Sensor Glass",
    "Industrial Adhesive Base",
    "Control-Grade Connector Stock",
)

PROCESSED_MATERIALS = (
    "Wound Conductor Set",
    "Laminated Core Pack",
    "Conditioned Semiconductor Die",
    "Magnet Rotor Insert",
    "Moulded Insulation Set",
    "Machined Housing Set",
    "Precision Bearing Set",
    "Sensor Optics Set",
)

SUBASSEMBLIES = (
    "Power Stage Assembly",
    "Control Board Assembly",
    "Motor Core Assembly",
    "Rotor Assembly",
    "Thermal Housing Assembly",
    "Feedback Sensor Assembly",
    "Connector Harness Assembly",
    "Isolation Assembly",
)

TERMINAL_MATERIALS = (
    "Compact Motor Controller",
    "High-Capacity Drive Controller",
    "Remote Monitoring Controller",
    "Precision Motion Controller",
    "Ruggedised Control Cabinet Module",
    "Energy Recovery Controller",
    "Process Sensor Controller",
    "Safety Control Module",
)


def namespace_seed(master_seed: int, namespace: str) -> int:
    """Derive a stable seed without coupling independent entity families."""

    digest = hashlib.sha256(f"{master_seed}:{namespace}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def rng_for(master_seed: int, namespace: str) -> random.Random:
    return random.Random(namespace_seed(master_seed, namespace))


def supplier_id(index: int) -> str:
    return f"SUP-{index + 1:04d}"


def node_id(index: int) -> str:
    return f"NODE-{index + 1:04d}"


def material_id(index: int) -> str:
    return f"MAT-{index + 1:04d}"


def generate_organisations(master_seed: int) -> list[dict[str, Any]]:
    rng = rng_for(master_seed, "organisations")
    parent_by_index = {1: supplier_id(0), 2: supplier_id(0), 4: supplier_id(3), 5: supplier_id(3)}
    organisations: list[dict[str, Any]] = []
    for index, name in enumerate(SUPPLIER_NAMES):
        country, region, _, _, _, _ = COUNTRY_PROFILES[index]
        risk_roll = rng.random()
        risk_band = "LOW" if risk_roll < 0.38 else "MEDIUM" if risk_roll < 0.82 else "HIGH"
        recovery_base = {"LOW": 4, "MEDIUM": 7, "HIGH": 11}[risk_band]
        organisations.append(
            {
                "supplier_id": supplier_id(index),
                "supplier_name": name,
                "parent_group_id": parent_by_index.get(index),
                "hq_country_code": country,
                "region_code": region,
                "financial_risk_band": risk_band,
                "recovery_time_weeks": recovery_base + rng.randrange(0, 4),
                "open_cost_participant_flag": index < 18 or index in {20, 21},
                "active_flag": True,
            }
        )
    return organisations


def _supplier_node_owners() -> list[str]:
    return [
        *(supplier_id(i) for i in range(12)),
        *(supplier_id(i) for i in range(12, 20)),
        supplier_id(20),
        supplier_id(21),
        *(supplier_id(i) for i in range(6)),
        *(supplier_id(i) for i in range(6, 12)),
    ]


def generate_nodes(master_seed: int, config: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = rng_for(master_seed, "nodes")
    tier_sequence = ["TIER_4"] * 12 + ["TIER_3"] * 8 + ["TIER_2"] * 8 + ["TIER_1"] * 6
    owners = _supplier_node_owners()
    nodes: list[dict[str, Any]] = []
    for index, (tier, owner) in enumerate(zip(tier_sequence, owners, strict=True)):
        profile_index = (index * 7 + namespace_seed(master_seed, "node-geography") % len(COUNTRY_PROFILES)) % len(COUNTRY_PROFILES)
        country, region, timezone, currency, latitude, longitude = COUNTRY_PROFILES[profile_index]
        nodes.append(
            {
                "node_id": node_id(index),
                "supplier_id": owner,
                "node_name": f"{SUPPLIER_NAMES[int(owner[-4:]) - 1]} Site {index + 1:02d}",
                "node_type": "SUPPLIER_SITE",
                "node_tier": tier,
                "external_boundary_flag": tier == "TIER_4",
                "processing_capability_flag": tier in {"TIER_3", "TIER_2", "TIER_1"},
                "pooling_policy": "WEIGHTED_AVERAGE",
                "country_code": country,
                "region_code": region,
                "latitude": round(latitude + rng.uniform(-0.7, 0.7), 5),
                "longitude": round(longitude + rng.uniform(-0.7, 0.7), 5),
                "timezone": timezone,
                "local_currency": currency,
                "site_risk_score": round(rng.uniform(18, 82), 1),
                "active_flag": True,
            }
        )

    plant_coordinates = {
        "Birmingham": (52.4862, -1.8904, "Europe/London", "EUROPE_WEST"),
        "Dortmund": (51.5136, 7.4653, "Europe/Berlin", "EUROPE_CENTRAL"),
        "Katowice": (50.2649, 19.0238, "Europe/Warsaw", "EUROPE_CENTRAL"),
        "Zaragoza": (41.6488, -0.8891, "Europe/Madrid", "EUROPE_SOUTH"),
    }
    plant_priorities = {"Birmingham": 1.10, "Dortmund": 1.25, "Katowice": 1.00, "Zaragoza": 0.95}
    plants: list[dict[str, Any]] = []
    for offset, plant in enumerate(config["business"]["plants"]):
        index = len(tier_sequence) + offset
        latitude, longitude, timezone, region = plant_coordinates[plant["name"]]
        nodes.append(
            {
                "node_id": node_id(index),
                "supplier_id": None,
                "node_name": plant["name"],
                "node_type": "PLANT",
                "node_tier": "PLANT",
                "external_boundary_flag": False,
                "processing_capability_flag": False,
                "pooling_policy": "WEIGHTED_AVERAGE",
                "country_code": plant["country_code"],
                "region_code": region,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "local_currency": plant["local_currency"],
                "site_risk_score": round(8.0 + offset * 2.5, 1),
                "active_flag": True,
            }
        )
        plants.append(
            {
                "plant_id": node_id(index),
                "plant_name": plant["name"],
                "primary_role": plant["primary_role"],
                "base_currency": "EUR",
                "plant_priority_weight": plant_priorities[plant["name"]],
                "customer_region": region,
            }
        )
    return nodes, plants


def generate_materials() -> list[dict[str, Any]]:
    materials: list[dict[str, Any]] = []
    families = ("CONDUCTOR", "MAGNETIC", "POWER_ELECTRONICS", "MOTION", "INSULATION", "HOUSING", "SENSING", "CONTROL")
    definitions = (
        (RAW_MATERIALS, "BOUNDARY_RAW", "KG"),
        (PROCESSED_MATERIALS, "PROCESSED", "EA"),
        (SUBASSEMBLIES, "SUBASSEMBLY", "EA"),
        (TERMINAL_MATERIALS, "TERMINAL", "EA"),
    )
    index = 0
    for names, stage, uom in definitions:
        for stage_index, name in enumerate(names):
            terminal = stage == "TERMINAL"
            materials.append(
                {
                    "material_id": material_id(index),
                    "material_name": name,
                    "material_stage": stage,
                    "material_family": families[stage_index % len(families)],
                    "uom": uom,
                    "criticality_class": ("CRITICAL" if stage_index < 4 else "HIGH") if terminal else ("HIGH" if stage_index % 4 == 0 else "MEDIUM"),
                    "terminal_material_flag": terminal,
                    "external_price_eligible_flag": stage == "BOUNDARY_RAW",
                    "poolable_flag": True,
                    "shelf_life_weeks": 52 if stage == "BOUNDARY_RAW" else 26 if stage == "PROCESSED" else 18,
                    "active_flag": True,
                }
            )
            index += 1
    return materials


def generate_recipes(master_seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = rng_for(master_seed, "recipes")
    tier_3_nodes = [node_id(i) for i in range(12, 20)]
    tier_2_nodes = [node_id(i) for i in range(20, 28)]
    tier_1_nodes = [node_id(i) for i in range(28, 34)]
    raw = [material_id(i) for i in range(12)]
    processed = [material_id(i) for i in range(12, 20)]
    subassemblies = [material_id(i) for i in range(20, 28)]
    terminals = [material_id(i) for i in range(28, 36)]
    recipes: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []

    group_specs = {
        ("TIER_3", 0, 0): ("RGP-0001", "BLENDABLE"),
        ("TIER_3", 1, 0): ("RGP-0002", "BLENDABLE"),
        ("TIER_2", 0, 0): ("RGP-0003", "EXCLUSIVE"),
        ("TIER_1", 0, 0): ("RGP-0004", "EXCLUSIVE"),
    }

    def add_recipe(
        node: str,
        output: str,
        input_materials: Iterable[str],
        *,
        group_id: str | None = None,
        activation_mode: str = "BLENDABLE",
    ) -> None:
        recipe_number = len(recipes) + 1
        recipe = f"RCP-{recipe_number:05d}"
        recipes.append(
            {
                "recipe_id": recipe,
                "node_id": node,
                "output_material_id": output,
                "recipe_group_id": group_id,
                "activation_mode": activation_mode,
                "yield_rate": round(rng.uniform(0.91, 0.99), 4),
                "minimum_run_quantity": float(rng.choice((0, 10, 20, 25, 40))),
                "setup_required_flag": rng.random() < 0.68,
                "effective_from_period": "P01",
                "effective_to_period": "P12",
                "active_flag": True,
            }
        )
        for sequence, input_material in enumerate(input_materials, start=1):
            inputs.append(
                {
                    "recipe_id": recipe,
                    "input_material_id": input_material,
                    "quantity_per_output": round(rng.uniform(0.35, 1.35), 4),
                    "scrap_recovery_flag": False,
                    "input_sequence": sequence,
                }
            )

    tier_specs = (
        ("TIER_3", tier_3_nodes, processed, raw),
        ("TIER_2", tier_2_nodes, subassemblies, processed),
        ("TIER_1", tier_1_nodes, terminals, subassemblies),
    )
    producer_indexes: dict[str, list[tuple[int, int]]] = {}
    for tier_name, nodes, outputs, stage_inputs in tier_specs:
        if tier_name == "TIER_2":
            producer_indexes[tier_name] = [
                (3, 4),
                (6, 7),
                (2, 5),
                (3, 6),
                (3, 6),
                (5, 0),
                (6, 1),
                (7, 2),
            ]
        elif tier_name == "TIER_1":
            producer_indexes[tier_name] = [(j % 6, (j + 2) % 6) for j in range(8)]
        else:
            producer_indexes[tier_name] = [(j, (j + 3) % 8) for j in range(8)]

        for output_index, output in enumerate(outputs):
            for producer_position, producer_index in enumerate(producer_indexes[tier_name][output_index]):
                primary_index = (
                    output_index
                    if tier_name == "TIER_1"
                    else (output_index + producer_position * 2) % len(stage_inputs)
                )
                recipe_inputs = [stage_inputs[primary_index]]
                if producer_position == 0 and (
                    output_index % 2 == 0 or (tier_name == "TIER_1" and output_index < 2)
                ):
                    recipe_inputs.append(stage_inputs[(primary_index + 1) % len(stage_inputs)])
                group_id, activation = group_specs.get((tier_name, output_index, producer_position), (None, "BLENDABLE"))
                add_recipe(nodes[producer_index], output, recipe_inputs, group_id=group_id, activation_mode=activation)

    alternate_specs = (
        (tier_3_nodes[0], processed[0], (raw[10], raw[11]), "RGP-0001", "BLENDABLE"),
        (tier_3_nodes[1], processed[1], (raw[9],), "RGP-0002", "BLENDABLE"),
        (tier_2_nodes[3], subassemblies[0], (processed[6], processed[7]), "RGP-0003", "EXCLUSIVE"),
        (tier_1_nodes[0], terminals[0], (subassemblies[6],), "RGP-0004", "EXCLUSIVE"),
    )
    for node, output, recipe_inputs, group_id, activation in alternate_specs:
        add_recipe(node, output, recipe_inputs, group_id=group_id, activation_mode=activation)

    return recipes, inputs


def generate_approvals(
    master_seed: int,
    recipes: Iterable[Mapping[str, Any]],
    inputs: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rng = rng_for(master_seed, "approvals")
    recipe_rows = list(recipes)
    input_rows = list(inputs)
    recipe_by_id = {row["recipe_id"]: row for row in recipe_rows}
    raw = [material_id(i) for i in range(12)]
    terminals = [material_id(i) for i in range(28, 36)]
    tier_4_nodes = [node_id(i) for i in range(12)]
    plant_nodes = [node_id(i) for i in range(34, 38)]
    output_producers: dict[str, set[str]] = defaultdict(set)
    for recipe in recipe_rows:
        output_producers[recipe["output_material_id"]].add(recipe["node_id"])

    candidate_sellers: dict[tuple[str, str], set[str]] = defaultdict(set)
    for input_row in input_rows:
        recipe = recipe_by_id[input_row["recipe_id"]]
        material = input_row["input_material_id"]
        buyer = recipe["node_id"]
        if material in raw:
            raw_index = raw.index(material)
            sellers = (tier_4_nodes[raw_index], tier_4_nodes[(raw_index + 5) % len(tier_4_nodes)])
        else:
            sellers = tuple(sorted(output_producers[material]))
        for seller in sellers:
            candidate_sellers[(buyer, material)].add(seller)

    triples: set[tuple[str, str, str]] = set()
    terminal_primary_source: dict[tuple[str, str], str] = {}
    tier_1_nodes = [node_id(i) for i in range(28, 34)]
    subassemblies = [material_id(i) for i in range(20, 28)]
    for terminal_index, subassembly in enumerate(subassemblies[2:], start=2):
        producers = (tier_1_nodes[terminal_index % 6], tier_1_nodes[(terminal_index + 2) % 6])
        sellers = sorted(output_producers[subassembly])
        terminal_primary_source[(producers[0], subassembly)] = sellers[0]
        terminal_primary_source[(producers[1], subassembly)] = sellers[1]
    single_source_index: dict[str, int] = defaultdict(int)
    for (buyer, material), seller_set in sorted(candidate_sellers.items()):
        sellers = sorted(seller_set)
        buyer_number = int(buyer[-4:])
        material_number = int(material[-4:])
        if 21 <= material_number <= 28 and 29 <= buyer_number <= 34:
            subassembly_index = material_number - 21
            if subassembly_index < 2:
                selected = sellers
            elif (buyer, material) in terminal_primary_source:
                selected = [terminal_primary_source[(buyer, material)]]
            else:
                selected = [sellers[single_source_index[material] % len(sellers)]]
                single_source_index[material] += 1
        elif (buyer_number + material_number) % 2 == 0:
            selected = sellers
        else:
            selected = [sellers[single_source_index[material] % len(sellers)]]
            single_source_index[material] += 1
        for seller in selected:
            triples.add((seller, buyer, material))

    for terminal_index, terminal in enumerate(terminals):
        eligible_plants = (
            plant_nodes[terminal_index % 4],
            plant_nodes[(terminal_index + 1) % 4],
            plant_nodes[(terminal_index + 2) % 4],
        )
        for seller in sorted(output_producers[terminal]):
            for plant in eligible_plants:
                triples.add((seller, plant, terminal))

    source_count_by_pool = Counter((buyer, material) for _, buyer, material in triples)
    approvals: list[dict[str, Any]] = []
    for index, (seller, buyer, material) in enumerate(sorted(triples)):
        source_count = source_count_by_pool[(buyer, material)]
        approvals.append(
            {
                "approval_id": f"APR-{index + 1:05d}",
                "seller_node_id": seller,
                "buyer_node_id": buyer,
                "material_id": material,
                "approval_status": "APPROVED",
                "valid_from_period": "P01",
                "valid_to_period": "P12",
                "maximum_approved_share": round(rng.uniform(0.62, 0.82), 2) if source_count > 1 else None,
                "qualification_score": round(rng.uniform(72, 98), 1),
                "notes": "Qualified structural source",
            }
        )
    return approvals


def build_dataset(master_seed: int = DEFAULT_MASTER_SEED) -> dict[str, list[dict[str, Any]]]:
    config = load_config()
    organisations = generate_organisations(master_seed)
    nodes, plants = generate_nodes(master_seed, config)
    materials = generate_materials()
    recipes, inputs = generate_recipes(master_seed)
    approvals = generate_approvals(master_seed, recipes, inputs)
    return {
        "supplier_organisations.csv": organisations,
        "network_nodes.csv": nodes,
        "plants.csv": plants,
        "materials.csv": materials,
        "transformation_recipes.csv": recipes,
        "transformation_inputs.csv": inputs,
        "material_flow_approvals.csv": approvals,
    }


def _csv_text(rows: Iterable[Mapping[str, Any]], fieldnames: list[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_cell(row[key]) for key in fieldnames})
    return buffer.getvalue()


def _csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def render_files(master_seed: int = DEFAULT_MASTER_SEED) -> dict[str, str]:
    config = load_config()
    dataset = build_dataset(master_seed)
    rendered: dict[str, str] = {}
    for file_name in STRUCTURAL_FILES:
        fields = [field["name"] for field in config["raw_contracts"][file_name]["columns"]]
        rendered[f"data/{file_name}"] = _csv_text(dataset[file_name], fields)
    manifest = {
        "configuration_id": config["configuration_id"],
        "configuration_version": config["configuration_version"],
        "generator": "generate_network.py",
        "master_seed": master_seed,
        "namespaced_seeds": {
            namespace: namespace_seed(master_seed, namespace)
            for namespace in ("organisations", "nodes", "node-geography", "recipes", "approvals")
        },
        "files": {
            relative_path.removeprefix("data/"): {
                "rows": len(dataset[relative_path.removeprefix("data/")]),
                "sha256": sha256_bytes(content.encode("utf-8")),
            }
            for relative_path, content in rendered.items()
        },
    }
    rendered["generation_manifest.json"] = canonical_json(manifest)
    return rendered


def write_files(output_dir: Path, master_seed: int = DEFAULT_MASTER_SEED) -> dict[str, str]:
    rendered = render_files(master_seed)
    for relative_path, content in rendered.items():
        path = output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
    return rendered


def check_files(output_dir: Path, master_seed: int = DEFAULT_MASTER_SEED) -> list[str]:
    expected = render_files(master_seed)
    drift: list[str] = []
    for relative_path, content in expected.items():
        path = output_dir / relative_path
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            drift.append(relative_path)
    expected_paths = set(expected)
    actual_paths = {
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and "evidence" not in path.relative_to(output_dir).parts
    } if output_dir.exists() else set()
    drift.extend(sorted(actual_paths - expected_paths))
    return sorted(set(drift))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--master-seed", type=int, default=DEFAULT_MASTER_SEED)
    parser.add_argument("--check", action="store_true", help="fail if committed generated files differ")
    args = parser.parse_args(argv)
    output_dir = args.output_dir.resolve()
    if args.check:
        drift = check_files(output_dir, args.master_seed)
        if drift:
            print("Network generation drift: " + ", ".join(drift), file=sys.stderr)
            return 1
        print(f"Generated network files are current ({len(render_files(args.master_seed))} files).")
        return 0
    rendered = write_files(output_dir, args.master_seed)
    with tempfile.TemporaryDirectory() as temporary:
        verification_dir = Path(temporary)
        write_files(verification_dir, args.master_seed)
        if check_files(verification_dir, args.master_seed):
            raise RuntimeError("generated files failed deterministic self-check")
    print(f"Generated {len(rendered)} network files in {output_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
