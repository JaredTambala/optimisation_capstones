from __future__ import annotations

from tooling.contract_runtime import ROOT
from tooling.validate_student_release import validate_clean_room


def test_professional_release_passes_isolated_validation() -> None:
    summary = validate_clean_room()
    assert summary["files"] == 245
    assert summary["dataset_packages"] == 6
    assert summary["dataset_csv_files"] == 150
    assert summary["dataset_rows"] > 30_000
    assert summary["required_outputs"] == 14
    assert summary["application_evidence_contracts"] == 3


def test_ai_review_prompt_is_private_and_non_deterministic() -> None:
    prompt = (
        ROOT / "capstones/CAP-001/evaluation/AI_SUBMISSION_REVIEW_SYSTEM_PROMPT.md"
    ).read_text(encoding="utf-8")
    release = ROOT / "student_release/CAP-001-tier-n-release"

    assert "You are not a deterministic\ngrading harness" in prompt
    assert "you do not compare the submission with a hidden model\nsolution" in prompt
    assert "evidence-grounded professional judgement" in prompt
    assert not (release / "ASSESSMENT_AND_DEFENCE_GUIDE.md").exists()
    assert (release / "ASSESSMENT_RUBRIC.md").is_file()
    assert not list(release.rglob("*AI_SUBMISSION_REVIEW_SYSTEM_PROMPT*"))
