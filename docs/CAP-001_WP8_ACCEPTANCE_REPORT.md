# CAP-001 WP8 Acceptance Report

## Document control

| Field | Value |
|---|---|
| Work package | WP8 — consultant engagement and assessment design |
| Status | Accepted and frozen 1.0 |
| Date | 27 August 2026 |
| Decision owner | Capstone owner |
| Release effect | Authorises controlled WP9 population; does not itself release student material |

## 1. Current outcome

WP8 is complete. The frozen authoring set frames a realistic client engagement,
defines functional candidate outcomes, isolates the permitted technical
constraints, fixes a proportionate evidence burden and maps all normative
requirements to verification.

The capstone owner accepts WP8-O01 through WP8-O10. WP8-O11 is intentionally
handed to WP10 assessment governance: score caps, grade-boundary rules,
resubmission, partial credit and calibration must be approved there without
changing the gate meanings frozen by WP8.

## 2. Deliverable inventory

| ID | Artefact | State | Readiness finding |
|---|---|---|---|
| WP8-D01 | `docs/CAP-001_CONSULTANT_ENGAGEMENT_BRIEF.md` | Frozen 1.0 | Client-facing scope and functional outcomes accepted |
| WP8-D02 | `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md` | Frozen 1.0 | 70 functional, modelling, data, NFR and validation requirements frozen |
| WP8-D03 | `docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md` | Frozen 1.0 | Functional journeys, live/stored behaviour and rationalised output burden accepted |
| WP8-D04 | `docs/CAP-001_ASSESSMENT_RUBRIC_AND_DEFENCE_CONTRACT.md` | Frozen 1.0 | Eleven gates, 100-point rubric framework and defence prompt bank accepted |
| WP8-D05 | `docs/CAP-001_WP8_REQUIREMENT_EVIDENCE_TRACEABILITY.md` | Frozen 1.0 | Every normative requirement has business purpose and verification coverage |
| WP8-D06 | This report | Accepted 1.0 | Owner decisions, handoffs and freeze are recorded |

The authoring source is
`docs/CONSULTANT_ENGAGEMENT_AND_ASSESSMENT_DESIGN_CONTRACT.md`. The controlled
deliverable status is recorded in `docs/WP8_DELIVERABLE_REGISTER.md`.

## 3. Consistency review

| Review | Result | Evidence |
|---|---|---|
| Client-outcome language | PASS | Consultant brief contains business context, decisions, users, authority and observable outcomes without application architecture or rubric mechanics |
| Requirement boundary | PASS | Task requirements identify formulation, data treatment and NFRs as the controlled technical exceptions |
| Data semantics | PASS | Source preservation, persistent versioned masters, valid/audit time, conflict handling, atomic publication and run pinning are specified |
| Scenario openness | PASS | Supplied packages are examples; new complete dataset versions are a functional requirement |
| Supply-graph outcome | PASS | Visual upstream/downstream exploration is required while design/technology remain candidate-owned |
| Incoterm outcome | PASS | Visibility, governed CRUD, active/effective state, referential protection and solve consequence are specified |
| Model neutrality | PASS | Explicit MILP/MINLP is mandatory; Pyomo, PuLP and other suitable libraries and methods remain permitted |
| Evidence proportionality | PASS | Run evidence is separated from comparison-set evidence; `scenario_results.csv` is retired and CN-004 removes the dedicated recursive-value reconciliation file without replacement |
| Assessment neutrality | PASS | Gates and rubric do not require matching the published incumbent allocation, an exact objective or an author application |
| Traceability completeness | PASS | All 70 normative IDs appear exactly once in the task contract and all 70 are present in the WP8 traceability matrix |
| Repository alignment | PASS at WP8 boundary | CN-004/CN-005 implementation is complete; machine configuration, schema evolution and student-release population are explicitly controlled WP9 work |

WP8's CN-004 and CN-005 decisions required controlled model, generator,
validator and contract changes. The generated-artifact checks, source audit,
dataset assessments, benchmark replay and full implementation test suite are
therefore part of the acceptance evidence; prose review alone is insufficient.

## 4. Accepted owner decisions

The following decisions are accepted as the frozen WP8 position.

| ID | Decision | Accepted resolution | Reason |
|---|---|---|---|
| WP8-O01 | Supplied-example burden | Import/validate all six; reproduce the published BASE benchmark; analyse at least two justified supplied stress examples; solve one user-authored version | Tests compatibility, economic understanding and generality without requiring six expensive recursive narratives |
| WP8-O02 | Unseen dataset | Require import, validation and an application-launched recursive decision attempt, not a successful or globally optimal result | Tests generic product behaviour while respecting non-convex runtime and solver access |
| WP8-O03 | Master-data breadth | All 25 masters must be versioned and inspectable; Incoterms and the decision-material cost/capacity/demand/logistics/approval/inventory set require authored changes; generic UI CRUD for every remaining reference table is optional | Preserves the user's full data reality without turning the assessment into 25 repetitive admin screens |
| WP8-O04 | Incoterm creation | Permit creation of a schema-valid unique Incoterm abstraction, with the same effective dating, responsibility, authority and referential controls | `Create` must be meaningful if full CRUD is required; the product labels the rules as modelling abstractions, not legal advice |
| WP8-O05 | `STRESS_ONLY` | Make it an optional diagnostic, not a mandatory candidate behaviour | Each supplied condition is a complete P01-known dataset to re-optimise; stress replay is useful but not central to the engagement |
| WP8-O06 | Configuration demonstration | Require resilience, one within-stage sensitivity and the authority path for a rejected and accepted override | Directly tests the configurable product behaviours the client values |
| WP8-O07 | Stored results | Permit stored results for expensive supplied comparisons when strictly version-pinned and stale-safe; require live authoring/publication and at least one application-launched user-authored solve | Preserves interactivity and reproducibility without making web-request solver duration the test |
| WP8-O08 | Output burden | Adopt per-run core/recursive groups; retain BASE benchmark-reproduction evidence and create dataset/configuration comparisons once per comparison set; retire `scenario_results.csv` | Removes closed-scenario terminology and duplicated evidence |
| WP8-O09 | NFR targets | Retain the two-second non-solver acknowledgement/completion target and current Chromium at 1280 × 720 as frozen minimums | Concrete enough to test, proportionate for a desktop planning prototype and explicitly excludes solver runtime |
| WP8-O10 | Authority evidence | Permit a documented role simulation with trusted-boundary enforcement and audit evidence; do not require production identity federation | Tests decision rights without turning the capstone into an identity-platform exercise |
| WP8-O11 | Gate consequences | Refer score caps, resubmission and partial-credit rules to assessment governance; do not freeze them in WP8 without calibration | A technically invalid result and an absent submission need different consequences, and policy approval is required |

## 5. Controlled downstream artefact changes

WP8 acceptance does not authorise silent edits to frozen data. It authorises a
controlled WP9 change set that must include:

1. revise the decision configuration so supplied scenario IDs are examples, not
   a closed application runtime;
2. state the complete-horizon-known-at-P01 assumption in shared configuration;
3. add the Incoterm active/effective and master-record version contract;
4. add published dataset and resolved record-version identities to manifest and
   run metadata schemas;
5. replace scenario-labelled comparison contracts with dataset/configuration
   comparison contracts and retire approved redundant outputs;
6. preserve the completed CN-004 retirement of
   `recursive_cost_reconciliation.csv` without replacement; recursive
   quantities and values remain in-model calculations independently checked by
   the evaluator;
7. preserve the completed CN-005 publication of the solved BASE reference and
   retirement of the synthetic standard-cost diagnostic and comparison output;
8. populate, rather than directly hand-edit around, the controlled student-
   release brief and task requirements;
9. regenerate derived artefacts and hashes; and
10. update tests, traceability and release manifests before the WP9 clean-room
   journey.

## 6. WP8 acceptance gate result

The acceptance conditions have been met:

- the owner accepted WP8-O01 through WP8-O10;
- WP8-O11 is explicitly routed to WP10 assessment governance;
- the six WP8 documents are consistent with those decisions;
- no owner-level WP8 decision remains controlled-open;
- a clean-room reader can distinguish client outcomes, technical data/NFR
  controls, assessment evidence and candidate-owned design choices; and
- the capstone owner recorded 27 August 2026 as the approval date and version
  1.0 as the frozen WP8 document set.

WP8 is therefore complete and accepted. WP9 may populate the controlled student
release and evolve the shared schemas. WP10 may implement assessor workflow and
calibrated policy consequences. Neither work package may silently change the
WP8 contract.

## 7. Acceptance evidence

The 27 August 2026 freeze review established that:

- all eight WP8 control documents identify their frozen or accepted 1.0 state;
- the candidate contract contains 70 normative requirement rows and the
  traceability matrix contains the same 70 identifiers with no missing or extra
  ID;
- the assessment contract contains 11 deterministic quality gates and its
  rubric categories total 100 points;
- no owner-level draft, pending or controlled-open marker remains in the WP8
  document set; downstream implementation and governance items are explicitly
  labelled WP9 or WP10 handoffs;
- source-document audit reports 25 raw contracts, 240 raw fields and 13
  capstone-specific output contracts;
- the generated-contract check reports all 193 derived artefacts current;
- BASE benchmark replay, the 19-gate commercial assessment, the 24-gate
  dataset-package assessment and the 10-gate whole-dataset viability audit all
  pass; and
- the full 96-test repository suite and `git diff --check` pass.
