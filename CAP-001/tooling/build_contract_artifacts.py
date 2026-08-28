"""Generate CAP-001 controlled contracts from the decision configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from tooling.contract_runtime import (
    CONFIG_PATH,
    ROOT,
    canonical_json,
    contract_to_json_schema,
    load_config,
    sha256_bytes,
)


RELEASE_ROOT = Path("student_release/CAP-001-tier-n-release")
GENERATED_MANIFEST = Path("generated/contracts/CAP-001_ARTIFACT_MANIFEST.json")
GENERATED_ONLY_ROOTS = (
    Path("schemas"),
    Path("adrs"),
    Path("docs/generated"),
    Path("generated/contracts"),
)
# The populated miniature fixture is authored independently of this contract
# and scaffold generator. Excluding these paths prevents real fixture data
# from being treated as drift or as stale generated content.
AUTHORED_PREFIXES = (
    Path("reference/base_benchmark"),
    Path("adrs/ADR-005.md"),
    Path("adrs/ADR-008.md"),
)


def _text(value: str) -> bytes:
    return value.encode("utf-8")


def _json(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def _schema_name(contract_name: str) -> str:
    return f"{Path(contract_name).stem}.schema.json"


def _shape_schema(value: Any, *, title: str | None = None) -> dict[str, Any]:
    """Build a strict structural schema from a controlled example value."""

    if isinstance(value, dict):
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {key: _shape_schema(child) for key, child in value.items()},
            "required": list(value),
            "additionalProperties": False,
        }
    elif isinstance(value, list):
        variants: list[dict[str, Any]] = []
        seen: set[str] = set()
        for child in value:
            child_schema = _shape_schema(child)
            signature = json.dumps(child_schema, sort_keys=True)
            if signature not in seen:
                seen.add(signature)
                variants.append(child_schema)
        if not variants:
            item_schema: dict[str, Any] = {}
        elif len(variants) == 1:
            item_schema = variants[0]
        else:
            item_schema = {"anyOf": variants}
        schema = {"type": "array", "items": item_schema}
    elif isinstance(value, bool):
        schema = {"type": "boolean"}
    elif isinstance(value, int):
        schema = {"type": "integer"}
    elif isinstance(value, float):
        schema = {"type": "number"}
    elif value is None:
        schema = {"type": "null"}
    else:
        schema = {"type": "string"}
    if title:
        schema["title"] = title
    return schema


def _release_manifest_shape(config: Mapping[str, Any]) -> dict[str, Any]:
    """Describe the author-owned release manifest, not a candidate submission."""

    return {
        "release_id": "CAP-001-PROFESSIONAL-RELEASE",
        "release_version": config["versions"]["capstone"],
        "configuration_version": config["configuration_version"],
        "data_contract_version": config["versions"]["data"],
        "schema_version": config["versions"]["schema"],
        "rubric_version": config["versions"]["rubric"],
        "dataset_package_ids": list(config["professional_release"]["dataset_package_ids"]),
        "files": [],
        "dataset_packages": {},
    }


def _dictionary(config: Mapping[str, Any]) -> str:
    lines = [
        "# CAP-001 Data Dictionary",
        "",
        "> Generated from `config/cap001_decision_config.json`. Do not edit directly.",
        "",
        f"Configuration version: `{config['configuration_version']}`",
        f"Schema version: `{config['versions']['schema']}`",
        "",
        "## Conventions",
        "",
        "- UTF-8 CSV with one header row.",
        "- Stable string identifiers; no business meaning is encoded in numeric suffixes.",
        "- ISO-8601 dates and timezone-aware timestamps.",
        "- Explicit currency and unit fields; probabilities and rates use 0–1 unless stated otherwise.",
        "- Empty cells represent declared nullable values only. Literal placeholder strings such as `N/A` are invalid.",
        "- Foreign keys and relationship rules are authoritative as listed below.",
        "",
        "## Raw-data contracts",
        "",
    ]
    for file_name, contract in config["raw_contracts"].items():
        lines.extend([f"### `{file_name}`", "", contract["description"], ""])
        lines.append(f"Primary key: `{', '.join(contract['primary_key'])}`")
        if contract.get("foreign_keys"):
            lines.append("")
            lines.append("Foreign keys:")
            lines.append("")
            for foreign_key in contract["foreign_keys"]:
                suffix = " (nullable)" if foreign_key.get("nullable") else ""
                lines.append(f"- `{foreign_key['column']}` → `{foreign_key['references']}`{suffix}")
        lines.extend(["", "| Column | Type | Required/nullable | Domain or constraints | Definition |", "|---|---|---|---|---|"])
        for field in contract["columns"]:
            required = "required"
            if field.get("nullable") or not field.get("required", False):
                required = "nullable"
            constraints: list[str] = []
            if "const" in field:
                constraints.append(f"constant `{field['const']}`")
            if "enum" in field:
                constraints.append(", ".join(f"`{item}`" for item in field["enum"]))
            if "pattern" in field:
                constraints.append(f"pattern `{field['pattern']}`")
            if "format" in field:
                constraints.append(field["format"])
            if "domain" in field:
                constraints.append(field["domain"])
            if "unit" in field:
                constraints.append(f"unit: {field['unit']}")
            if "minimum" in field:
                constraints.append(f">= {field['minimum']}")
            if "exclusiveMinimum" in field:
                constraints.append(f"> {field['exclusiveMinimum']}")
            if "maximum" in field:
                constraints.append(f"<= {field['maximum']}")
            description = field.get("description", "").replace("|", "\\|")
            lines.append(f"| `{field['name']}` | {field['type']} | {required} | {'; '.join(constraints) or '—'} | {description} |")
        if contract.get("cross_field_rules"):
            lines.extend(["", "Cross-field rules:", ""])
            lines.extend(f"- {rule}" for rule in contract["cross_field_rules"])
        lines.append("")
    lines.extend(["## Required-output contracts", ""])
    for file_name, contract in config["output_contracts"].items():
        lines.extend([f"### `{file_name}`", "", f"Path: `{contract['path']}`", "", contract["description"], ""])
        lines.extend(["| Field | Type | Required/nullable | Definition/constraints |", "|---|---|---|---|"])
        for field in contract["fields"]:
            status = "required" if field.get("required", False) else "nullable/conditional"
            constraints = []
            if "enum" in field:
                constraints.append(", ".join(f"`{value}`" for value in field["enum"]))
            if "const" in field:
                constraints.append(f"constant `{field['const']}`")
            constraints.append(field.get("description", ""))
            lines.append(f"| `{field['name']}` | {field['type']} | {status} | {'; '.join(x for x in constraints if x) or '—'} |")
        lines.append("")
    lines.extend(["## Application data-governance evidence contracts", ""])
    for file_name, contract in config["application_evidence_contracts"].items():
        lines.extend([f"### `{file_name}`", "", f"Path: `{contract['path']}`", "", contract["description"], ""])
        lines.extend(["| Field | Type | Required/nullable | Definition/constraints |", "|---|---|---|---|"])
        for field in contract["fields"]:
            status = "required" if field.get("required", False) else "nullable/conditional"
            constraints = []
            if "enum" in field:
                constraints.append(", ".join(f"`{value}`" for value in field["enum"]))
            if "const" in field:
                constraints.append(f"constant `{field['const']}`")
            constraints.append(field.get("description", ""))
            lines.append(f"| `{field['name']}` | {field['type']} | {status} | {'; '.join(x for x in constraints if x) or '—'} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _configuration_summary(config: Mapping[str, Any]) -> str:
    accepted_adrs = sum(item["status"] == "ACCEPTED" for item in config["adr_register"])
    proposed_adrs = sum(item["status"] == "PROPOSED" for item in config["adr_register"])
    return f"""# CAP-001 Configuration Summary

> Generated from `config/cap001_decision_config.json`. Do not edit directly.

| Control | Value |
|---|---|
| Configuration | `{config['configuration_version']}` |
| Capstone/data/model | `{config['versions']['capstone']}` / `{config['versions']['data']}` / `{config['versions']['model']}` |
| Network | `{config['network']['schema']}`, four supplier tiers plus four plants |
| Pooling | `{config['network']['pooling_policy']}` |
| Reference benchmark | `{config['model']['reference_benchmark_name']}` on `{config['model']['reference_benchmark_dataset']}` |
| Assessed semantics | `{config['model']['assessed_name']}` |
| Raw contracts | {len(config['raw_contracts'])} |
| Output contracts | {len(config['output_contracts'])} |
| Supplied dataset snapshots | {', '.join(s['scenario_id'] for s in config['scenarios'])} |
| ADRs | {len(config['adr_register'])}: {accepted_adrs} accepted, {proposed_adrs} proposed |

## Release control

These generated contracts are necessary but not sufficient for release. The
ADRs, miniature fixture, generated datasets, benchmark and release validations
must also remain current.
"""


def _adr_template() -> str:
    return """# ADR-### — Concise decision name

| Field | Value |
|---|---|
| Status | PROPOSED |
| Owner | Named role and individual |
| Reviewers | Named roles and individuals |
| Approval date | Pending |

## Context

Problem, constraints and affected stakeholders.

## Decision

Approved implementation position or an explicit statement that resolution is pending.

## Alternatives considered

Credible alternatives and reasons for selection or rejection.

## Mathematical and accounting consequences

Effects on equations, bounds, objective and reconciliation.

## Data consequences

Effects on schemas, generation and validation.

## Assessment consequences

Effects on the brief, outputs, rubric and evidence-based review.

## Affected artefacts

Files or packages that must be regenerated.
"""


def _adr_record(item: Mapping[str, Any]) -> str:
    reviewers = ", ".join(item["reviewer_roles"])
    return f"""# {item['id']} — {item['title']}

| Field | Value |
|---|---|
| Status | {item['status']} |
| Owner | {item['owner_role']} |
| Reviewers | {reviewers} |
| Approval date | Pending |

## Context

The CAP-001 v0.3 specification fixes the modelling direction and requires this
decision to be resolved before release. The shared configuration records the
currently frozen position and identifies any remaining controlled-open detail.

## Decision

Proposed. The frozen v0.3 specification position remains authoritative. Exact
implementation detail must be approved here before it can change configuration,
generated contracts or evaluation behaviour.

## Alternatives considered

To be completed during ADR review. Silent implementation choices are prohibited.

## Mathematical and accounting consequences

To be made explicit before approval, including effects on equations, bounds,
objective stages, solver classification and reconciliation.

## Data consequences

Any approved change must update the decision configuration and regenerate the
data dictionary, schemas, empty contracts and affected validators.

## Assessment consequences

Any candidate-visible or assessor-visible consequence must be reflected in the
brief, output contract, rubric and private AI review guide.

## Affected artefacts

- `config/cap001_decision_config.json`
- generated schemas and data dictionary
- affected generators and private viability models
- candidate brief and assessor-side review guidance
"""


def planned_artifacts(config: Mapping[str, Any]) -> dict[Path, bytes]:
    artifacts: dict[Path, bytes] = {}

    # Strict structural control schemas.
    decision_schema = _shape_schema(config, title="CAP-001 decision configuration")
    decision_schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://capstones.internal/schemas/decision_config.schema.json"})
    artifacts[Path("schemas/decision_config.schema.json")] = _json(decision_schema)

    release_example = _release_manifest_shape(config)
    release_schema = _shape_schema(release_example, title="CAP-001 release manifest")
    release_schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://capstones.internal/schemas/release_manifest.schema.json"})
    release_schema["properties"]["dataset_package_ids"] = {"type": "array", "items": {"type": "string"}, "minItems": 6, "uniqueItems": True}
    release_schema["properties"]["files"] = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "bytes": {"type": "integer", "minimum": 0},
            },
            "required": ["path", "sha256", "bytes"],
            "additionalProperties": False,
        },
    }
    release_schema["properties"]["dataset_packages"] = {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "manifest_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "file_count": {"type": "integer", "minimum": 25},
                "row_count": {"type": "integer", "minimum": 1},
            },
            "required": ["manifest_sha256", "file_count", "row_count"],
            "additionalProperties": False,
        },
    }
    artifacts[Path("schemas/release_manifest.schema.json")] = _json(release_schema)

    # Data, result and application-evidence schemas.
    for name, contract in config["raw_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "columns")
        schema_path = Path("schemas/raw_data") / _schema_name(name)
        artifacts[schema_path] = _json(schema)

    for name, contract in config["output_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "fields")
        schema_path = Path("schemas/required_outputs") / _schema_name(name)
        artifacts[schema_path] = _json(schema)

    for name, contract in config["application_evidence_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "fields")
        schema_path = Path("schemas/application_evidence") / _schema_name(name)
        artifacts[schema_path] = _json(schema)

    for name, contract in config["miniature_fixture_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "fields")
        schema_path = Path("schemas/miniature_fixture") / _schema_name(name)
        artifacts[schema_path] = _json(schema)

    # Generated documentation and ADR records.
    dictionary = _dictionary(config)
    artifacts[Path("docs/generated/CAP-001_DATA_DICTIONARY.md")] = _text(dictionary)
    artifacts[Path("docs/generated/CAP-001_CONFIGURATION_SUMMARY.md")] = _text(_configuration_summary(config))
    artifacts[Path("adrs/ADR_TEMPLATE.md")] = _text(_adr_template())
    artifacts[Path("adrs/register.json")] = _json({"configuration_version": config["configuration_version"], "adrs": config["adr_register"]})
    for item in config["adr_register"]:
        if item["id"] in {"ADR-005", "ADR-008"}:
            continue
        artifacts[Path("adrs") / f"{item['id']}.md"] = _text(_adr_record(item))

    # Private control repository skeleton.
    private_paths = config["required_repository_paths"]["private_control"]
    for directory in private_paths:
        marker = Path(directory) / ".gitkeep"
        if _is_authored_path(Path(directory)) or _is_authored_path(marker):
            continue
        artifacts[marker] = b""

    # Source digest used by drift and lineage controls.
    config_digest = sha256_bytes(CONFIG_PATH.read_bytes())
    artifacts[Path("config/cap001_decision_config.sha256")] = _text(f"{config_digest}  cap001_decision_config.json\n")

    manifest_entries = [
        {"path": path.as_posix(), "sha256": sha256_bytes(content), "bytes": len(content)}
        for path, content in sorted(artifacts.items(), key=lambda item: item[0].as_posix())
    ]
    artifacts[GENERATED_MANIFEST] = _json({
        "configuration_id": config["configuration_id"],
        "configuration_version": config["configuration_version"],
        "configuration_sha256": config_digest,
        "generated_artifacts": manifest_entries,
    })
    return artifacts


def write_artifacts(artifacts: Mapping[Path, bytes]) -> None:
    for relative_path, content in artifacts.items():
        target = ROOT / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if target.suffix == ".sh":
            target.chmod(0o755)


def _is_authored_path(relative_path: Path) -> bool:
    return any(relative_path == prefix or prefix in relative_path.parents for prefix in AUTHORED_PREFIXES)


def check_artifacts(artifacts: Mapping[Path, bytes]) -> list[str]:
    errors: list[str] = []
    for relative_path, expected in artifacts.items():
        target = ROOT / relative_path
        if not target.exists():
            errors.append(f"missing generated artefact: {relative_path}")
            continue
        actual = target.read_bytes()
        if actual != expected:
            errors.append(f"generated artefact drifted: {relative_path}")
    expected_paths = set(artifacts)
    actual_paths: set[Path] = set()
    for relative_root in GENERATED_ONLY_ROOTS:
        root = ROOT / relative_root
        if root.exists():
            actual_paths.update(path.relative_to(ROOT) for path in root.rglob("*") if path.is_file())
    for extra in sorted(actual_paths - expected_paths, key=lambda path: path.as_posix()):
        if _is_authored_path(extra):
            continue
        errors.append(f"unsupported stale generated artefact: {extra}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if committed derived artefacts differ from the configuration")
    args = parser.parse_args(argv)
    config = load_config()
    artifacts = planned_artifacts(config)
    if args.check:
        errors = check_artifacts(artifacts)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(f"CAP-001 generated artefacts are current ({len(artifacts)} files).")
        return 0
    write_artifacts(artifacts)
    print(f"Generated {len(artifacts)} CAP-001 artefacts from {CONFIG_PATH.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
