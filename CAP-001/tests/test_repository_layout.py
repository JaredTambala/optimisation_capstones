from __future__ import annotations

from tooling.contract_runtime import ROOT


def test_cap001_is_isolated_beneath_one_top_level_directory() -> None:
    repository_root = ROOT.parent

    assert ROOT.name == "CAP-001"
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / "source").is_dir()
    assert (ROOT / "student_release/CAP-001-tier-n-release").is_dir()
    assert (
        repository_root
        / "standards/Optimisation_Search_and_Decision_Intelligence_Capstone_Control_Standard_v0.2.docx"
    ).is_file()

    legacy_root_entries = {
        "adrs",
        "cap001_model",
        "capstones",
        "config",
        "docs",
        "generated",
        "pyproject.toml",
        "schemas",
        "student_release",
        "templates",
        "tests",
        "tooling",
    }
    assert not any((repository_root / name).exists() for name in legacy_root_entries)
    assert not any(
        path.name.startswith("CAP-001_")
        for path in repository_root.iterdir()
    )
