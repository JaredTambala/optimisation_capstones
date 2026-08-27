# CAP-001 WP8 Deliverable Register

## Document control

| Field | Value |
|---|---|
| Work package | WP8 — consultant engagement and assessment design |
| Status | Frozen register 1.0 |
| Date | 27 August 2026 |
| Governing design | `docs/CONSULTANT_ENGAGEMENT_AND_ASSESSMENT_DESIGN_CONTRACT.md` Frozen 1.0 |
| Release effect | WP8 artefacts remain private authoring controls and are accepted as the basis for controlled WP9 population |

## Purpose

This register defines the smallest coherent WP8 deliverable set. It prevents
the student brief, technical controls, application evidence and assessment
mechanics from being mixed into one implementation-led document.

CN-004 (`CAP-001_DERIVED_VALUE_RECONCILIATION_CHANGE_NOTES.md`) records the
controlled follow-on required to retire the dedicated recursive-cost
reconciliation file without replacement. Recursive values remain calculations
inside the candidate's mathematical model and the evaluator's independent
working state.

CN-005 (`CAP-001_BASE_REFERENCE_BENCHMARK_CHANGE_NOTES.md`) replaces the
synthetic fixed-cost diagnostic with a solved, independently validated BASE
reference incumbent. The incumbent is calibration evidence and never a model
input or prescribed allocation.

| ID | Deliverable | Purpose | Current state | Freeze dependency |
|---|---|---|---|---|
| WP8-D01 | `docs/CAP-001_CONSULTANT_ENGAGEMENT_BRIEF.md` | State the client problem, users, decisions, functional outcomes and engagement success in business language | Frozen 1.0 | Accepted |
| WP8-D02 | `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md` | State normative functional requirements and the controlled mathematical, data and non-functional boundaries | Frozen 1.0 | Accepted |
| WP8-D03 | `docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md` | Define demonstrable application behaviours, run evidence and proportionate submission artefacts | Frozen 1.0 | Accepted |
| WP8-D04 | `docs/CAP-001_ASSESSMENT_RUBRIC_AND_DEFENCE_CONTRACT.md` | Define gates, rubric interpretations and ownership-focused defence prompts | Frozen 1.0 | Accepted; score consequences handed to WP10 |
| WP8-D05 | `docs/CAP-001_WP8_REQUIREMENT_EVIDENCE_TRACEABILITY.md` | Map every requirement to business purpose, evidence, gate, rubric or defence without duplicate burden | Frozen 1.0 | Accepted |
| WP8-D06 | `docs/CAP-001_WP8_ACCEPTANCE_REPORT.md` | Record consistency review, resolved decisions and owner freeze decision | Accepted 1.0 | Accepted |

## Authoring boundaries

- WP8-D01 is written as a client brief. It does not contain rubric points,
  required filenames, framework choices or evaluator mechanics.
- WP8-D02 contains stable normative identifiers. General application
  requirements are functional; concrete technical instructions are limited to
  the mathematical formulation, data treatment and non-functional baseline.
- WP8-D03 says what must be demonstrable and reproducible, not which pages or
  components must be built.
- WP8-D04 assesses outcomes, reasoning and evidence. It does not compare a
  candidate with a hidden allocation or preferred application architecture.
- WP8-D05 is the completeness control. An obligation without a business reason
  or verification route must be removed or corrected before release.
- WP8-D06 is the only artefact that may mark WP8 complete.

## Completed sequence

1. WP8-D01 and the functional sections of WP8-D02 were accepted.
2. Assessment burden, authority demonstration and non-functional minimums were
   resolved.
3. WP8-D03 and WP8-D04 were frozen, with assessment-policy consequences
   explicitly handed to WP10.
4. WP8-D05 confirmed complete requirement-to-evidence coverage.
5. The clean-room author review and owner acceptance were recorded in WP8-D06.
