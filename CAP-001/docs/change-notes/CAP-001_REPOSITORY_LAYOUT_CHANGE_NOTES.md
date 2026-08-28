# CAP-001 Repository Layout Change Notes

## Document control

| Field | Value |
|---|---|
| Change note | CN-006 — Isolate CAP-001 beneath one top-level project directory |
| Status | Approved and implemented |
| Date | 28 August 2026 |
| Configuration version | `0.3.6` |
| Semantic effect | None on business data, formulation, benchmark, rubric or candidate obligations |

## 1. Decision

All CAP-001-specific source material, authoring controls, code, tests,
configuration, schemas, generated evidence and candidate-release material live
beneath the repository's top-level `CAP-001/` directory.

The portfolio-wide control standard is shared material and lives under the
repository-level `standards/` directory. The repository root otherwise contains
only portfolio navigation and shared repository controls.

## 2. Project boundary

The CAP-001 project root contains:

- `source/` for the CAP-001 specification;
- `docs/` and `adrs/` for decisions and acceptance evidence;
- `config/` and `schemas/` for machine-readable contracts;
- `generator/`, `generated/`, `miniature_fixture/` and `reference/` for data and
  validation evidence;
- `cap001_model/`, `tooling/` and `tests/` for private implementation controls;
- `evaluation/` for the private AI-agent review prompt; and
- `student_release/` for the professional candidate pack.

Commands and generated paths are project-relative and are run from `CAP-001/`.

## 3. Controlled consequences

- Configuration `0.3.6` records project-relative private-control paths.
- The contract artefact manifest moves to
  `generated/contracts/CAP-001_ARTIFACT_MANIFEST.json` so contract generation does
  not claim ownership of dataset and viability evidence under `generated/`.
- The generated private-control README is retired; `CAP-001/README.md` is an
  authored project entry point.
- Source-document validation resolves the CAP-001 specification from `source/`
  and the shared standard from `../standards/`.
- A repository-layout regression test prevents the former root-level CAP-001
  directories and files from returning.

No dataset row, mathematical requirement, candidate-facing assessment rule or
BASE benchmark control is changed by this reorganisation.
