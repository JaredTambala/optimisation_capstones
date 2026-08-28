# CAP-001 WP8 Requirement-to-Evidence Traceability

> **Historical assessment note:** Gate and defence columns record the WP8
> design at its freeze date. WP9 professional release contract 1.1 supersedes
> them for assessment. Current review uses the published rubric and the private
> AI-agent system prompt; requirement and evidence mappings remain useful.

## Document control

| Field | Value |
|---|---|
| Purpose | Prove that each WP8 candidate obligation has a business reason and proportionate verification route |
| Status | WP8 frozen 1.0 |
| Date | 27 August 2026 |
| Requirement source | `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md` Frozen 1.0 |
| Evidence source | `docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md` Frozen 1.0 |
| Assessment source | `docs/CAP-001_ASSESSMENT_RUBRIC_AND_DEFENCE_CONTRACT.md` Frozen 1.0 |

## 1. Reading the matrix

Rubric references use:

- R1 business framing and user value;
- R2 data understanding and preparation;
- R3 mathematical formulation;
- R4 method selection and implementation;
- R5 validation, benchmarking and robustness;
- R6 interactive application;
- R7 software engineering and reproducibility;
- R8 presentation and recommendation;
- R9 production readiness and limitations; and
- R10 technical defence.

Technical-defence references use the prompt areas in the defence contract.
`—` under Gate means that the outcome is qualitatively assessed or sampled in
defence rather than acting as a deterministic pre-score gate.

## 2. Functional requirements

| Requirement | Business purpose | Minimum evidence | Gate | Rubric/defence |
|---|---|---|---|---|
| CAP-F-001 | Prevent mixed or unidentified planning realities | Import/select demonstration, source hashes and published manifest | G02, G09 | R2, R6; TD-Data history |
| CAP-F-002 | Let users understand the state they are acting on | Visible state identities and history demonstration | G09, G11 | R2, R6 |
| CAP-F-003 | Make the effect of proposed data change reviewable | Draft diff, affected references and graph evidence | G09 | R2, R6; TD-Data history |
| CAP-F-004 | Prevent incomplete or invalid data becoming a solve input | Blocking validation and atomic publication demonstration | G02, G09 | R2, R6, R7 |
| CAP-F-005 | Ensure the product handles business change rather than named examples | Assessor-created complete dataset probe | G10 | R2, R6, R7 |
| CAP-F-006 | Enable material business-data exploration | Governed edits across the mandatory fact set | G09, G10 | R2, R6 |
| CAP-F-007 | Give commercial owners visibility of Incoterm meaning and use | Current/history listing and affected-contract evidence | G09 | R2, R6; TD-Cost policy |
| CAP-F-008 | Let authorised users govern Incoterms | CRUD/activation demonstration with history | G02, G09 | R2, R6; TD-Data history |
| CAP-F-009 | Connect an Incoterm change to business and model effect | Before/after contract, cost and result comparison | G07, G09, G11 | R1, R2, R6; TD-Cost policy |
| CAP-F-010 | Preserve commercial and historical integrity | Rejected erasure/invalid reference demonstration | G02, G09 | R2, R5, R7 |
| CAP-F-011 | Make multi-tier structure understandable | Running visual supply-graph demonstration | G09 | R6; TD-Graph |
| CAP-F-012 | Let users investigate dependency and exposure | Assessor-selected upstream/downstream traversal | G09 | R1, R2, R6; TD-Graph |
| CAP-F-013 | Connect facts and decisions to the network | Data/result-to-graph relationship evidence | G09, G11 | R1, R6; TD-Graph |
| CAP-F-014 | Keep policy distinct from business data | Independent version selection and identity evidence | G08, G09 | R2, R6 |
| CAP-F-015 | Support a material resilience decision | Quantitative intervention and trade-off comparison | G09, G11 | R1, R4, R6, R8 |
| CAP-F-016 | Demonstrate meaningful controlled configurability | Within-stage parameter or approved equivalent comparison | G09, G11 | R4, R6 |
| CAP-F-017 | Prevent silent approval bypass | Rejected and authorised override evidence | G05, G08, G09 | R2, R6, R7; TD-Configuration |
| CAP-F-018 | Provide the central planning outcome honestly | Run state and horizon-wide result or failure record | G03–G09 | R1, R3–R6 |
| CAP-F-019 | Protect operational feasibility | Plan outputs and independent constraint reconciliation | G05 | R3, R5 |
| CAP-F-020 | Calibrate the submitted BASE decision against known evidence | Candidate BASE run, benchmark controls and material-difference explanation | G04, G11 | R1, R3–R5, R6 |
| CAP-F-021 | Give planners an actionable weekly plan | Standard plan artefacts and application exploration | G05, G09, G11 | R1, R6, R8 |
| CAP-F-022 | Explain operational risk and limiting facts | Constraint/service evidence connected to recommendation | G05, G11 | R1, R5, R6, R8 |
| CAP-F-023 | Explain end-to-end material value | Cost lineage, roll-forward and application trace | G06, G07, G09 | R3, R5, R6; TD-Recursive value |
| CAP-F-024 | Support controlled comparison | Dataset/configuration comparison artefacts and views | G08, G11 | R1, R2, R6 |
| CAP-F-025 | Prevent invalid decisions being mistaken for valid ones | Controlled status and failure-state demonstrations | G01, G05, G06, G11 | R4–R7 |
| CAP-F-026 | Convert analysis into accountable action | Decision summary tied to exact versions and evidence | G08, G11 | R1, R8; TD-Recommendation |
| CAP-F-027 | Establish supplied-data compatibility | Six-package import/validation record | G02, G10 | R2, R7 |
| CAP-F-028 | Establish faithful BASE reproduction | Independently validated BASE run and benchmark-reproduction record | G04–G08 | R3–R5 |
| CAP-F-029 | Exercise materially different supplied realities | Candidate-justified comparison set | G05–G08, G11 | R1, R4–R6, R8 |
| CAP-F-030 | Prove user-authored data capability | Draft-to-publish-to-solve successor journey | G02, G08–G10 | R2, R6, R7; TD-Data history |
| CAP-F-031 | Prove policy configurability without data mutation | Same-dataset policy comparison | G08, G09, G11 | R1, R4, R6; TD-Configuration |

## 3. Mathematical requirements

| Requirement | Business purpose | Minimum evidence | Gate | Rubric/defence |
|---|---|---|---|---|
| CAP-M-001 | Ensure the recommendation is grounded in an inspectable optimisation formulation | Algebraic model specification and generated model evidence | G03 | R3; TD-Physical model |
| CAP-M-002 | Require a meaningful known-case calibration without prescribing an allocation | Candidate BASE run, benchmark contract and reproduction checks | G04 | R3–R5 |
| CAP-M-003 | Represent recursive end-to-end value correctly | Equations, fixture and full-run reconciliation | G03, G06, G07 | R3, R5; TD-Recursive value |
| CAP-M-004 | Protect service priority and anti-dilution | Objective stages, locks or equivalent and recomputation | G03, G05, G06 | R3–R5 |
| CAP-M-005 | Keep the formulation numerically and logically bounded | Bound derivation, model bounds and violation checks | G03, G05 | R3–R5 |
| CAP-M-006 | Prevent unsupported solver claims | Status, incumbent, bound/gap and limitation evidence | G03, G11 | R4, R8; TD-Method |
| CAP-M-007 | Permit diverse methods without concealing departures | Method report and independent departure checks | G03, G05–G07 | R4, R5; TD-Method |

## 4. Technical data requirements

| Requirement | Business purpose | Minimum evidence | Gate | Rubric/defence |
|---|---|---|---|---|
| CAP-D-001 | Retain trustworthy source provenance | Preserved files, schema identity and hashes | G02 | R2, R7 |
| CAP-D-002 | Protect operational history and restart recovery | Persistence/restart test | G01, G02 | R2, R7 |
| CAP-D-003 | Make every business fact traceable | Master-record metadata and history | G02, G08 | R2; TD-Data history |
| CAP-D-004 | Remove temporal ambiguity | Boundary/as-of tests and UTC audit evidence | G02 | R2, R5 |
| CAP-D-005 | Support correct effective and audit history | Overlap/correction tests and history demonstration | G02 | R2, R5; TD-Data history |
| CAP-D-006 | Prevent destructive CRUD | Create/read/successor/retirement demonstration | G02, G09 | R2, R6 |
| CAP-D-007 | Prevent silent lost updates | Stale/conflicting write test | G02, G09 | R5, R7 |
| CAP-D-008 | Protect the trusted data boundary | Server-side or equivalent boundary tests | G02, G09 | R5, R7, R9 |
| CAP-D-009 | Ensure a solve consumes one complete reproducible reality | Atomic publication test and manifest | G02, G08 | R2, R5, R7 |
| CAP-D-010 | Preserve withdrawn historical evidence | Withdrawal and historical selection test | G02 | R2, R7 |
| CAP-D-011 | Keep existing recommendations reproducible | Run lineage and post-change rerun comparison | G08 | R2, R5, R7 |
| CAP-D-012 | Allow controlled portability and recovery | Export into clean instance and hash comparison | G01, G08 | R7, R9 |
| CAP-D-013 | Make Incoterm availability operationally meaningful | Active-state, referential and contract-eligibility checks | G02, G07, G09 | R2, R5, R6; TD-Cost policy |
| CAP-D-014 | Preserve the student's responsibility to derive end-to-end value inside the formulation | Raw-schema/output-contract scan, formulation inspection, in-memory evaluator recomputation and derived-input-isolation test | G03, G04, G07 | R2–R5; TD-Recursive value |

## 5. Non-functional requirements

| Requirement | Business purpose | Minimum evidence | Gate | Rubric/defence |
|---|---|---|---|---|
| CAP-N-001 | Deliver an end-to-end usable decision product | Clean application run and controlled journeys | G01, G09 | R6, R7 |
| CAP-N-002 | Avoid loss or partial publication | Restart, failed-write and atomicity tests | G02 | R5, R7 |
| CAP-N-003 | Protect authority and secrets | Authority tests, secret scan and production note | G09 | R7, R9; TD-Configuration |
| CAP-N-004 | Make core journeys accessible | Accessibility tooling and keyboard evidence | — | R6, R7 |
| CAP-N-005 | Keep interaction usable during expensive work | Declared environment and response/progress measurements | — | R6, R7, R9 |
| CAP-N-006 | Prevent misleading failure and preserve recovery | Failure/retry demonstrations | G09, G11 | R6, R7 |
| CAP-N-007 | Support diagnosis and audit | Correlated data-change and solve logs/status | G08 | R7, R9 |
| CAP-N-008 | Allow independent installation and operation | Clean environment execution | G01 | R7 |
| CAP-N-009 | Support data continuity and recovery | Export/restore demonstration | G02, G08 | R7, R9 |
| CAP-N-010 | Establish a minimum usable presentation environment | Declared browser/viewport demonstration | — | R6, R7 |

## 6. Validation requirements

| Requirement | Business purpose | Minimum evidence | Gate | Rubric/defence |
|---|---|---|---|---|
| CAP-V-001 | Prevent malformed business data entering a decision | Data validation report and negative cases | G02 | R2, R5 |
| CAP-V-002 | Establish understanding of controlled accounting semantics | Miniature fixture results and residuals | G03, G06, G07 | R3, R5; TD-Recursive value |
| CAP-V-003 | Establish operational validity | Independent physical checks | G05 | R3, R5; TD-Physical model |
| CAP-V-004 | Establish recursive pool validity | Independent quantity/value/unit-cost checks | G06 | R3, R5; TD-Recursive value |
| CAP-V-005 | Establish commercial-accounting validity | Ledger, markup and leakage checks | G07 | R3, R5; TD-Cost policy |
| CAP-V-006 | Make claims reproducible | Version/hash completeness and rerun evidence | G08 | R2, R5, R7 |
| CAP-V-007 | Prevent contradictory business evidence | Cross-channel recomputation | G11 | R5, R6, R8 |
| CAP-V-008 | Demonstrate that material controls fail safely | Adversarial test and visible product state | G05–G07 or G09 | R5–R7; TD-Failure |

## 7. Coverage findings

The frozen mapping contains no orphan WP8 requirement: every requirement maps
to at least one evidence route and rubric criterion, quality gate or defence
area. The burden and control positions are fixed as follows:

1. `CAP-F-029` requires at least two candidate-justified supplied stress solves;
2. `CAP-F-030` requires one application-launched user-authored solve, while the
   assessor-created dataset requires an application-launched recursive attempt
   with honest outcome classification;
3. `CAP-N-003` permits controlled role simulation with trusted-boundary
   enforcement and audit evidence;
4. `CAP-N-005` and `CAP-N-010` use the two-second non-solver and current
   Chromium at 1280 x 720 minimums;
5. dataset/configuration comparison evidence replaces the closed scenario
   comparison and `scenario_results.csv` is retired; and
6. WP10 owns the calibrated consequence of `FAIL` and `NOT_EVIDENCED` without
   changing the gate meanings.

## 8. Downstream implementation alignment

CN-004 and CN-005 have already removed derived-cost inputs and dedicated
recursive-cost comparison outputs and have published the solved BASE reference
benchmark. WP9 must reconcile the remaining older repository controls with
this frozen matrix:

- `CAP-001_REQUIREMENTS_TRACEABILITY_MATRIX.md` still specifies a closed six-
  scenario runtime, all-six evaluation burden, named application views and the
  former WP6 gate count;
- `config/cap001_decision_config.json` and output schemas still enumerate the
  six scenario IDs and use scenario-labelled run/comparison fields;
- the Incoterm raw schema does not yet expose the required active state or
  record-version semantics;
- dataset/run manifests do not yet pin effective master-record versions; and
- the student-release brief and task requirements remain WP1 placeholders.

WP8 defines the accepted requirement and evidence meaning. Configuration,
schema and student-release changes are controlled WP9 implementation work.
WP10 owns calibrated gate consequences and assessor workflow. Neither handoff
may silently change the frozen WP8 obligation set.
