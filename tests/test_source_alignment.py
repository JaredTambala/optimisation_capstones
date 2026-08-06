from __future__ import annotations

import pytest


def test_configuration_matches_approved_source_documents() -> None:
    pytest.importorskip("docx", reason="install the audit extra to verify DOCX alignment")
    from tooling.audit_source_documents import audit

    summary = audit()
    assert summary == {
        "governing_documents": 2,
        "raw_contracts": 26,
        "raw_fields": 248,
        "cap_specific_outputs": 13,
        "common_outputs": 5,
        "rubric_categories": 10,
        "solution_statuses": 6,
    }

