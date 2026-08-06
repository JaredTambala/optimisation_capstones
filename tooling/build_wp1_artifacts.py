"""Generate every derived WP1 artefact from the CAP-001 decision config."""

from __future__ import annotations

import argparse
import csv
import io
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
    minimal_json_object,
    sha256_bytes,
)


RELEASE_ROOT = Path("student_release/CAP-001-tier-n-release")
SUBMISSION_ROOT = Path("templates/student_submission")
GENERATED_MANIFEST = Path("generated/WP1_ARTIFACT_MANIFEST.json")
GENERATED_ONLY_ROOTS = (
    Path("schemas"),
    Path("adrs"),
    Path("docs/generated"),
    Path("generated"),
    RELEASE_ROOT,
    SUBMISSION_ROOT,
)


def _text(value: str) -> bytes:
    return value.encode("utf-8")


def _json(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def _csv_header(fields: list[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow([field["name"] for field in fields])
    return _text(stream.getvalue())


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


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _yaml(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            if isinstance(child, (dict, list)) and child:
                lines.append(f"{prefix}{key}:")
                lines.append(_yaml(child, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(child) if not isinstance(child, (dict, list)) else '[]' if isinstance(child, list) else '{}'}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for child in value:
            if isinstance(child, dict):
                first, *rest = child.items()
                lines.append(f"{prefix}- {first[0]}: {_yaml_scalar(first[1])}")
                for key, nested in rest:
                    if isinstance(nested, (dict, list)):
                        lines.append(f"{prefix}  {key}:")
                        lines.append(_yaml(nested, indent + 4))
                    else:
                        lines.append(f"{prefix}  {key}: {_yaml_scalar(nested)}")
            else:
                lines.append(f"{prefix}- {_yaml_scalar(child)}")
        return "\n".join(lines)
    return f"{prefix}{_yaml_scalar(value)}"


def _default_case(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "capstone_id": "CAP-001",
        "capstone_version": config["versions"]["capstone"],
        "data_version": config["versions"]["data"],
        "model_version": config["versions"]["model"],
        "default_scenario_id": "BASE",
        "planning_horizon": {
            "start": config["planning"]["start_date"],
            "end": config["planning"]["end_date"],
            "periods": config["planning"]["periods"],
        },
        "network": {
            "schema": config["network"]["schema"],
            "release_instance_supplier_tiers": config["network"]["release_instance_supplier_tiers"],
            "pooling_policy": config["network"]["pooling_policy"],
        },
        "model_contract": {
            "baseline": config["model"]["baseline_name"],
            "assessed_model": config["model"]["assessed_name"],
            "service_objective": config["model"]["service_objective"],
            "allow_declared_approximation": config["model"]["allow_declared_approximation"],
        },
        "runtime_budgets": config["runtime_budgets"],
        "tolerances": config["tolerances"],
        "random_seeds": [42, 314, 2718],
    }


def _release_manifest_template(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "capstone_id": "CAP-001",
        "capstone_version": config["versions"]["capstone"],
        "data_version": config["versions"]["data"],
        "model_version": config["versions"]["model"],
        "rubric_version": config["versions"]["rubric"],
        "default_scenario_id": "BASE",
        "planning_horizon": {"start": config["planning"]["start_date"], "end": config["planning"]["end_date"]},
        "model_contract": {"baseline": "fixed_price_milp", "assessed_model": "recursive_cost_minlp"},
        "required_outputs": [contract["path"] for contract in config["output_contracts"].values()],
        "supported_commands": ["setup", "test", "solve_baseline", "solve_default", "run_app"],
        "files": [],
        "row_counts": {},
        "template_only": True,
    }


def _dictionary(config: Mapping[str, Any]) -> str:
    lines = [
        "# CAP-001 Data Dictionary",
        "",
        "> Generated from `config/cap001_decision_config.json`. Do not edit directly.",
        "",
        f"Configuration version: `{config['configuration_version']}`  ",
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
        lines.extend([f"### `{file_name}`", "", f"Path: `{contract['path']}`  ", contract["description"], ""])
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
    return f"""# CAP-001 WP1 Configuration Summary

> Generated from `config/cap001_decision_config.json`. Do not edit directly.

| Control | Value |
|---|---|
| Configuration | `{config['configuration_version']}` |
| Capstone/data/model | `{config['versions']['capstone']}` / `{config['versions']['data']}` / `{config['versions']['model']}` |
| Network | `{config['network']['schema']}`, four supplier tiers plus four plants |
| Pooling | `{config['network']['pooling_policy']}` |
| Baseline | `{config['model']['baseline_name']}` |
| Assessed semantics | `{config['model']['assessed_name']}` |
| Raw contracts | {len(config['raw_contracts'])} |
| Output contracts | {len(config['output_contracts'])} |
| Scenarios | {', '.join(s['scenario_id'] for s in config['scenarios'])} |
| ADRs | {len(config['adr_register'])}, all proposed pending controlled approval |

## Release block

WP1 establishes contracts; it does not approve the controlled-open decisions.
No student release may be issued until the ADRs, miniature fixture, generator,
reference routes and all acceptance checks pass.
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

Effects on the brief, outputs, quality gates and scoring.

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

Any student-visible or evaluator-visible consequence must be reflected in the
brief, output contract, quality gates, rubric evidence and defence guide.

## Affected artefacts

- `config/cap001_decision_config.json`
- generated schemas and data dictionary
- generator and reference models in later work packages
- student brief and evaluator controls in later work packages
"""


def _scaffold_readme(name: str, purpose: str) -> str:
    return f"""# {name}

{purpose}

This directory is a WP1 scaffold. Later work packages may add implementation
files, but they must consume or verify against the shared decision configuration.
"""


def _template_document(title: str, purpose: str) -> str:
    return f"""# {title}

> WP1 controlled template. Populate in the responsible later work package.

{purpose}

The completed document must remain consistent with CAP-001 v0.3, approved ADRs
and `config/default_case.yaml`.
"""


def _script_placeholder(command_name: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
echo "{command_name} is a WP1 scaffold and is not implemented yet." >&2
exit 2
"""


def planned_artifacts(config: Mapping[str, Any]) -> dict[Path, bytes]:
    artifacts: dict[Path, bytes] = {}

    # Strict structural control schemas.
    decision_schema = _shape_schema(config, title="CAP-001 decision configuration")
    decision_schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://capstones.internal/schemas/decision_config.schema.json"})
    artifacts[Path("schemas/decision_config.schema.json")] = _json(decision_schema)

    submission_schema = _shape_schema(config["submission_manifest_example"], title="CAP-001 submission manifest")
    submission_schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://capstones.internal/schemas/submission_manifest.schema.json"})
    artifacts[Path("schemas/submission_manifest.schema.json")] = _json(submission_schema)

    release_example = _release_manifest_template(config)
    release_schema = _shape_schema(release_example, title="CAP-001 release manifest")
    release_schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://capstones.internal/schemas/release_manifest.schema.json"})
    release_schema["properties"]["required_outputs"] = {"type": "array", "items": {"type": "string"}, "minItems": 1, "uniqueItems": True}
    release_schema["properties"]["supported_commands"] = {"type": "array", "items": {"type": "string"}, "minItems": 5, "uniqueItems": True}
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
    release_schema["properties"]["row_counts"] = {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0}}
    artifacts[Path("schemas/release_manifest.schema.json")] = _json(release_schema)

    # Raw and output schemas and header-only/minimal valid examples.
    for name, contract in config["raw_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "columns")
        schema_path = Path("schemas/raw_data") / _schema_name(name)
        artifacts[schema_path] = _json(schema)
        artifacts[RELEASE_ROOT / schema_path] = _json(schema)
        artifacts[RELEASE_ROOT / "data/raw" / name] = _csv_header(contract["columns"])
        artifacts[RELEASE_ROOT / "data/miniature_fixture/inputs" / name] = _csv_header(contract["columns"])

    for name, contract in config["output_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "fields")
        schema_path = Path("schemas/required_outputs") / _schema_name(name)
        artifacts[schema_path] = _json(schema)
        artifacts[RELEASE_ROOT / schema_path] = _json(schema)
        example_path = RELEASE_ROOT / "reference/empty_contracts" / contract["path"]
        if contract["format"] == "json_object":
            artifacts[example_path] = _json(minimal_json_object(contract))
        else:
            artifacts[example_path] = _csv_header(contract["fields"])

    for name, contract in config["miniature_fixture_contracts"].items():
        schema = contract_to_json_schema(Path(name).stem, contract, "fields")
        schema_path = Path("schemas/miniature_fixture") / _schema_name(name)
        artifacts[schema_path] = _json(schema)
        artifacts[RELEASE_ROOT / schema_path] = _json(schema)
        target = RELEASE_ROOT / "data/miniature_fixture" / name
        if name == "fixture_manifest.json":
            artifacts[target] = _json({
                "fixture_id": "CAP-001-MINIATURE",
                "fixture_version": config["configuration_version"],
                "period_count": 5,
                "supplier_tier_count": 4,
                "input_files": list(config["raw_contracts"]),
                "expected_reconciliation_files": ["fixture_control_totals.csv", "recursive_cost_reconciliation.csv"],
            })
        elif contract["format"] == "json_object":
            artifacts[target] = _json(minimal_json_object(contract))
        else:
            artifacts[target] = _csv_header(contract["fields"])
            artifacts[RELEASE_ROOT / "data/miniature_fixture/expected_reconciliation" / name] = _csv_header(contract["fields"])

    recursive_reconciliation = config["output_contracts"]["recursive_cost_reconciliation.csv"]
    artifacts[RELEASE_ROOT / "data/miniature_fixture/expected_reconciliation/recursive_cost_reconciliation.csv"] = _csv_header(recursive_reconciliation["fields"])

    # Generated documentation and ADR records.
    dictionary = _dictionary(config)
    artifacts[Path("docs/generated/CAP-001_DATA_DICTIONARY.md")] = _text(dictionary)
    artifacts[RELEASE_ROOT / "DATA_DICTIONARY.md"] = _text(dictionary)
    artifacts[Path("docs/generated/WP1_CONFIGURATION_SUMMARY.md")] = _text(_configuration_summary(config))
    artifacts[Path("adrs/ADR_TEMPLATE.md")] = _text(_adr_template())
    artifacts[Path("adrs/register.json")] = _json({"configuration_version": config["configuration_version"], "adrs": config["adr_register"]})
    for item in config["adr_register"]:
        artifacts[Path("adrs") / f"{item['id']}.md"] = _text(_adr_record(item))

    # Default case and student/release manifests.
    default_case = _default_case(config)
    artifacts[RELEASE_ROOT / "config/default_case.yaml"] = _text(_yaml(default_case) + "\n")
    artifacts[RELEASE_ROOT / "release_manifest.template.json"] = _json(release_example)
    artifacts[RELEASE_ROOT / "starter/submission.yaml"] = _text(_yaml(config["submission_manifest_example"]) + "\n")
    artifacts[SUBMISSION_ROOT / "submission.yaml"] = _text(_yaml(config["submission_manifest_example"]) + "\n")

    # Student release document/template skeleton.
    release_docs = {
        "CAPSTONE_BRIEF.md": ("CAP-001 Capstone Brief", "Controlled student task and business context."),
        "TASK_REQUIREMENTS.md": ("CAP-001 Task Requirements", "Normative model, evidence, application and assessment requirements."),
        "COST_POLICY.md": ("CAP-001 Cost Policy", "Capitalisation, markup, allocation and single-ledger rules."),
        "SCENARIO_CATALOGUE.md": ("CAP-001 Scenario Catalogue", "BASE and SCN-01 through SCN-05 definitions and run modes."),
        "PRODUCTION_EXTENSION.md": ("CAP-001 Production Extension", "Integration, ownership, scale, monitoring, audit and fallback expectations."),
        "AI_NATIVE_WORKING_GUIDE.md": ("AI-Native Working Guide", "Expected AI use, validation duties and technical accountability."),
    }
    for name, (title, purpose) in release_docs.items():
        artifacts[RELEASE_ROOT / name] = _text(_template_document(title, purpose))
    starter_templates = {
        "README_TEMPLATE.md": ("Submission README", "Explain setup, commands, architecture and evidence paths."),
        "model_specification_template.md": ("Model Specification", "Document sets, variables, equations, bounds and assumptions."),
        "validation_report_template.md": ("Validation Report", "Present fixture, physical, value, scenario and robustness evidence."),
        "solver_strategy_template.md": ("Solver Strategy", "Classify the method and report settings, starts, bounds, gaps and status."),
        "production_readiness_template.md": ("Production Readiness", "Describe integration, security, scale, monitoring and fallback."),
        "AI_USAGE_TEMPLATE.md": ("AI Usage", "Record material assistance, manual checks, corrections, rejections and validation."),
    }
    for name, (title, purpose) in starter_templates.items():
        artifacts[RELEASE_ROOT / "starter" / name] = _text(_template_document(title, purpose))

    # Private control repository skeleton.
    private_paths = config["required_repository_paths"]["private_control"]
    private_root = Path("capstones/CAP-001")
    artifacts[private_root / "README.md"] = _text(_scaffold_readme("CAP-001 private control", "Private generator, fixture, reference and evaluation implementation."))
    for directory in private_paths:
        artifacts[Path(directory) / ".gitkeep"] = b""

    # Release paths not otherwise materialized.
    for directory in config["required_repository_paths"]["student_release"]:
        marker = RELEASE_ROOT / directory / ".gitkeep"
        if not any(path.parent == marker.parent for path in artifacts):
            artifacts[marker] = b""

    # Submission repository skeleton and controlled placeholders.
    artifacts[SUBMISSION_ROOT / "README.md"] = _text(_scaffold_readme("CAP-001 student submission", "Starter structure for the consultant submission."))
    artifacts[SUBMISSION_ROOT / "AI_USAGE.md"] = _text(_template_document("AI Usage", "Record material AI assistance and validation."))
    for directory in config["required_repository_paths"]["submission_template"]:
        marker = SUBMISSION_ROOT / directory / ".gitkeep"
        if not any(path.parent == marker.parent for path in artifacts):
            artifacts[marker] = b""
    for name in ("setup.sh", "run_tests.sh", "run_baseline.sh", "run_model.sh", "run_app.sh"):
        artifacts[SUBMISSION_ROOT / "scripts" / name] = _text(_script_placeholder(name))
    for report in ("model_specification.md", "validation_report.md", "solver_strategy.md", "assumptions_and_limitations.md", "production_readiness.md"):
        title = report.removesuffix(".md").replace("_", " ").title()
        artifacts[SUBMISSION_ROOT / "reports" / report] = _text(_template_document(title, "Student-authored controlled evidence."))

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
        print(f"WP1 generated artefacts are current ({len(artifacts)} files).")
        return 0
    write_artifacts(artifacts)
    print(f"Generated {len(artifacts)} WP1 artefacts from {CONFIG_PATH.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
