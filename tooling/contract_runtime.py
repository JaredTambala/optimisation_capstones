"""Runtime helpers for CAP-001's machine-readable data contracts.

The module intentionally uses only the Python standard library.  The emitted
schemas follow JSON Schema 2020-12, while these helpers provide deterministic
validation for the subset used by the capstone and for CSV header contracts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "cap001_decision_config.json"

EXPECTED_RAW_FILES = (
    "planning_calendar.csv",
    "supplier_organisations.csv",
    "network_nodes.csv",
    "plants.csv",
    "materials.csv",
    "transformation_recipes.csv",
    "transformation_inputs.csv",
    "material_flow_approvals.csv",
    "supply_contracts.csv",
    "incoterm_rules.csv",
    "import_duty_rates.csv",
    "source_capacity.csv",
    "transformation_capacity.csv",
    "shipping_lanes.csv",
    "external_source_prices.csv",
    "conversion_costs.csv",
    "cost_allocation_rules.csv",
    "inventory_policies.csv",
    "opening_inventory.csv",
    "terminal_demand.csv",
    "supplier_performance_history.csv",
    "incident_history.csv",
    "disruption_scenarios.csv",
    "disruption_impacts.csv",
    "fx_rates.csv",
)

EXPECTED_OUTPUT_FILES = (
    "run_metadata.json",
    "metrics.json",
    "orders.csv",
    "shipments.csv",
    "production.csv",
    "inventory_cost_rollforward.csv",
    "demand_service.csv",
    "cost_component_ledger.csv",
    "cost_lineage.csv",
    "constraint_report.csv",
    "reconciliation_summary.json",
    "base_benchmark_reproduction.json",
    "dataset_comparison.csv",
    "configuration_comparison.csv",
)

# Fingerprints are derived from the v0.3 field tables and approved output
# contracts. They make a renamed, removed or reordered field a deliberate
# versioned change rather than an unnoticed regeneration.
EXPECTED_RAW_FIELD_MAP_SHA256 = "b929bdf0ebc936bdcb5693fc48b83276fb491a4eccc830aa1b1d576e4142851a"
EXPECTED_OUTPUT_FIELD_MAP_SHA256 = "41a6d3d496f1e9eaec5fc83d6ab7ff164c8421c0b2dee695b3b54b84f2d9717e"

EXPECTED_TOP_LEVEL_KEYS = {
    "$schema",
    "configuration_id",
    "configuration_version",
    "status",
    "document_control",
    "versions",
    "business",
    "planning",
    "network",
    "model",
    "pooling_and_value",
    "cost_policy",
    "scenarios",
    "scenario_semantics",
    "solution_statuses",
    "tolerances",
    "runtime_budgets",
    "reference_environment",
    "data_governance",
    "assessment",
    "release_controls",
    "controlled_open_decisions",
    "adr_register",
    "raw_contracts",
    "output_contracts",
    "application_evidence_contracts",
    "miniature_fixture_contracts",
    "professional_release",
    "required_repository_paths",
}


class ContractError(ValueError):
    """Raised when configuration or contract evidence is invalid."""


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    validate_config(config)
    return config


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate_config(config: Mapping[str, Any]) -> None:
    """Validate structural and frozen-policy invariants."""

    keys = set(config)
    _require(keys == EXPECTED_TOP_LEVEL_KEYS, f"configuration keys differ: missing={sorted(EXPECTED_TOP_LEVEL_KEYS - keys)}, unsupported={sorted(keys - EXPECTED_TOP_LEVEL_KEYS)}")
    _require(config["configuration_id"] == "CAP-001-DECISION-CONFIG", "wrong configuration_id")
    _require(config["configuration_version"] == "0.3.5", "wrong configuration version")
    _require(config["versions"] == {"capstone": "0.3.0", "data": "0.3.3", "model": "0.3.1", "rubric": "1.1.0", "schema": "0.4.0"}, "controlled versions drifted")
    _require(config["business"]["base_currency"] == "EUR", "base currency must be EUR")
    _require(len(config["business"]["plants"]) == 4, "exactly four plants required")
    _require({p["name"] for p in config["business"]["plants"]} == {"Birmingham", "Dortmund", "Katowice", "Zaragoza"}, "plant set drifted")
    planning = config["planning"]
    _require((planning["start_date"], planning["end_date"], planning["periods"]) == ("2027-01-04", "2027-03-28", 12), "planning horizon drifted")
    _require(planning["same_period_conversion"], "same-period conversion must be true")
    _require(not planning["include_work_in_progress"], "WIP is excluded from release 1")
    _require(planning["prohibit_post_horizon_arrivals"], "post-horizon arrivals must be prohibited")
    _require(planning["complete_horizon_known_at_p01"], "complete horizon must be known at P01")
    network = config["network"]
    _require(network["schema"] == "TIER_N_DAG", "network schema must be TIER_N_DAG")
    _require(network["release_instance_supplier_tiers"] == 4, "release instance must contain four supplier tiers")
    _require(network["pooling_policy"] == "WEIGHTED_AVERAGE", "pooling policy drifted")
    model = config["model"]
    _require(model["assessed_class"] == "NONCONVEX_MINLP", "assessed model class drifted")
    _require(model["reference_benchmark_dataset"] == "BASE", "reference benchmark must use BASE")
    _require(model["reference_benchmark_required"], "reference benchmark is required")
    _require(model["reference_benchmark_is_solution_evidence_not_model_input"], "reference benchmark must not be a model input")
    _require(not model["reference_benchmark_exact_allocation_match_required"], "equivalent feasible allocations must remain admissible")
    _require(model["algebraic_formulation_required"], "an algebraic formulation is required")
    _require(model["permitted_formulation_classes"] == ["MILP", "MINLP"], "permitted formulation classes drifted")
    _require(model["formulation_free_methods_prohibited"], "formulation-free methods must be prohibited")
    _require(model["permitted_method_classifications"] == ["EXACT", "RELAXED", "APPROXIMATE", "HEURISTIC"], "method classifications drifted")
    _require(config["solution_statuses"] == ["globally_optimal", "locally_optimal", "feasible_time_limited", "best_found", "infeasible", "solver_failed"], "solution status vocabulary drifted")
    _require([s["scenario_id"] for s in config["scenarios"]] == ["BASE", "SCN-01", "SCN-02", "SCN-03", "SCN-04", "SCN-05"], "scenario catalogue drifted")
    _require(sum(item["points"] for item in config["assessment"]["rubric"]) == 100, "rubric must total 100")
    _require(config["assessment"]["evaluation_mode"] == "AI_AGENT_SYSTEM_PROMPT_GUIDED_RUBRIC_REVIEW", "evaluation mode drifted")
    _require(config["assessment"]["deterministic_submission_evaluator_prohibited"], "deterministic submission evaluator must be prohibited")
    _require(config["assessment"]["candidate_evaluation_material"] == "RUBRIC_ONLY", "candidate evaluation material must be rubric-only")
    _require(config["assessment"]["evidence_checks_are_contextual_review_not_automated_gates"], "evidence checks must remain contextual")
    _require(len(config["adr_register"]) == 12, "ADR-001 through ADR-012 are required")
    _require([x["id"] for x in config["adr_register"]] == [f"ADR-{i:03d}" for i in range(1, 13)], "ADR sequence drifted")
    _require(tuple(config["raw_contracts"]) == EXPECTED_RAW_FILES, "raw contract names or order drifted")
    _require(tuple(config["output_contracts"]) == EXPECTED_OUTPUT_FILES, "output contract names or order drifted")
    raw_field_map = {name: [field["name"] for field in contract["columns"]] for name, contract in config["raw_contracts"].items()}
    raw_field_fingerprint = hashlib.sha256(json.dumps(raw_field_map, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    _require(raw_field_fingerprint == EXPECTED_RAW_FIELD_MAP_SHA256, "v0.3 raw field names or order drifted")
    output_field_map = {name: [field["name"] for field in contract["fields"]] for name, contract in config["output_contracts"].items()}
    output_field_fingerprint = hashlib.sha256(json.dumps(output_field_map, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    _require(output_field_fingerprint == EXPECTED_OUTPUT_FIELD_MAP_SHA256, "required-output field names or order drifted")
    _require(set(config["cost_policy"]["capitalised_components"]).isdisjoint(config["cost_policy"]["noncapitalised_components"]), "capitalised and non-capitalised ledgers overlap")
    _require(set(config["cost_policy"]["capitalised_components"]) | set(config["cost_policy"]["noncapitalised_components"]) == {"EXTERNAL_PURCHASE", "FREIGHT", "DUTY", "INSURANCE", "FIXED_ORDER", "FIXED_SHIPMENT", "CONVERSION", "SETUP", "OVERHEAD", "SURGE", "MARKUP", "HOLDING", "ACTIVATION", "SHORTAGE"}, "cost ledger classification is incomplete")
    _require(config["cost_policy"]["derived_intermediate_cost_inputs_prohibited"], "derived intermediate costs must be prohibited as inputs")
    _validate_contract_collection(config["raw_contracts"], "columns")
    _validate_contract_collection(config["output_contracts"], "fields")
    _validate_contract_collection(config["application_evidence_contracts"], "fields")
    _validate_contract_collection(config["miniature_fixture_contracts"], "fields")
    _require(config["professional_release"]["student_facing_yaml_prohibited"], "student-facing YAML must be prohibited")
    _validate_foreign_key_references(config["raw_contracts"])


def _validate_contract_collection(contracts: Mapping[str, Any], field_key: str) -> None:
    allowed_contract_keys = {"description", "primary_key", "unique_keys", "foreign_keys", "columns", "cross_field_rules", "format", "path", "fields"}
    allowed_field_keys = {"name", "type", "required", "nullable", "pattern", "format", "domain", "description", "unit", "enum", "const", "minimum", "maximum", "exclusiveMinimum", "minLength", "default", "additionalPropertiesType", "itemsType"}
    for name, contract in contracts.items():
        unsupported = set(contract) - allowed_contract_keys
        _require(not unsupported, f"{name}: unsupported contract keys {sorted(unsupported)}")
        fields = contract[field_key]
        names = [field["name"] for field in fields]
        _require(len(names) == len(set(names)), f"{name}: duplicate field names")
        _require(names, f"{name}: contract has no fields")
        for field in fields:
            extra = set(field) - allowed_field_keys
            _require(not extra, f"{name}.{field.get('name')}: unsupported field controls {sorted(extra)}")
            _require(field.get("type") in {"string", "integer", "number", "boolean", "object", "array"}, f"{name}.{field.get('name')}: unsupported type")
        for key in contract.get("primary_key", []):
            _require(key in names, f"{name}: primary key {key} is not a column")
        for unique in contract.get("unique_keys", []):
            _require(all(key in names for key in unique), f"{name}: unique key references an unknown column")


def _validate_foreign_key_references(contracts: Mapping[str, Any]) -> None:
    for file_name, contract in contracts.items():
        own_columns = {field["name"] for field in contract["columns"]}
        for foreign_key in contract.get("foreign_keys", []):
            _require(foreign_key["column"] in own_columns, f"{file_name}: FK column missing")
            reference_file, reference_column = foreign_key["references"].rsplit(".", 1)
            _require(reference_file in contracts, f"{file_name}: FK file {reference_file} missing")
            reference_columns = {field["name"] for field in contracts[reference_file]["columns"]}
            _require(reference_column in reference_columns, f"{file_name}: FK target {foreign_key['references']} missing")


def field_to_json_schema(field: Mapping[str, Any]) -> dict[str, Any]:
    field_type: Any = field["type"]
    if field.get("nullable"):
        field_type = [field_type, "null"]
    schema: dict[str, Any] = {"type": field_type}
    for key in ("pattern", "format", "enum", "const", "minimum", "maximum", "exclusiveMinimum", "minLength", "default"):
        if key in field:
            schema[key] = field[key]
    if field.get("nullable") and "enum" in schema and None not in schema["enum"]:
        schema["enum"] = [*schema["enum"], None]
    if field["type"] == "object" and "additionalPropertiesType" in field:
        schema["additionalProperties"] = {"type": field["additionalPropertiesType"]}
    if field["type"] == "array":
        schema["items"] = {"type": field.get("itemsType", "string")}
    if field.get("description"):
        schema["description"] = field["description"]
    return schema


def contract_to_json_schema(name: str, contract: Mapping[str, Any], field_key: str) -> dict[str, Any]:
    properties = {field["name"]: field_to_json_schema(field) for field in contract[field_key]}
    # CSV columns are always present in the row contract; nullable controls
    # whether an empty cell may become null. JSON fields follow required flags.
    if contract.get("format") == "json_object":
        required = [field["name"] for field in contract[field_key] if field.get("required", False)]
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://capstones.internal/schemas/{name}.schema.json",
            "title": name,
            "description": contract.get("description", ""),
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }
    required = list(properties)
    row = {"type": "object", "properties": properties, "required": required, "additionalProperties": False}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://capstones.internal/schemas/{name}.schema.json",
        "title": name,
        "description": contract.get("description", ""),
        "type": "array",
        "items": row,
    }


def minimal_value(field: Mapping[str, Any]) -> Any:
    if field.get("nullable") or not field.get("required", False):
        return None
    if "const" in field:
        return field["const"]
    if field.get("enum"):
        return field["enum"][0]
    kind = field["type"]
    if kind == "string":
        if field.get("format") == "date":
            return "1970-01-01"
        if field.get("format") == "date-time":
            return "1970-01-01T00:00:00Z"
        pattern = field.get("pattern", "")
        known = {
            "^P(0[1-9]|1[0-2])$": "P01",
            "^[A-Z]{2}$": "GB",
            "^[A-Z]{3}$": "EUR",
            "^NODE-[0-9]{4}$": "NODE-0001",
            "^MAT-[0-9]{4}$": "MAT-0001",
            "^SUP-[0-9]{4}$": "SUP-0001",
            "^RCP-[0-9]{5}$": "RCP-00001",
            "^APR-[0-9]{5}$": "APR-00001",
            "^CTR-[0-9]{5}$": "CTR-00001",
            "^LANE-[0-9]{5}$": "LANE-00001",
            "^COST-[0-9]{4}$": "COST-0001",
            "^DUTY-[0-9]{5}$": "DUTY-00001",
            "^IMP-[0-9]{5}$": "IMP-00001",
            "^INC-[0-9]{5}$": "INC-00001",
            "^[A-Z][A-Z0-9_]*$": "EUROPE",
            "^[A-Z][A-Z0-9_-]{1,15}$": "EXW",
            "^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$": "BASE",
            "^[a-f0-9]{64}$": "0" * 64,
        }
        return known.get(pattern, "PLACEHOLDER")
    if kind == "integer":
        if "const" in field:
            return field["const"]
        return max(int(field.get("minimum", 0)), 0)
    if kind == "number":
        if "exclusiveMinimum" in field:
            return float(field["exclusiveMinimum"]) + 1.0
        return max(float(field.get("minimum", 0.0)), 0.0)
    if kind == "boolean":
        return False
    if kind == "object":
        return {}
    if kind == "array":
        return []
    raise ContractError(f"unsupported minimal value type {kind}")


def minimal_json_object(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {field["name"]: minimal_value(field) for field in contract["fields"] if field.get("required", False)}


def validate_record(record: Mapping[str, Any], fields: Iterable[Mapping[str, Any]], *, require_all_columns: bool) -> None:
    fields_by_name = {field["name"]: field for field in fields}
    unsupported = set(record) - set(fields_by_name)
    _require(not unsupported, f"unsupported fields: {sorted(unsupported)}")
    required = set(fields_by_name) if require_all_columns else {name for name, field in fields_by_name.items() if field.get("required", False)}
    missing = required - set(record)
    _require(not missing, f"missing fields: {sorted(missing)}")
    for name, value in record.items():
        validate_scalar(value, fields_by_name[name], path=name)


def validate_scalar(value: Any, field: Mapping[str, Any], *, path: str) -> None:
    if value is None:
        _require(field.get("nullable") or not field.get("required", False), f"{path}: null is not permitted")
        return
    kind = field["type"]
    type_ok = {
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
    }[kind]
    _require(type_ok, f"{path}: expected {kind}, got {type(value).__name__}")
    if "const" in field:
        _require(value == field["const"], f"{path}: must equal {field['const']!r}")
    if "enum" in field:
        _require(value in field["enum"], f"{path}: {value!r} not in controlled domain")
    if kind == "string":
        if "pattern" in field:
            _require(re.fullmatch(field["pattern"], value) is not None, f"{path}: value does not match {field['pattern']}")
        if "minLength" in field:
            _require(len(value) >= field["minLength"], f"{path}: value is too short")
        if field.get("format") == "date":
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ContractError(f"{path}: invalid ISO date") from exc
        if field.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ContractError(f"{path}: invalid ISO timestamp") from exc
            _require(value.endswith("Z") or re.search(r"[+-][0-9]{2}:[0-9]{2}$", value) is not None, f"{path}: timezone is required")
    if kind in {"integer", "number"}:
        if "minimum" in field:
            _require(value >= field["minimum"], f"{path}: below minimum")
        if "exclusiveMinimum" in field:
            _require(value > field["exclusiveMinimum"], f"{path}: not above exclusive minimum")
        if "maximum" in field:
            _require(value <= field["maximum"], f"{path}: above maximum")
    if kind == "object" and "additionalPropertiesType" in field:
        expected = field["additionalPropertiesType"]
        for child_name, child_value in value.items():
            validate_scalar(child_value, {"type": expected, "required": True}, path=f"{path}.{child_name}")
    if kind == "array" and "itemsType" in field:
        for index, child_value in enumerate(value):
            validate_scalar(child_value, {"type": field["itemsType"], "required": True}, path=f"{path}[{index}]")


def coerce_csv_value(text: str, field: Mapping[str, Any]) -> Any:
    if text == "":
        return None
    kind = field["type"]
    if kind == "string":
        return text
    if kind == "integer":
        return int(text)
    if kind == "number":
        return float(text)
    if kind == "boolean":
        lowered = text.lower()
        if lowered not in {"true", "false"}:
            raise ContractError(f"{field['name']}: expected true or false")
        return lowered == "true"
    raise ContractError(f"CSV field {field['name']} uses unsupported type {kind}")


def validate_csv_file(path: Path, contract: Mapping[str, Any]) -> int:
    fields = contract.get("columns", contract.get("fields"))
    expected_header = [field["name"] for field in fields]
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require(reader.fieldnames == expected_header, f"{path}: header drifted; expected {expected_header}, got {reader.fieldnames}")
        count = 0
        fields_by_name = {field["name"]: field for field in fields}
        for row_number, row in enumerate(reader, start=2):
            try:
                typed = {name: coerce_csv_value(value, fields_by_name[name]) for name, value in row.items()}
                validate_record(typed, fields, require_all_columns=True)
            except (ContractError, ValueError) as exc:
                raise ContractError(f"{path}:{row_number}: {exc}") from exc
            count += 1
    return count


def validate_json_file(path: Path, contract: Mapping[str, Any]) -> None:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    validate_record(value, contract["fields"], require_all_columns=False)


def resolve_data_dir(default: Path | None = None) -> Path:
    value = os.environ.get("CAPSTONE_DATA_DIR")
    if value:
        return Path(value).resolve()
    if default is None:
        raise ContractError("CAPSTONE_DATA_DIR is not set and no default was supplied")
    return default.resolve()


TOLERANCE_KINDS = ("quantity", "value", "unit_cost")


def tolerance_scale(actual: float, expected: float) -> float:
    return max(abs(actual), abs(expected))


def tolerance_for(actual: float, expected: float, absolute: float, relative: float) -> float:
    return max(absolute, relative * tolerance_scale(actual, expected))


def residuals(actual: float, expected: float) -> tuple[float, float]:
    absolute_residual = abs(actual - expected)
    scale = tolerance_scale(actual, expected)
    relative_residual = absolute_residual / scale if scale > 0 else 0.0
    return absolute_residual, relative_residual


def within_tolerance(actual: float, expected: float, absolute: float, relative: float) -> bool:
    absolute_residual, _ = residuals(actual, expected)
    return absolute_residual <= tolerance_for(actual, expected, absolute, relative)


def tolerance_pair(config: Mapping[str, Any], kind: str) -> tuple[float, float]:
    _require(kind in TOLERANCE_KINDS, f"unknown tolerance kind: {kind}")
    entry = config["tolerances"][kind]
    return entry["absolute"], entry["relative"]


def validate_raw_data_directory(data_dir: Path, config: Mapping[str, Any]) -> dict[str, int]:
    data_dir = data_dir.resolve()
    _require(data_dir.is_dir(), f"raw-data directory does not exist: {data_dir}")
    actual = {path.name for path in data_dir.iterdir() if path.is_file()}
    expected = set(config["raw_contracts"])
    _require(actual == expected, f"raw-data file set drifted: missing={sorted(expected - actual)}, unsupported={sorted(actual - expected)}")
    before = {name: sha256_path(data_dir / name) for name in expected}
    counts = {name: validate_csv_file(data_dir / name, config["raw_contracts"][name]) for name in config["raw_contracts"]}
    after = {name: sha256_path(data_dir / name) for name in expected}
    _require(before == after, "raw-data validation modified authoritative inputs")
    return counts
