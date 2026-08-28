"""Assemble and verify the CAP-001 professional candidate release."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

from tooling.contract_runtime import (
    EXPECTED_RAW_FILES,
    ROOT,
    canonical_json,
    load_config,
    sha256_bytes,
)


RELEASE_ROOT = ROOT / "student_release" / "CAP-001-tier-n-release"
DATASET_SOURCE_ROOT = ROOT / "capstones" / "CAP-001" / "generated" / "datasets"
BENCHMARK_SOURCE_ROOT = ROOT / "capstones" / "CAP-001" / "reference" / "base_benchmark"

PROJECTED_DOCUMENTS = {
    "CAPSTONE_BRIEF.md": ROOT / "docs" / "CAP-001_CONSULTANT_ENGAGEMENT_BRIEF.md",
    "TASK_REQUIREMENTS.md": ROOT / "docs" / "CAP-001_CANDIDATE_TASK_REQUIREMENTS.md",
    "APPLICATION_AND_EVIDENCE_GUIDE.md": ROOT / "docs" / "CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md",
}


def _text(value: str) -> bytes:
    return value.encode("utf-8")


def _json(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def _candidate_projection(
    source: Path,
    *,
    omit_section_eight: bool = False,
    omit_section_nine: bool = False,
) -> bytes:
    """Remove authoring control language while preserving frozen requirements."""

    text = source.read_text(encoding="utf-8")
    text = re.sub(r"\n## Document control\n.*?(?=\n## )", "", text, count=1, flags=re.S)
    if omit_section_eight:
        text = re.sub(r"\n## 8\..*\Z", "\n", text, count=1, flags=re.S)
    if omit_section_nine:
        text = re.sub(r"\n## 9\..*\Z", "\n", text, count=1, flags=re.S)
    replacements = {
        "`docs/CAP-001_CONSULTANT_ENGAGEMENT_BRIEF.md`": "`CAPSTONE_BRIEF.md`",
        "`docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md`": "`TASK_REQUIREMENTS.md`",
        "`docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md`": "`APPLICATION_AND_EVIDENCE_GUIDE.md`",
        "`docs/CONSULTANT_ENGAGEMENT_AND_ASSESSMENT_DESIGN_CONTRACT.md`": "the controlled engagement design",
        "Requirement identifiers are frozen within WP8 and mapped to business purpose,\nevidence and rubric criteria in the WP8 traceability matrix. No identifier": (
            "Requirement identifiers are stable within this release and map to business\n"
            "purpose, evidence and rubric criteria.\n"
            "No identifier"
        ),
        "These responsiveness and presentation minimums are the frozen WP8 baseline.": (
            "These responsiveness and presentation minimums are the release baseline."
        ),
        "## 8. Frozen WP8 controls and downstream policy boundary": (
            "## 8. Release controls and assessment-policy boundary"
        ),
        "WP8 fixes the following interpretation:": "This release fixes the following interpretation:",
        "WP10 owns score caps, grade-boundary handling, resubmission and partial-credit": (
            "Assessment governance owns score caps, grade-boundary handling, resubmission and partial-credit"
        ),
        "The current thirteen output schemas are reorganised by purpose. The exact\nschema changes are a WP9 implementation activity governed by this frozen WP8\nburden.": (
            "The fourteen released output schemas are organised by purpose and implement\n"
            "this controlled evidence contract."
        ),
        "Where an\nexisting schema uses `scenario_id`, WP9 must replace or supplement it with:": (
            "Where a legacy schema used `scenario_id`, the released run identity instead uses:"
        ),
        "ADR-010 and ADR-012 may refine assessment-environment budgets and evaluation\nmechanics in WP9/WP10.": (
            "Assessment governance may refine assessment-environment budgets and evaluation mechanics."
        ),
        "WP10 assessment governance must": "Assessment governance must",
        "WP8 freezes": "This guide defines",
        "The frozen WP8 rubric framework": "The rubric framework",
        "a WP10 policy": "an assessment-governance policy",
        "the WP8 category meanings": "the category meanings",
        "WP8": "this release",
        "WP9": "release assembly",
        "WP10": "assessment governance",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    return _text(text.rstrip() + "\n")


def _readme(config: Mapping[str, Any]) -> str:
    package_ids = ", ".join(config["professional_release"]["dataset_package_ids"])
    return f"""# CAP-001 Professional Candidate Pack

You are acting as an independent optimisation consultant to Asterion Industrial
Controls Group. Start with `CAPSTONE_BRIEF.md`, then read
`TASK_REQUIREMENTS.md`, `APPLICATION_AND_EVIDENCE_GUIDE.md` and
`ASSESSMENT_RUBRIC.md`.

## Your principal deliverable

You must build, submit and defend a working end-to-end full-stack
decision-support application. It must give business users an interactive
interface, persistent governed data, an integrated algebraic MILP or MINLP
optimisation workflow, and interpretable results. A model plus scripts,
notebooks, APIs, static reports or interface mock-ups is not a substitute for
the working application.

You choose the architecture, framework, modelling library, solver route,
persistence technology and repository structure. That design freedom does not
make the application optional.

## What is supplied

- six complete, interchangeable 25-table planning datasets: {package_ids};
- a data dictionary and machine-readable schemas for source data, standard
  result evidence and application data-governance evidence;
- a miniature accounting fixture with published reconciliation controls;
- a non-prescriptive BASE benchmark that your own submitted model must reproduce
  at the published service and objective-quality grain; and
- guidance on cost policy, example datasets, AI-assisted work and production
  readiness.

Every dataset contains the whole P01–P12 planning reality known when the P01
plan is prepared. The named packages are examples, not a closed scenario menu.
Your product must also accept a new complete schema-valid dataset identity.

## What is deliberately not supplied

There is no starter application, solver configuration, submission manifest,
required repository tree or prescribed command vocabulary. Select and justify
your own application architecture, algebraic modelling library, MILP or MINLP
formulation, solver route, persistence design and test strategy.

Your own README must tell an independent reviewer how to install the product, run its tests,
reproduce BASE, launch and use the application, initiate or retrieve a solve,
find the submitted evidence, and understand runtime or licensing assumptions.

## Integrity

`release_manifest.json` identifies every supplied file. `CHECKSUMS.sha256`
provides a portable digest list. Source CSVs are immutable starting snapshots;
the application must import their rows into governed, history-preserving
logical masters before user changes are published as a new dataset version.
"""


def _dataset_guide() -> str:
    return """# Supplied Dataset Guide

## Interpretation

Each directory under `data/datasets` is an entire, complete 25-table planning
dataset. Replace the whole selected dataset to explore a different supplied
reality. Do not layer a package over BASE or borrow missing values from another
package. All dated conditions and recoveries in P01–P12 are known at P01.

The package identifiers are convenient examples only. They must not become a
runtime enumeration or a set of hard-coded transformations in the product.

## Why the six examples exist

| Package | Material condition | Pedagogical value |
|---|---|---|
| `BASE` | Normal commercial and operating reality | Common calibration point and required benchmark reproduction |
| `SCN-01` | Severe polymer-resin source constraint and recovery | Tests upstream dependency, advance positioning, surge and service trade-offs |
| `SCN-02` | Asia–Europe standard-lane delay, capacity loss and cost increase | Tests lead-time reasoning, mode choice, landed value and inventory timing |
| `SCN-03` | Tier-1 site outage and staged recovery | Tests alternate approved production paths and bottleneck interpretation |
| `SCN-04` | Correlated central-European constraints across tiers | Tests regional concentration, interacting capacity limits and resilience value |
| `SCN-05` | Combined source, logistics and critical-demand pressure | Tests whether explanations remain coherent when several mechanisms interact |

Complexity has value only when it changes a decision or demonstrates a
required capability. Candidates choose at least two stress examples that are
material to their analysis and explain that choice. They must also author,
publish and solve another valid data reality through the application.

Policy changes are separate. A resilience rule, approval override or objective
preference can be compared on an unchanged published dataset and must have its
own identity and authority trail.
"""


def _ai_guide() -> str:
    return """# AI-Native Working Guide

AI assistance is permitted. The candidate remains accountable for every
submitted claim, equation, data transformation, test, interface behaviour and
recommendation.

Disclose material AI-assisted contributions and retain concise evidence of how
they were checked. Strong evidence includes an example that was independently
verified, materially corrected or rejected. Do not use AI-generated prose or
code as a substitute for understanding the formulation, solver status,
recursive value calculation, data lineage or business recommendation.

You must be able to explain and defend the material AI-assisted and manually
authored parts of your work. Confidential client, employer or personal data
must not be introduced into the capstone or an unapproved external service.
"""


def _production_guide() -> str:
    return """# Production Readiness Guide

The submitted product is a professional capstone prototype, not a production
certification exercise. Explain what would be needed to operate it responsibly
for Asterion, proportionate to the design you chose.

Address material considerations across source integration and data quality,
identity and authority, secrets and security, audit and retention, concurrent
editing, scale and performance, solver capacity and licensing, observability,
failure recovery, backup and restore, release/change control, and operational
fallback when no trustworthy result is available.

Relate these considerations to failures and limitations actually observed in
your product. A credible bounded deployment path is more useful than a generic
claim that the prototype is production ready.
"""


def _fixture_payloads(config: Mapping[str, Any]) -> dict[Path, bytes]:
    root = RELEASE_ROOT / "data" / "miniature_fixture"
    payloads: dict[Path, bytes] = {}
    for name in EXPECTED_RAW_FILES:
        path = root / "inputs" / name
        if not path.is_file():
            raise FileNotFoundError(f"missing miniature-fixture input: {path}")
        payloads[path.relative_to(RELEASE_ROOT)] = path.read_bytes()
    for relative in (
        Path("fixture_control_totals.csv"),
        Path("expected_reconciliation/fixture_control_totals.csv"),
    ):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing miniature-fixture evidence: {path}")
        payloads[path.relative_to(RELEASE_ROOT)] = path.read_bytes()
    payloads[Path("data/miniature_fixture/fixture_manifest.json")] = _json(
        {
            "fixture_id": "CAP-001-MINIATURE",
            "fixture_version": config["configuration_version"],
            "period_count": 5,
            "supplier_tier_count": 3,
            "input_files": list(EXPECTED_RAW_FILES),
            "expected_reconciliation_files": ["fixture_control_totals.csv"],
        }
    )
    walkthrough = RELEASE_ROOT / "reference" / "miniature_fixture" / "ACCOUNTING_WALKTHROUGH.md"
    if not walkthrough.is_file():
        raise FileNotFoundError(f"missing miniature-fixture walkthrough: {walkthrough}")
    payloads[walkthrough.relative_to(RELEASE_ROOT)] = walkthrough.read_bytes()
    return payloads


def _dataset_payloads(config: Mapping[str, Any]) -> tuple[dict[Path, bytes], dict[str, Any]]:
    payloads: dict[Path, bytes] = {}
    summaries: dict[str, Any] = {}
    for dataset_id in config["professional_release"]["dataset_package_ids"]:
        source = DATASET_SOURCE_ROOT / dataset_id
        manifest_path = source / "dataset_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        csv_paths = sorted((source / "data").glob("*.csv"))
        if tuple(path.name for path in csv_paths) != tuple(sorted(EXPECTED_RAW_FILES)):
            raise ValueError(f"{dataset_id}: incomplete dataset file set")
        row_count = 0
        for path in csv_paths:
            with path.open(newline="", encoding="utf-8") as handle:
                row_count += sum(1 for _ in csv.reader(handle)) - 1
        for path in [*csv_paths, manifest_path]:
            relative = Path("data/datasets") / dataset_id / path.relative_to(source)
            payloads[relative] = path.read_bytes()
        summaries[dataset_id] = {
            "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
            "file_count": len(csv_paths),
            "row_count": row_count,
        }
        if manifest["dataset_id"] != dataset_id:
            raise ValueError(f"{dataset_id}: manifest identity drifted")
    return payloads, summaries


def _source_tree_payloads(source_root: Path, target_root: Path) -> dict[Path, bytes]:
    return {
        target_root / path.relative_to(source_root): path.read_bytes()
        for path in sorted(source_root.rglob("*"))
        if path.is_file()
    }


def planned_payloads(config: Mapping[str, Any]) -> dict[Path, bytes]:
    payloads: dict[Path, bytes] = {
        Path("README.md"): _text(_readme(config)),
        Path("DATASET_GUIDE.md"): _text(_dataset_guide()),
        Path("AI_NATIVE_WORKING_GUIDE.md"): _text(_ai_guide()),
        Path("PRODUCTION_READINESS_GUIDE.md"): _text(_production_guide()),
        Path("DATA_DICTIONARY.md"): (ROOT / "docs/generated/CAP-001_DATA_DICTIONARY.md").read_bytes(),
        Path("COST_POLICY.md"): (RELEASE_ROOT / "COST_POLICY.md").read_bytes(),
    }
    for target_name, source in PROJECTED_DOCUMENTS.items():
        payloads[Path(target_name)] = _candidate_projection(
            source,
            omit_section_eight=target_name == "TASK_REQUIREMENTS.md",
            omit_section_nine=target_name == "APPLICATION_AND_EVIDENCE_GUIDE.md",
        )
    payloads[Path("ASSESSMENT_RUBRIC.md")] = (
        ROOT / "docs/CAP-001_CANDIDATE_ASSESSMENT_RUBRIC.md"
    ).read_bytes()

    for schema_group in ("raw_data", "required_outputs", "application_evidence", "miniature_fixture"):
        source = ROOT / "schemas" / schema_group
        payloads.update(_source_tree_payloads(source, Path("schemas") / schema_group))

    dataset_payloads, dataset_summaries = _dataset_payloads(config)
    payloads.update(dataset_payloads)
    payloads.update(_source_tree_payloads(BENCHMARK_SOURCE_ROOT, Path("reference/base_benchmark")))
    payloads.update(_fixture_payloads(config))

    for path, content in payloads.items():
        if path.suffix.lower() in {".yaml", ".yml"}:
            raise ValueError(f"student-facing YAML is prohibited: {path}")
        if path.suffix.lower() == ".md" and re.search(rb"\bWP(?:8|9|10)\b", content):
            raise ValueError(f"internal work-package language leaked into candidate document: {path}")

    manifest_files = [
        {"path": path.as_posix(), "sha256": sha256_bytes(content), "bytes": len(content)}
        for path, content in sorted(payloads.items(), key=lambda item: item[0].as_posix())
    ]
    manifest = {
        "release_id": "CAP-001-PROFESSIONAL-RELEASE",
        "release_version": config["versions"]["capstone"],
        "configuration_version": config["configuration_version"],
        "data_contract_version": config["versions"]["data"],
        "schema_version": config["versions"]["schema"],
        "rubric_version": config["versions"]["rubric"],
        "dataset_package_ids": list(config["professional_release"]["dataset_package_ids"]),
        "files": manifest_files,
        "dataset_packages": dataset_summaries,
    }
    payloads[Path("release_manifest.json")] = _json(manifest)
    checksum_rows = [
        f"{sha256_bytes(content)}  {path.as_posix()}"
        for path, content in sorted(payloads.items(), key=lambda item: item[0].as_posix())
    ]
    payloads[Path("CHECKSUMS.sha256")] = _text("\n".join(checksum_rows) + "\n")
    return payloads


def check_payloads(payloads: Mapping[Path, bytes]) -> list[str]:
    errors: list[str] = []
    for relative, expected in payloads.items():
        target = RELEASE_ROOT / relative
        if not target.is_file():
            errors.append(f"missing release file: {relative}")
        elif target.read_bytes() != expected:
            errors.append(f"release file drifted: {relative}")
    actual = {
        path.relative_to(RELEASE_ROOT)
        for path in RELEASE_ROOT.rglob("*")
        if path.is_file()
    }
    extra = sorted(actual - set(payloads), key=lambda path: path.as_posix())
    errors.extend(f"unsupported release file: {path}" for path in extra)
    return errors


def write_payloads(payloads: Mapping[Path, bytes]) -> None:
    expected = set(payloads)
    for path in sorted(RELEASE_ROOT.rglob("*"), reverse=True):
        if path.is_file() and path.relative_to(RELEASE_ROOT) not in expected:
            path.unlink()
    for path in sorted(RELEASE_ROOT.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    for relative, content in payloads.items():
        target = RELEASE_ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed release differs")
    args = parser.parse_args(argv)
    payloads = planned_payloads(load_config())
    if args.check:
        errors = check_payloads(payloads)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(f"CAP-001 professional release is current ({len(payloads)} files).")
        return 0
    write_payloads(payloads)
    print(f"Assembled CAP-001 professional release ({len(payloads)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
