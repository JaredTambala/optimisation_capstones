# CAP-001 Requirement-to-Evidence Traceability

## Document control

| Field | Value |
|---|---|
| Purpose | Show that each candidate obligation has a business reason, proportionate evidence route and rubric coverage |
| Status | Current author-side traceability control 1.1 |
| Date | 28 August 2026 |
| Requirement source | `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md` |
| Evidence source | `docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md` |
| Assessment source | `docs/CAP-001_CANDIDATE_ASSESSMENT_RUBRIC.md` |

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

The matrix is an author-side completeness control, not a deterministic grading
workflow. The private AI review prompt directs the assessor to interpret this
evidence contextually against the published rubric.

## 2. Functional requirements

| Requirement | Business purpose | Minimum evidence | Rubric coverage |
|---|---|---|---|
| CAP-F-001 | Prevent mixed or unidentified planning realities | Import/select demonstration, source hashes and published manifest | R2, R6 |
| CAP-F-002 | Let users understand the state they are acting on | Visible state identities and history demonstration | R2, R6 |
| CAP-F-003 | Make the effect of proposed data change reviewable | Draft diff, affected references and graph evidence | R2, R6 |
| CAP-F-004 | Prevent incomplete or invalid data becoming a solve input | Blocking validation and atomic publication demonstration | R2, R6, R7 |
| CAP-F-005 | Ensure the product handles business change rather than named examples | Assessor-created complete dataset probe | R2, R6, R7 |
| CAP-F-006 | Enable material business-data exploration | Governed edits across the mandatory fact set | R2, R6 |
| CAP-F-007 | Give commercial owners visibility of Incoterm meaning and use | Current/history listing and affected-contract evidence | R2, R6 |
| CAP-F-008 | Let authorised users govern Incoterms | CRUD/activation demonstration with history | R2, R6 |
| CAP-F-009 | Connect an Incoterm change to business and model effect | Before/after contract, cost and result comparison | R1, R2, R6 |
| CAP-F-010 | Preserve commercial and historical integrity | Rejected erasure/invalid reference demonstration | R2, R5, R7 |
| CAP-F-011 | Make multi-tier structure understandable | Running visual supply-graph demonstration | R6 |
| CAP-F-012 | Let users investigate dependency and exposure | Assessor-selected upstream/downstream traversal | R1, R2, R6 |
| CAP-F-013 | Connect facts and decisions to the network | Data/result-to-graph relationship evidence | R1, R6 |
| CAP-F-014 | Keep policy distinct from business data | Independent version selection and identity evidence | R2, R6 |
| CAP-F-015 | Support a material resilience decision | Quantitative intervention and trade-off comparison | R1, R4, R6, R8 |
| CAP-F-016 | Demonstrate meaningful controlled configurability | Within-stage parameter or approved equivalent comparison | R4, R6 |
| CAP-F-017 | Prevent silent approval bypass | Rejected and authorised override evidence | R2, R6, R7 |
| CAP-F-018 | Provide the central planning outcome honestly | Run state and horizon-wide result or failure record | R1, R3–R6 |
| CAP-F-019 | Protect operational feasibility | Plan outputs and independent constraint reconciliation | R3, R5 |
| CAP-F-020 | Calibrate the submitted BASE decision against known evidence | Candidate BASE run, benchmark controls and material-difference explanation | R1, R3–R5, R6 |
| CAP-F-021 | Give planners an actionable weekly plan | Standard plan artefacts and application exploration | R1, R6, R8 |
| CAP-F-022 | Explain operational risk and limiting facts | Constraint/service evidence connected to recommendation | R1, R5, R6, R8 |
| CAP-F-023 | Explain end-to-end material value | Cost lineage, roll-forward and application trace | R3, R5, R6 |
| CAP-F-024 | Support controlled comparison | Dataset/configuration comparison artefacts and views | R1, R2, R6 |
| CAP-F-025 | Prevent invalid decisions being mistaken for valid ones | Controlled status and failure-state demonstrations | R4–R7 |
| CAP-F-026 | Convert analysis into accountable action | Decision summary tied to exact versions and evidence | R1, R8 |
| CAP-F-027 | Establish supplied-data compatibility | Six-package import/validation record | R2, R7 |
| CAP-F-028 | Establish faithful BASE reproduction | Independently validated BASE run and benchmark-reproduction record | R3–R5 |
| CAP-F-029 | Exercise materially different supplied realities | Candidate-justified comparison set | R1, R4–R6, R8 |
| CAP-F-030 | Prove user-authored data capability | Draft-to-publish-to-solve successor journey | R2, R6, R7 |
| CAP-F-031 | Prove policy configurability without data mutation | Same-dataset policy comparison | R1, R4, R6 |

## 3. Mathematical requirements

| Requirement | Business purpose | Minimum evidence | Rubric coverage |
|---|---|---|---|
| CAP-M-001 | Ensure the recommendation is grounded in an inspectable optimisation formulation | Algebraic model specification and generated model evidence | R3 |
| CAP-M-002 | Require a meaningful known-case calibration without prescribing an allocation | Candidate BASE run, benchmark contract and reproduction checks | R3–R5 |
| CAP-M-003 | Represent recursive end-to-end value correctly | Equations, fixture and full-run reconciliation | R3, R5 |
| CAP-M-004 | Protect service priority and anti-dilution | Objective stages, locks or equivalent and recomputation | R3–R5 |
| CAP-M-005 | Keep the formulation numerically and logically bounded | Bound derivation, model bounds and violation checks | R3–R5 |
| CAP-M-006 | Prevent unsupported solver claims | Status, incumbent, bound/gap and limitation evidence | R4, R8 |
| CAP-M-007 | Permit diverse methods without concealing departures | Method report and independent departure checks | R4, R5 |

## 4. Technical data requirements

| Requirement | Business purpose | Minimum evidence | Rubric coverage |
|---|---|---|---|
| CAP-D-001 | Retain trustworthy source provenance | Preserved files, schema identity and hashes | R2, R7 |
| CAP-D-002 | Protect operational history and restart recovery | Persistence/restart test | R2, R7 |
| CAP-D-003 | Make every business fact traceable | Master-record metadata and history | R2 |
| CAP-D-004 | Remove temporal ambiguity | Boundary/as-of tests and UTC audit evidence | R2, R5 |
| CAP-D-005 | Support correct effective and audit history | Overlap/correction tests and history demonstration | R2, R5 |
| CAP-D-006 | Prevent destructive CRUD | Create/read/successor/retirement demonstration | R2, R6 |
| CAP-D-007 | Prevent silent lost updates | Stale/conflicting write test | R5, R7 |
| CAP-D-008 | Protect the trusted data boundary | Server-side or equivalent boundary tests | R5, R7, R9 |
| CAP-D-009 | Ensure a solve consumes one complete reproducible reality | Atomic publication test and manifest | R2, R5, R7 |
| CAP-D-010 | Preserve withdrawn historical evidence | Withdrawal and historical selection test | R2, R7 |
| CAP-D-011 | Keep existing recommendations reproducible | Run lineage and post-change rerun comparison | R2, R5, R7 |
| CAP-D-012 | Allow controlled portability and recovery | Export into clean instance and hash comparison | R7, R9 |
| CAP-D-013 | Make Incoterm availability operationally meaningful | Active-state, referential and contract-eligibility checks | R2, R5, R6 |
| CAP-D-014 | Preserve the student's responsibility to derive end-to-end value inside the formulation | Raw-schema/output-contract scan, formulation inspection, in-memory evaluator recomputation and derived-input-isolation test | R2–R5 |

## 5. Non-functional requirements

| Requirement | Business purpose | Minimum evidence | Rubric coverage |
|---|---|---|---|
| CAP-N-001 | Deliver an end-to-end usable decision product | Clean application run and controlled journeys | R6, R7 |
| CAP-N-002 | Avoid loss or partial publication | Restart, failed-write and atomicity tests | R5, R7 |
| CAP-N-003 | Protect authority and secrets | Authority tests, secret scan and production note | R7, R9 |
| CAP-N-004 | Make core journeys accessible | Accessibility tooling and keyboard evidence | R6, R7 |
| CAP-N-005 | Keep interaction usable during expensive work | Declared environment and response/progress measurements | R6, R7, R9 |
| CAP-N-006 | Prevent misleading failure and preserve recovery | Failure/retry demonstrations | R6, R7 |
| CAP-N-007 | Support diagnosis and audit | Correlated data-change and solve logs/status | R7, R9 |
| CAP-N-008 | Allow independent installation and operation | Clean environment execution | R7 |
| CAP-N-009 | Support data continuity and recovery | Export/restore demonstration | R7, R9 |
| CAP-N-010 | Establish a minimum usable presentation environment | Declared browser/viewport demonstration | R6, R7 |

## 6. Validation requirements

| Requirement | Business purpose | Minimum evidence | Rubric coverage |
|---|---|---|---|
| CAP-V-001 | Prevent malformed business data entering a decision | Data validation report and negative cases | R2, R5 |
| CAP-V-002 | Establish understanding of controlled accounting semantics | Miniature fixture results and residuals | R3, R5 |
| CAP-V-003 | Establish operational validity | Independent physical checks | R3, R5 |
| CAP-V-004 | Establish recursive pool validity | Independent quantity/value/unit-cost checks | R3, R5 |
| CAP-V-005 | Establish commercial-accounting validity | Ledger, markup and leakage checks | R3, R5 |
| CAP-V-006 | Make claims reproducible | Version/hash completeness and rerun evidence | R2, R5, R7 |
| CAP-V-007 | Prevent contradictory business evidence | Cross-channel recomputation | R5, R6, R8 |
| CAP-V-008 | Demonstrate that material controls fail safely | Adversarial test and visible product state | R5–R7 |

## 7. Coverage findings

The mapping contains no orphan requirement: every requirement maps to at least
one evidence route and rubric category. The burden and control positions are:

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
6. assessment governance owns the calibrated treatment of incomplete,
   contradictory or unsupported evidence without changing the requirement
   meanings.

## 8. Current implementation alignment

The current configuration, schemas and candidate release implement the mapped
requirements:

- complete datasets and run outputs use open dataset-version identity rather
  than a closed scenario enumeration;
- Incoterms expose active state while the application requirements add
  effective master-record history and governed CRUD;
- published dataset and run evidence pins source snapshots, resolved records,
  policy configuration and method configuration;
- derived recursive values remain formulation results and are independently
  reconciled rather than supplied as input data; and
- the BASE benchmark supports reproduction without prescribing an allocation.

Any change to a candidate requirement must update this matrix, its evidence
contract, the release projection and the assessment rubric together.
