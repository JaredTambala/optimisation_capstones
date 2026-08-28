# CAP-001 Requirements Traceability Matrix

## Document control

| Field | Value |
|---|---|
| Matrix version | 0.4 working draft — WP8 accepted |
| Date | 27 August 2026 |
| Scope | CAP-001 Tier-N End-to-End Cost and Resilience Optimisation |
| Primary specification | *CAP-001 Tier-N End-to-End Cost Model, Modelling Decisions and Dataset Generation Specification* v0.3 |
| Primary specification SHA-256 | `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` |
| Inherited standard | *Optimisation, Search and Decision Intelligence Capstone Control Standard* v0.2 |
| Inherited standard SHA-256 | `2741ebd6b1e01e4102c39c9f43de3a9f05b081aa61a3efd2838a431024a45637` |
| Delivery plan | *CAP-001 Delivery and Assessment Implementation Plan* v0.3 |
| Precedence | CAP-001 v0.3, then approved ADRs/shared configuration for implementation detail, then common standard v0.2 for shared controls |

## How to use this matrix

This matrix primarily records planning coverage. Implementation state is
reported separately below so that a `Covered` row is not mistaken for proof
that its later-stage artefact already exists.

- **Covered** — the plan assigns an artefact and verification route.
- **Controlled-open** — the specification intentionally requires an ADR, calibration result or numerical decision before release.
- **Policy-open** — assessment governance must approve the consequence before release.
- **Handoff** — WP8 has frozen the governing principle and a downstream work
  package must implement or calibrate it without changing that principle.
- **Superseded** — a prior two-tier requirement is no longer applicable and must not be carried into the release.

As each work package completes, the implementation team should add an evidence path, test identifier, result and approval date.

WP1 was completed and accepted on 31 July 2026. Its implementation evidence is
recorded in `docs/WP1_ACCEPTANCE_REPORT.md`.

The network-structure implementation and technical checks were completed on
18 August 2026. Its candidate data, scorecard and witnesses are recorded under
`capstones/CAP-001/generated/network/`, with the review state in
`docs/NETWORK_STRUCTURE_IMPLEMENTATION_STATUS.md`. The capstone owner accepted
the candidate and froze its depth thresholds on 18 August 2026. The planning
statuses below continue to describe end-to-end coverage; they are not
substitutes for this implementation evidence.

The planning and complete-dataset-package set was recalibrated and accepted on
25 August 2026. All 24 technical depth gates pass across six self-contained
packages and 150 raw CSV instances. Evidence is recorded under
`capstones/CAP-001/generated/datasets/evidence/` and summarised in
`docs/PLANNING_AND_DATASET_PACKAGE_IMPLEMENTATION_REPORT.md`. The owner froze
the planning seed, depth thresholds and six package hashes on 25 August 2026.

WP7 was accepted on 25 August 2026 after all ten whole-dataset viability gates
passed. WP8 was accepted on 27 August 2026. Its frozen functional, technical-
data, non-functional and evidence requirements are traced in
`docs/CAP-001_WP8_REQUIREMENT_EVIDENCE_TRACEABILITY.md`. WP9 must reconcile the
WP1-era configuration, schemas and student release with that accepted position.
WP9 release contract 1.1 subsequently replaced the proposed deterministic
submission evaluator with rubric-guided AI review using professional judgement.

## 1. Common control requirements

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| COM-001 | Same fixed context, data, default case, scenarios, baseline, controls and rubric for all students | Decision configuration, brief and manifest | WP1/WP9 | Cross-artefact comparison | Covered |
| COM-002 | AI use is expected; consultant remains accountable | Brief, `AI_USAGE_TEMPLATE.md`, defence | WP9/WP10 | Evidence and defence review | Covered |
| COM-003 | Interactive decision-support application is mandatory | App contract and rubric-guided review | WP9 | Application inspection and functional evidence | Covered |
| COM-004 | App supports input review, meaningful controls, results, baseline, trade-offs, recommendation, export and failure states | App evidence contract | WP8/WP9 | Controlled functional journeys | Covered |
| COM-005 | Private generator, seeds, hidden ranges, adversarial material and AI review prompt remain private; the approved public BASE benchmark is explicitly allow-listed | Repository separation and allow-list builder | WP9 | Leak negative test and public-benchmark allow-list test | Covered |
| COM-006 | Release manifest records release versions, hashes, row counts and supplied packages | `release_manifest.json` | WP9 | Schema and checksum tests | Covered |
| COM-007 | Narrative, schemas, dictionary, generator, references and assessor guide share one approved configuration | Decision configuration and drift tests | WP1/WP9 | Generated/verified artefact comparison | Covered |
| COM-008 | The candidate documents installation, tests, BASE reproduction, application launch/use and solve operation in their own README | Candidate requirement and contextual review | WP9 | Evidence-grounded inspection | Covered |
| COM-009 | Authoritative data can be mounted read-only | Configured data-directory interface | WP1/WP10 | Read-only mount test | Covered |
| COM-010 | Required run metadata, metrics, constraints, reconciliation, baseline and app evidence are machine-readable | Output schemas and evidence contract | WP1/WP8 | Schema and proportionate inspection | Covered |
| COM-011 | Solver status and optimality language are controlled | Status vocabulary and AI review attention point | WP1/WP9 | Log/metadata/report comparison | Covered |
| COM-012 | Solver access cannot create an undeclared grading advantage | Solver-access and method-neutral assessment policy | WP8/WP9/WP10 | Candidate-journey and policy review | Handoff |
| COM-013 | 20–30 minute technical defence is required | Defence guide and record | WP10 | Structured defence | Covered |
| COM-014 | 10–12 slide client presentation is required | Presentation guide | WP9/WP10 | Artefact review | Covered |
| COM-015 | Submission evaluation is rubric-guided professional judgement, not deterministic grading | Private AI-agent system prompt | WP9 | Prompt review | Covered |
| COM-016 | AI scoring cites evidence and explains confidence and material judgement | Private AI-agent system prompt | WP9 | Prompt review and calibration | Covered |
| COM-017 | Human moderation handles contradictions, inaccessible evidence and material uncertainty | Reviewer workflow | WP9 | Moderation review | Covered |
| COM-018 | The candidate release is reproducible and submission review is auditable | Clean-room release build and cited assessment record | WP9 | Release rerun and evidence review | Covered |
| COM-019 | Common data conventions use stable keys, ISO dates, explicit UOM/currency, true nulls and fictional entities | Shared schema rules | WP1 | Structural validation | Covered |
| COM-020 | Production response covers architecture, integration, security, audit, scale, monitoring and fallback | Report template and rubric | WP9/WP10 | Topic-specific evidence review | Covered |

## 2. Scope, network and timing

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| SCP-001 | Asterion, four plants, EUR and fixed terminal demand define the use case | Decision configuration and brief | WP1/WP9 | Exact-value test | Covered |
| SCP-002 | Horizon is 12 weeks from 4 January to 28 March 2027 | Calendar data and config | WP1/WP6 | Period/date sequence test | Covered |
| SCP-003 | Generic Tier-N DAG instantiated as four supplier tiers plus plants | Graph generator and validator | WP4 | Tier, connectivity and acyclicity tests | Covered |
| SCP-004 | Tier number measures proximity to Asterion | Dictionary and tier validator | WP1/WP4 | Parent/path tests | Covered |
| SCP-005 | Multi-sourcing and multiple source inputs are supported at each relevant stage | Generic approvals/contracts/recipes | WP4/WP5 | Path and recipe fixtures | Covered |
| SCP-006 | External boundary prices are allowed; Tier 1–Tier 3 values are recursive | Pricing policy, calibration checks and evaluator | WP5/WP7/WP10 | Boundary/leakage tests | Covered |
| SCP-007 | Same-period conversion; receipts/production usable in period | Timing ADR, fixture and task requirements | ADR-002/WP2/WP8 | Boundary fixture | Controlled-open |
| SCP-008 | No WIP and no post-P12 arrival | Planning generator and evaluator | WP6/WP10 | Negative tests | Covered |
| SCP-009 | Opening inventory includes quantity and book value | Input schema, fixture and output contract | WP1/WP2/WP8 | Roll-forward fixture | Covered |
| SCP-010 | Release exclusions are not introduced through hidden fields | Configuration/schema allow-list | WP1/WP9 | Schema and release scan | Covered |

## 3. BASE reference, recursive model and cost policy

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| MOD-001 | Faithful reproduction of the published BASE reference controls is mandatory | Consultant task, benchmark contract and formulation requirement | WP8/WP9/WP10 | Independent candidate-result validation and benchmark comparison | Covered |
| MOD-002 | Synthetic standard-cost diagnostic requirement retired by CN-005 | CN-005 and contract scan | WP8/WP9 | Absence and reference/input-isolation tests | Retired |
| MOD-003 | Assessed semantics are a bounded non-convex recursive-cost MINLP | Method-neutral formulation contract | WP3/WP8/WP9 | Formulation review and bounds evidence | Covered |
| MOD-004 | Weighted-average pool exists by node-material-period | Fixture, task requirement and evaluator | WP2/WP8/WP10 | Fixture and reconciliation | Covered |
| MOD-005 | Pool quantity equals prior inventory plus receipts plus production | Fixture, task requirement and evaluator | WP2/WP8/WP10 | Equation-level check | Covered |
| MOD-006 | Pool value equals prior value plus receipt value plus production value | Fixture, task requirement and evaluator | WP2/WP8/WP10 | Equation-level check | Covered |
| MOD-007 | Pool value equals unit cost multiplied by pool quantity | Fixture, task requirement and evaluator | WP2/WP8/WP10 | Residual test | Covered |
| MOD-008 | All outflows use the same pool unit cost | Fixture, task requirement and evaluator | WP2/WP8/WP10 | Common-cost test | Covered |
| MOD-009 | Closing inventory retains quantity and value at all nodes | Fixture and output contract | WP2/WP8/WP10 | Roll-forward test | Covered |
| MOD-010 | Production value equals eligible base plus configured markup/value-add | Fixture, cost policy and evaluator | WP2/WP5/WP10 | Fixture and ledger test | Covered |
| MOD-011 | Receipt value equals dispatched value plus configured capitalised additions | Fixture, cost policy and evaluator | WP2/WP5/WP10 | Fixture and lane ledger test | Covered |
| MOD-012 | Zero-quantity pools have zero value and safe unit-cost treatment | Bounds, epsilon and pool-on logic | ADR-003/ADR-009 | Zero-pool fixtures | Controlled-open |
| MOD-013 | Quantity, value and unit-cost bounds are finite and documented | Bound propagation report | ADR-009/WP5 | Envelope and violation tests | Controlled-open |
| MOD-014 | External purchase, configured logistics, attributable fixed cost, conversion/setup/overhead/surge and markup are capitalised | Cost policy and ledger rules | ADR-005/WP5 | Classification and roll-forward tests | Controlled-open |
| MOD-015 | Holding, horizon activation and shortage/service are not capitalised | Cost policy and objective | ADR-005/WP5 | Classification test | Controlled-open |
| MOD-016 | Every cost appears exactly once and markup uses only eligible base | Cost policy, output contract and evaluator | WP5/WP8/WP10 | Double-count/markup tests | Covered |
| MOD-017 | Precomputed intermediate, cumulative-path, terminal and reference-solution values are prohibited as model inputs | Cost policy and evaluator leakage check | WP5/WP10 | Hidden leakage test | Covered |
| MOD-018 | Objective is lexicographic: shortage, economic value/cost, then surplus/activation tie-break | Objective requirement and evaluator | ADR-006/WP8/WP10 | Stage-lock and anti-dilution evidence | Controlled-open |
| MOD-019 | Stage 2 includes served terminal value and closing inventory value at every node | Objective requirement and evaluator | ADR-006/WP8/WP10 | Objective recomputation | Covered |
| MOD-020 | MOQ, order multiples, fixed orders, activation, capacity, storage, lead time and lane capacity apply | Task requirement and evaluator | ADR-007/WP8/WP10 | Constraint reconciliation | Controlled-open |
| MOD-021 | Every route exposes an explicit MILP or MINLP; exact, relaxed, approximate and heuristic solution strategies are permitted around that formulation with disclosure | Formulation and method/status policy | ADR-012/WP8/WP9 | Model inspection and metadata/report consistency | Covered |
| MOD-022 | Bounds, gaps, starts, runtime and solver evidence are reported where applicable | Submission metadata and solver report contract | WP8/WP9/WP10 | Log/metadata reconciliation | Covered |
| MOD-023 | Resilience measures are student-defined and at least one intervention changes the decision | Brief, outputs and app | WP9/WP10 | Evidence and implementation review | Covered |

## 4. Scenarios

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| SCN-001 | BASE preserves normal data and remains immutable | Dataset-package builder and validator | WP6 | Identity/hash test | Covered |
| SCN-002 | SCN-01 reduces the controlled Tier-4 silicon source to 30% in P03–P05 and 60% in P06, recovering in P07 | Scenario impacts | WP6 | Exact target/period/multiplier test | Covered |
| SCN-003 | SCN-02 applies Asia–Europe transit ×1.75, freight ×1.40 and capacity ×0.75 in P02–P07, with air available | Scenario impacts | WP6 | Exact transformation test | Covered |
| SCN-004 | SCN-03 applies Tier-1 unavailability in P04, 50% in P05 and recovery in P06 | Scenario impacts | WP6 | Exact recovery test | Covered |
| SCN-005 | SCN-04 reduces multiple Tier 2–Tier 4 nodes in one region by 20–40% | Scenario impacts | WP6 | Target and range test | Covered |
| SCN-006 | SCN-05 combines SCN-01/02 with 10–15% terminal-demand uplift | Scenario impacts | WP6 | Overlap and uplift test | Covered |
| SCN-007 | Package-local impacts may target supported node, organisation, parent, region, lane, recipe, material, external-price, conversion and demand entities | Scenario schema and common data-preparation path | WP1/WP6 | Target-domain tests | Covered |
| SCN-008 | Recovery is explicit and package-local transformations are deterministic | Impact data and dataset-package validator | WP6 | Repeated package build | Covered |
| SCN-009 | `STRESS_ONLY` is optional; when retained, it is distinguished from fresh re-optimisation in metadata, results and app | Run-mode vocabulary and application contract | WP1/WP8/WP9 | Cross-output comparison | Covered |
| SCN-010 | All six supplied complete datasets are imported and validated; BASE, at least two candidate-justified stress examples and new authored versions provide solve evidence | Consultant task and evidence contracts | WP6/WP8/WP9 | Evidence inventory and generality probe | Covered |

## 5. Raw data contracts

All field-level types, keys, domains, units and generation rules from the v0.3 specification must be present in shared configuration, generated dictionary, machine schemas, generator and validators.

| ID | Required raw file | Primary coverage | WP | Status |
|---|---|---|---|---|
| DAT-001 | `planning_calendar.csv` | 12 periods, dates and terminal flag | WP1/WP6 | Covered |
| DAT-002 | `supplier_organisations.csv` | Organisation hierarchy, tiers, geography and risk | WP4 | Covered |
| DAT-003 | `network_nodes.csv` | Generic nodes, owner, tier, boundary/processing/pooling flags | WP4 | Covered |
| DAT-004 | `plants.csv` | Fixed four plant nodes and priorities | WP4 | Covered |
| DAT-005 | `materials.csv` | Materials, families, UOM and terminal status | WP4 | Covered |
| DAT-006 | `transformation_recipes.csv` | Output, group, blend/exclusive mode, yield, setup/min-run | WP4 | Covered |
| DAT-007 | `transformation_inputs.csv` | Recipe inputs and coefficients | WP4 | Covered |
| DAT-008 | `material_flow_approvals.csv` | Approved source/destination/material/effective path | WP4 | Covered |
| DAT-009 | `supply_contracts.csv` | Currency, Incoterm, MOQ, multiples, fixed and activation controls; redundant `pricing_method` removed by CN-003 | WP1/WP5 | Covered |
| DAT-010 | `incoterm_rules.csv` | Cost responsibility abstraction; active/effective master-record evolution and governed creation required by WP8 | WP5/WP8/WP9 | Covered |
| DAT-011 | `import_duty_rates.csv` | Origin/destination/material-family duty | WP5 | Covered |
| DAT-012 | `source_capacity.csv` | External/intermediate source capacity by period | WP6 | Covered |
| DAT-013 | `transformation_capacity.csv` | Regular/surge processing capacity | WP6 | Covered |
| DAT-014 | `shipping_lanes.csv` | Mode, lead time, capacity and logistics costs | WP5 | Covered |
| DAT-015 | `external_source_prices.csv` | Boundary-source price only | WP5 | Covered |
| DAT-016 | `conversion_costs.csv` | Conversion, setup, overhead and markup inputs | WP5 | Covered |
| DAT-017 | `cost_allocation_rules.csv` | Capitalisation, stage, allocation basis, markup and ledger | WP5 | Covered |
| DAT-018 | `inventory_policies.csv` | Storage, holding and terminal policies | WP6 | Covered |
| DAT-019 | `opening_inventory.csv` | Opening quantity, unit cost and value | WP6 | Covered |
| DAT-020 | `terminal_demand.csv` | Plant-terminal-material-period demand and service weight | WP6 | Covered |
| DAT-021 | `supplier_performance_history.csv` | Exploratory performance evidence | WP6 | Covered |
| DAT-022 | `incident_history.csv` | Exploratory disruption evidence | WP6 | Covered |
| DAT-023 | `disruption_scenarios.csv` | BASE/SCN-01–05 metadata | WP6 | Covered |
| DAT-024 | `disruption_impacts.csv` | Targeted period impacts and recovery | WP6 | Covered |
| DAT-025 | `fx_rates.csv` | Currency-to-EUR rates | WP5 | Covered |
| DAT-026 | `baseline_standard_costs.csv` | Synthetic diagnostic input retired by CN-005; no replacement raw table | WP8 | Retired |

For every active `DAT` row, acceptance requires schema validation, dictionary
coverage, deterministic generation, foreign-key/domain checks,
model-ingestion test and at least one targeted negative test. Retired DAT-026
is instead subject to an absence check.

## 6. Scale, generation and validation

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| GEN-001 | Private deterministic seed strategy and synthetic entities | Generator config | WP4–WP6 | Byte-identical regeneration | Covered |
| GEN-002 | Dimensions precede facts; physical feasibility precedes economics | Build graph | WP4–WP6 | Pipeline integration | Covered |
| GEN-003 | Target scale: 4 plants, 4 tiers, 32–40 nodes, 30–40 materials, 6–8 terminals, 40–60 recipes, 120–180 approvals/contracts, 90–150 lanes, 12 periods and 6 scenarios | Generation config | WP4–WP7 | Counts and depth profile | Covered |
| GEN-004 | Network contains controlled multi-sourcing and hidden dependencies | Graph generator | WP4 | Path/concentration tests | Covered |
| GEN-005 | BASE is physically feasible with zero shortage and selected binding constraints | Constructive generation and private smoke check | WP6/WP7 | Feasibility certificate | Covered |
| GEN-006 | The data permits explainably different decisions under baseline and recursive economics | Commercial calibration | WP5/WP7 | Accepted alternative-plan and smoke-solve comparison | Covered |
| GEN-007 | Bounds and epsilon are constructed from safe theoretical envelopes | Bound propagation | WP5/WP7 | Accepted bound report and violation tests | Covered |
| GEN-008 | Scenario severity creates meaningful cost/service/resilience consequences | Scenario calibration | WP6/WP7 | Accepted materiality and plausibility review | Covered |
| VAL-001 | Keys, FKs, domains, periods, dates, UOM and currencies validate | Structural validator | WP1/WP4–WP6 | Positive/negative fixtures | Covered |
| VAL-002 | Network and material graph are valid and acyclic | Graph validator | WP4 | Cycle/orphan fixtures | Covered |
| VAL-003 | Approved paths, contracts, lanes and effective dates align | Cross-file validator | WP4/WP5 | Invalid-path fixtures | Covered |
| VAL-004 | Physical balances, lead times, capacities, MOQ/multiples, storage and service reconcile | Submission validator | WP10 | Independent recomputation | Covered |
| VAL-005 | Every pool, shipment, transformation, inventory and terminal flow reconciles in value | Fixture and submission reconciler | WP2/WP10 | Equation output | Covered |
| VAL-006 | Cost ledger has no double count, disappearance or invalid markup | Cost policy and evaluator | WP5/WP10 | Adversarial tests | Covered |
| VAL-007 | Zero-pool, common-outflow-cost and anti-dilution controls hold | Fixture and evaluator controls | WP2/WP10 | Targeted negative tests | Covered |
| VAL-008 | Default tolerances are applied consistently | Shared tolerance config | WP1/WP10 | Boundary fixtures | Covered |
| REL-001 | No release before fixture, generated dataset, schemas, depth/calibration evidence and acceptance checks pass cleanly | No-release pipeline gate | WP9 | Deliberate failing build | Covered |
| REL-002 | Release contains no private seed, unapproved model result, hidden range, hidden test, prompt or calibration evidence; the approved public BASE benchmark remains non-prescriptive | Allow-list/private scanner | WP9 | Leak fixtures and benchmark allow-list test | Covered |

## 7. Miniature fixture and implementation policy

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| FIX-001 | Five-period, four-layer (Tier 4/3/2 + plants) hand-worked fixture with multi-sourcing at three hops is supplied (amended by CN-002) | Fixture pack | WP2 | File inventory | Covered |
| FIX-002 | Published quantity/value/unit-cost and Stage-2 totals reproduce, including the closing value-conservation identity (capitalised cost + opening book value = Stage 2) | Expected reconciliation | WP2 | Regression tests | Covered |
| FIX-003 | Negative variants detect accounting and physical errors | Private fixture suite | WP2 | Intended-failure tests | Covered |
| REF-001 | Students may use Python 3.12 or another approved consultancy runtime | Environment policy and starter guidance | WP8/WP9 | Clean candidate journey | Covered |
| REF-002 | Every submitted model is an explicit algebraic MILP or MINLP; Pyomo, PuLP or another suitable algebraic library is permitted where it supports the formulation | Method-neutral formulation contract | WP8/WP10 | Formulation inspection and defence | Covered |
| REF-003 | At least one accessible algebraic MILP or MINLP solver route is documented without prescribing the candidate method | Solver and status guide | WP9 | Clean candidate journey | Covered |
| REF-004 | IPOPT may solve continuous nonlinear subproblems but integer feasibility must be enforced by the disclosed recursive MINLP workflow; an accessible solver route and fallback are completed under ADR-010 | Method/status policy | ADR-010/WP9 | Integrality evidence and approval | Handoff |
| REF-005 | Runtime budgets are calibrated for a fair candidate journey and permit documented incumbents and controlled stored results | Runtime policy | WP9/WP10 | Pilot timing profile | Handoff |
| REF-006 | The approved public BASE incumbent calibrates reproduction without acting as a model input or unique allocation; private author evidence remains private | Benchmark contract, frozen viability and calibration records | WP3/WP7/WP8 | Privacy, benchmark-isolation and assessment review | Covered |

## 8. Student deliverables, application and outputs

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| STU-001 | Student builds a valid 12-week Tier-N plan, reproduces the BASE benchmark controls, evaluates selected complete data realities and recommends resilience action | Controlled brief | WP8/WP9 | Brief/spec comparison | Covered |
| STU-002 | Learning pack includes task requirements, context, glossary, AI-native guide, dictionary, schemas, default case, cost policy, scenario catalogue and fixture | Student release | WP9 | Release inventory | Covered |
| STU-003 | Submission includes code, locked dependencies, tests, model/solver/validation reports, recommendation, production note, slides and AI disclosure | Starter/manifest | WP9/WP10 | Required-path test | Covered |
| STU-004 | App lets users govern data, explore the supply graph, configure policy, solve, compare and interpret decisions without prescribed view names | App contract | WP8/WP9 | Controlled functional journeys | Covered |
| STU-005 | App identifies result age, dataset/configuration versions, state, method and solver status | App contract | WP8/WP9/WP10 | Stored/async result fixtures | Covered |
| STU-006 | App distinguishes a complete dataset change from a policy change and, if retained, stress-only evaluation from re-optimisation | App/output contract | WP8/WP9/WP10 | Cross-result check | Covered |
| STU-007 | App exposes infeasibility, solver failure, stale results and failed validation | Failure-state contract | WP9/WP10 | Failure probes | Covered |
| STU-008 | App provides version-preserving master-data authoring, mandatory Incoterm CRUD/activity and immutable complete dataset publication | Data and app contracts | WP8/WP9 | Controlled data journey | Covered |
| STU-009 | App provides intuitive visual upstream/downstream supply-graph exploration connected to data and result effects | App contract | WP8/WP9 | Assessor-selected graph journey | Covered |
| STU-010 | App satisfies the proportionate integrity, security, accessibility, responsiveness, failure-safety, observability and reproducibility baseline | NFR and evidence contracts | WP8/WP9/WP10 | Tests, measurements and demonstrations | Covered |
| OUT-001 | `run_metadata.json` | Output schema and submission contract | WP1/WP8/WP10 | Schema/log comparison | Covered |
| OUT-002 | `metrics.json` | Output schema and submission contract | WP1/WP8/WP10 | Independent recomputation | Covered |
| OUT-003 | `orders.csv` | Output schema and submission contract | WP1/WP8/WP10 | Order constraint checks | Covered |
| OUT-004 | `shipments.csv` | Output schema and submission contract | WP1/WP8/WP10 | Flow/value/lead-time checks | Covered |
| OUT-005 | `production.csv` | Output schema and submission contract | WP1/WP8/WP10 | Recipe/value checks | Covered |
| OUT-006 | `inventory_cost_rollforward.csv` | Output schema and submission contract | WP1/WP8/WP10 | Pool reconciliation | Covered |
| OUT-007 | `demand_service.csv` | Output schema and submission contract | WP1/WP8/WP10 | Service reconciliation | Covered |
| OUT-008 | `cost_component_ledger.csv` | Output schema and submission contract | WP1/WP8/WP10 | Unique-class test | Covered |
| OUT-009 | `cost_lineage.csv` | Output schema and submission contract | WP1/WP8/WP10 | Contribution reconciliation | Covered |
| OUT-010 | Retire `recursive_cost_reconciliation.csv` without replacement; derive recursive values inside the formulation and validate them independently in memory | CN-004, model inspection and evaluator contract | WP8/WP9/WP10 | Formulation inspection, in-memory LHS/RHS checks and raw-schema isolation tests | Covered |
| OUT-011 | `constraint_report.csv` | Output schema and submission contract | WP1/WP8/WP10 | Independent LHS/RHS | Covered |
| OUT-012 | `reconciliation_summary.json` | Common run-level reconciliation contract | WP1/WP8/WP10 | Detailed/summary comparison | Covered |
| OUT-013 | `baseline_comparison.csv` | Synthetic diagnostic comparison retired by CN-005; benchmark evidence is supplied separately | WP8/WP10 | Absence and benchmark-reproduction checks | Retired |
| OUT-014 | Replace closed `scenario_comparison.csv` with dataset/configuration comparison evidence | Output schema and submission contract | WP8/WP9/WP10 | Comparison-set evidence check | Covered |
| OUT-015 | Retire `scenario_results.csv`; run metrics and comparison-set evidence cover its former purpose | Output burden decision | WP8/WP9 | Absence and duplication review | Covered |

## 9. Assessment and AI-assisted evaluation

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| ASM-001 | Rubric weights are 8/8/16/14/15/14/10/7/5/3 | Candidate assessment rubric 1.1.0 | WP9 | Total and version check | Covered |
| ASM-002 | Candidate-facing evaluation material is limited to the rubric | Release allow-list and clean-room validator | WP9 | Release-content check | Covered |
| ASM-003 | No deterministic submission evaluator or hidden answer key is used | WP9 contract and private AI-agent system prompt | WP9 | Prompt and process review | Covered |
| ASM-004 | AI scores cited evidence with criterion rationale and confidence | Private AI-agent system prompt | WP9 | Citation/calibration review | Covered |
| ASM-005 | AI gives explicit attention to invalid flows, omitted logic, contradictions, non-implemented resilience, concealed infeasibility and unsupported optimality without treating them as automatic conclusions | Private AI-agent system prompt | WP9 | Prompt review | Covered |
| ASM-006 | Human moderation addresses contradictions, inaccessible evidence and material uncertainty | Review workflow | WP9 | Moderation review | Covered |
| ASM-007 | Technical defence tests ownership of formulation, reconciliation, solver interpretation and AI use | Rubric and assessor prompts generated from submitted evidence | WP9 | Defence record | Covered |
| ASM-008 | Resubmission and appeal policies are separately approved if required | Assessment operations policy | Mobilisation | Governance approval | Policy-open |
| ASM-009 | Reviewer calibration uses representative submissions without becoming a deterministic score engine | Moderation examples | Operations | Cross-review analysis | Handoff |
| ASM-010 | Evaluation output records scores, rationales, citations, inaccessible evidence and material judgement | AI-agent system-prompt output format | WP9 | Record review | Covered |

## 10. ADR and release closure

| ID | Required decision | Owner | Status |
|---|---|---|---|
| ADR-001 | Narrative and scope | Capstone/domain lead | Controlled-open |
| ADR-002 | Network and time | Data/optimisation lead | Controlled-open |
| ADR-003 | Pooling and opening value | Optimisation/domain lead | Controlled-open |
| ADR-004 | Recursive value equations | Optimisation lead | Controlled-open |
| ADR-005 | Cost classification | Domain/optimisation lead | Controlled-open |
| ADR-006 | Objective and anti-dilution | Optimisation/evaluation lead | Controlled-open |
| ADR-007 | MOQ, setup and capacity | Optimisation/domain lead | Controlled-open |
| ADR-008 | Scenarios | Domain/data lead | Controlled-open |
| ADR-009 | Generator and bounds | Data/optimisation lead | Controlled-open |
| ADR-010 | Solver, runtime, access and fallback | Optimisation/evaluation lead | Controlled-open |
| ADR-011 | Outputs and tolerances | Data/evaluation lead | Controlled-open |
| ADR-012 | Approximation, assessment access and defence | Capstone/evaluation lead | Controlled-open |

## 11. Superseded requirements

The following previous-plan assumptions are explicitly superseded:

- a two-tier-only supplier-site/BOM network;
- a fixed-price MILP as the assessed economic model;
- tier-specific output files such as `tier2_orders.csv` and `tier1_production.csv`;
- a 19-file raw-data contract;
- the earlier 8-ADR sequence;
- the earlier rubric weights; and
- a release path that did not require a recursive-value fixture, full value reconciliation or solver-confidence evidence.

They must not remain in schemas, starter code, brief text, private authoring
tools or evaluator logic except as clearly labelled historical material.

## 12. Traceability conclusion

The v0.3 delivery plan covers every material requirement group in the CAP-001 v0.3 specification and the inherited common standard v0.2.

The open items are intentional release controls:

1. ADR-001 through ADR-012;
2. exact calibrated counts, coefficients, bounds, epsilon, solver and runtime policy;
3. exact scenario coefficients where the specification gives a range; and
4. moderation, resubmission and appeal policy.

None may be resolved by silently changing the fixed Tier-N network,
weighted-average recursive-cost policy, published BASE benchmark, dataset
catalogue, output contract or AI-native evidence standard.
