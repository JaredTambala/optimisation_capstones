# CAP-001 WP9 Acceptance Report

## Document control

| Field | Value |
|---|---|
| Work package | WP9 — professional candidate release |
| Status | Accepted 1.1 |
| Date | 27 August 2026 |
| Decision owner | Capstone owner |
| Governing contract | `docs/CAP-001_WP9_PROFESSIONAL_RELEASE_CONTRACT.md` 1.1 |
| Candidate release | `student_release/CAP-001-tier-n-release/` |

## 1. Decision

WP9 is accepted. The candidate release is a professional engagement pack, not
a starter repository or a programmatic-grading scaffold. It supplies the
business problem, functional outcomes, bounded technical requirements, six
complete example datasets, schemas, accounting fixture, BASE benchmark and
assessment expectations without prescribing a project tree, application
framework, algebraic modelling library, solver, configuration syntax or
command vocabulary. Candidate-facing assessment material is limited to a
concise 100-point rubric; detailed evaluator mechanics, gate vocabulary and
defence prompt design are not part of the engagement pack.

The release states prominently that the principal candidate deliverable is a
working end-to-end full-stack decision-support application. Candidate freedom
over architecture and technology does not permit a model-only, notebook-only,
API-only, report-only or interface-mock-up submission.

This decision closes release assembly only. It does not issue the final pack,
build a model solution or define later score-cap, resubmission or calibration
policy.

Submission review is governed privately by a versioned AI-agent system prompt.
It requires evidence citations and professional judgement, prohibits a hidden
model answer and does not operate as a deterministic submission evaluator.

## 2. Accepted release profile

| Control | Accepted result |
|---|---:|
| Release files | 245 |
| Manifested payload files | 243 |
| Complete dataset packages | 6 |
| CSV files across supplied datasets | 150 |
| Rows across supplied datasets | 33,439 |
| Raw-data schemas | 25 |
| Required-result schemas | 14 |
| Application-governance evidence schemas | 3 |
| Miniature-fixture schemas | 2 |
| Regression tests | 98 |

The six package manifests identify BASE and SCN-01 through SCN-05 as complete
datasets whose P01–P12 facts are known at P01. Their identifiers are source
provenance, not a closed application runtime. Each package contains all 25 CSV
snapshots and validates independently without fallback to another package.

## 3. Contract changes accepted

- Configuration `0.3.5`, data contract `0.3.3` and schema `0.4.0` implement
  immutable source-snapshot and history-preserving logical-master semantics.
- Incoterm codes are open to another schema-valid identifier. The starting
  snapshot includes `active_flag`; every supplied rule is active.
- An active contract referencing an inactive or absent Incoterm fails before
  model construction. The private fixture and benchmark route exercise the
  same rule.
- Run evidence pins the published dataset version, dataset content, resolved
  master-record versions, policy configuration and method configuration.
- `dataset_comparison.csv` and `configuration_comparison.csv` distinguish a
  data change from a policy change.
- `base_benchmark_reproduction.json` records non-prescriptive BASE
  reproduction evidence.
- Rubric version `1.1.0` replaces candidate-facing quality-gate and defence
  mechanics with ten concise categories totalling 100 points.
- `scenario_results.csv`, the closed `scenario_comparison.csv`, the synthetic
  standard-cost input and the dedicated recursive-cost reconciliation file are
  retired.

## 4. Candidate-neutrality decision

The following obsolete material was removed:

- supplied solver or default-case YAML;
- candidate submission YAML and manifest schema;
- placeholder shell commands;
- prescribed source, test, report and application directories;
- report and README templates;
- the detailed assessment, quality-gate and defence-mechanics guide;
- header-only raw-data placeholders; and
- empty result-contract examples.

The release instead tells the candidate which observable outcomes and evidence
must exist. The candidate owns their architecture and documents installation,
tests, BASE reproduction, application use, solve initiation or retrieval,
evidence locations, chosen stack and operating assumptions in their own
README.

## 5. Acceptance evidence

| Gate | Evidence | Result |
|---|---|:---:|
| Author-owned contract generation | `python -m tooling.build_contract_artifacts --check` | PASS |
| Six dataset generators and depth evidence | network, commercial, planning and package `--check` routes | PASS |
| Whole-dataset decision depth | retained viability audit | PASS — 10/10 gates |
| BASE physical and recursive evidence | `python -m tooling.build_base_reference_benchmark --check` | PASS |
| Miniature accounting fixture | `python -m tooling.build_fixture_reconciliation --check` | PASS |
| Candidate release drift | `python -m tooling.build_student_release --check` | PASS |
| Isolated release integrity | `python -m tooling.validate_student_release` | PASS |
| Source-document alignment | DOCX audit plus controlled release amendments | PASS |
| Repository regression | `pytest -q` | PASS — 98 tests |
| Patch hygiene | `git diff --check` | PASS |

The clean-room validator copies the release to an isolated directory and
revalidates its allow-list, file and checksum manifests, six raw-data package
sets, schemas, fixture and BASE benchmark pin. It also rejects symlinks,
student-facing YAML, internal work-package prose, starter material and retired
recursive-cost or standard-cost artefacts. These are release-authoring controls,
not a deterministic evaluation of a candidate submission.

## 6. Retained author-side controls

`tooling/build_student_release.py` is the single release assembler.
`tooling/validate_student_release.py` is the independent author-side clean-room
gate. Private generators, the reference model, viability evidence and hidden
calibration material are not copied into the candidate release. The public
BASE benchmark is an explicit, independently replayed allow-list item.

`capstones/CAP-001/evaluation/AI_SUBMISSION_REVIEW_SYSTEM_PROMPT.md` is the
private assessor-side review guide. It scores only the published rubric,
requires cited evidence, treats missing and contradictory evidence explicitly,
and routes uncertain judgement through explanation rather than hidden gates.

The release manifest and portable checksum list are generated controls. Any
subsequent change to candidate-visible content must rebuild them and repeat the
acceptance routes above.
