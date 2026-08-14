from __future__ import annotations

import os
import shutil
from pathlib import Path

from tooling.build_contract_artifacts import RELEASE_ROOT
from tooling.contract_runtime import ROOT, load_config, resolve_data_dir, sha256_path, validate_raw_data_directory


def test_raw_data_validates_without_writing_when_mounted_read_only(tmp_path: Path, monkeypatch) -> None:
    source = ROOT / RELEASE_ROOT / "data/raw"
    target = tmp_path / "authoritative_raw"
    shutil.copytree(source, target)
    before = {path.name: sha256_path(path) for path in target.iterdir()}

    for path in target.iterdir():
        path.chmod(0o444)
    target.chmod(0o555)
    monkeypatch.setenv("CAPSTONE_DATA_DIR", str(target))
    try:
        resolved = resolve_data_dir()
        counts = validate_raw_data_directory(resolved, load_config())
        assert len(counts) == 26
        assert sum(counts.values()) == 0
        after = {path.name: sha256_path(path) for path in target.iterdir()}
        assert before == after
    finally:
        target.chmod(0o755)
        for path in target.iterdir():
            path.chmod(0o644)
