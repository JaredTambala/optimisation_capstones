"""Materialize private solver proof cases from small, reviewable mutations."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any, Mapping


def load_proof_case(manifest_path: Path) -> Mapping[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _apply_mutation(data_dir: Path, mutation: Mapping[str, Any]) -> None:
    path = data_dir / mutation["file"]
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    matches = [
        row
        for row in rows
        if all(row[key] == value for key, value in mutation["match"].items())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"mutation for {path.name} expected one row, found {len(matches)}: "
            f"{mutation['match']}"
        )
    matches[0][mutation["column"]] = mutation["new_value"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def materialize_proof_case(manifest_path: Path, target_dir: Path) -> Mapping[str, Any]:
    """Copy canonical inputs and apply only the mutations declared by a case."""

    manifest_path = manifest_path.resolve()
    manifest = load_proof_case(manifest_path)
    source = (manifest_path.parent / manifest["input_source"]).resolve()
    if target_dir.exists():
        raise FileExistsError(target_dir)
    shutil.copytree(source, target_dir)
    mutations = list(manifest.get("mutations", []))
    source_variant = manifest.get("source_variant")
    if source_variant:
        variant_path = (manifest_path.parent / source_variant).resolve()
        variant = json.loads(variant_path.read_text(encoding="utf-8"))
        mutations.append(variant["mutation"])
    for mutation in mutations:
        _apply_mutation(target_dir, mutation)
    return manifest
