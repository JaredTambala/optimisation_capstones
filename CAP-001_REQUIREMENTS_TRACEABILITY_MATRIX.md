# CAP-001 Requirements Traceability Matrix

## Document control

| Field | Value |
|---|---|
| Matrix version | 0.2 |
| Date | 30 July 2026 |
| Scope | CAP-001 Tier-N End-to-End Cost and Resilience Optimisation |
| Primary specification | *CAP-001 Tier-N End-to-End Cost Model, Modelling Decisions and Dataset Generation Specification* v0.3 |
| Primary specification SHA-256 | `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` |
| Inherited standard | *Optimisation, Search and Decision Intelligence Capstone Control Standard* v0.2 |
| Inherited standard SHA-256 | `2741ebd6b1e01e4102c39c9f43de3a9f05b081aa61a3efd2838a431024a45637` |
| Delivery plan | *CAP-001 Delivery and Assessment Implementation Plan* v0.3 |
| Precedence | CAP-001 v0.3, then approved ADRs/shared configuration for implementation detail, then common standard v0.2 for shared controls |

## How to use this matrix

This matrix demonstrates planning coverage. It does not claim that implementation evidence exists.

- **Covered** — the plan assigns an artefact and verification route.
- **Controlled-open** — the specification intentionally requires an ADR, calibration result or numerical decision before release.
- **Policy-open** — assessment governance must approve the consequence before release.
- **Superseded** — a prior two-tier requirement is no longer applicable and must not be carried into the release.

As each work package completes, the implementation team should add an evidence path, test identifier, result and approval date.

WP1 was completed and accepted on 31 July 2026. Its implementation evidence is
recorded in `docs/WP1_ACCEPTANCE_REPORT.md`; the planning statuses below continue
to describe end-to-end coverage rather than claiming that later work packages
have been implemented.

## 1. Common control requirements

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| COM-001 | Same fixed context, data, default case, scenarios, baseline, controls and rubric for all students | Decision configuration, brief and manifest | WP1/WP9 | Cross-artefact comparison | Covered |
| COM-002 | AI use is expected; consultant remains accountable | Brief, `AI_USAGE_TEMPLATE.md`, defence | WP9/WP10 | Evidence and defence review | Covered |
| COM-003 | Interactive decision-support application is mandatory | App contract and submission validator | WP9/WP10 | Launch and functional probe | Covered |
| COM-004 | App supports input review, meaningful controls, results, baseline, trade-offs, recommendation, export and failure states | App evidence guide | WP9 | View and interaction inventory | Covered |
| COM-005 | Private generator, seeds, references, ranges, adversarial tests, evaluator prompts and calibration remain private | Repository separation and allow-list builder | WP9 | Leak negative test | Covered |
| COM-006 | Release manifest records versions, hashes, row counts, default case, commands and outputs | `release_manifest.json` | WP9 | Schema and checksum tests | Covered |
| COM-007 | Narrative, schemas, dictionary, generator, references and evaluator share one approved configuration | Decision configuration and drift tests | WP1 | Generated/verified artefact comparison | Covered |
| COM-008 | Submission exposes one command each for install, tests, baseline, assessed result and app | `submission.yaml` and runner | WP9/WP10 | Clean execution | Covered |
| COM-009 | Authoritative data can be mounted read-only | Configured data-directory interface | WP1/WP10 | Read-only mount test | Covered |
| COM-010 | Required run metadata, metrics, constraints, reconciliation, baseline and app evidence are machine-readable | Output schemas | WP1/WP7 | Schema and recomputation | Covered |
| COM-011 | Solver status and optimality language are controlled | Status vocabulary and claim checker | WP1/WP10 | Log/metadata/report comparison | Covered |
| COM-012 | Solver access cannot create an undeclared grading advantage | Solver-access and fallback policy | WP3/WP9 | Route benchmark and policy review | Controlled-open |
| COM-013 | 20–30 minute technical defence is required | Defence guide and record | WP10 | Structured defence | Covered |
| COM-014 | 10–12 slide client presentation is required | Presentation guide | WP9/WP10 | Artefact review | Covered |
| COM-015 | Quality gates precede qualitative scoring | Evaluation stage controller | WP10 | Deliberately defective submissions | Covered |
| COM-016 | AI scoring cites evidence and exposes confidence/review flags | Structured evaluator | WP10 | Calibration and citation test | Covered |
| COM-017 | Human review handles contradictions, low confidence and grade boundaries | Reviewer workflow | WP10 | Trigger fixtures | Covered |
| COM-018 | Release and assessment must be reproducible in a clean environment | Locked environments and clean-room jobs | WP9/WP10 | End-to-end rerun | Covered |
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
| SCP-006 | External boundary prices are allowed; Tier 1–Tier 3 values are recursive | Pricing policy and model controls | WP5/WP7 | Boundary/leakage tests | Covered |
| SCP-007 | Same-period conversion; receipts/production usable in period | Timing ADR and model | ADR-002/WP7 | Boundary fixture | Controlled-open |
| SCP-008 | No WIP and no post-P12 arrival | Model and validator | WP6/WP7 | Negative tests | Covered |
| SCP-009 | Opening inventory includes quantity and book value | Input schema and pool equations | WP1/WP7 | Roll-forward fixture | Covered |
| SCP-010 | Release exclusions are not introduced through hidden fields | Configuration/schema allow-list | WP1/WP9 | Schema and release scan | Covered |

## 3. Baseline, recursive model and cost policy

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| MOD-001 | Fixed-price MILP is mandatory diagnostic baseline | Baseline model | WP3/WP7 | Reproducible solve | Covered |
| MOD-002 | Baseline uses isolated `baseline_standard_costs.csv` and the same physical/commercial/timing controls | Baseline ingestion and comparison tests | WP5/WP7 | Control-parity/leak tests | Covered |
| MOD-003 | Assessed semantics are a bounded non-convex recursive-cost MINLP | Recursive model contract | WP3/WP7 | Formulation review and bounds | Covered |
| MOD-004 | Weighted-average pool exists by node-material-period | Pool variables/equations | WP2/WP7 | Fixture and reconciliation | Covered |
| MOD-005 | Pool quantity equals prior inventory plus receipts plus production | Quantity roll-forward | WP2/WP7 | Equation-level check | Covered |
| MOD-006 | Pool value equals prior value plus receipt value plus production value | Value roll-forward | WP2/WP7 | Equation-level check | Covered |
| MOD-007 | Pool value equals unit cost multiplied by pool quantity | Bilinear pool equation or faithful declared approximation | WP2/WP7 | Residual test | Covered |
| MOD-008 | All outflows use the same pool unit cost | Outflow value equations | WP2/WP7 | Common-cost test | Covered |
| MOD-009 | Closing inventory retains quantity and value at all nodes | Inventory equations/output | WP2/WP7 | Roll-forward test | Covered |
| MOD-010 | Production value equals eligible base plus configured markup/value-add | Transformation value equations | WP2/WP7 | Fixture and ledger test | Covered |
| MOD-011 | Receipt value equals dispatched value plus configured capitalised additions | Shipment value equations | WP2/WP7 | Fixture and lane ledger test | Covered |
| MOD-012 | Zero-quantity pools have zero value and safe unit-cost treatment | Bounds, epsilon and pool-on logic | ADR-003/ADR-009 | Zero-pool fixtures | Controlled-open |
| MOD-013 | Quantity, value and unit-cost bounds are finite and documented | Bound propagation report | ADR-009/WP5 | Envelope and violation tests | Controlled-open |
| MOD-014 | External purchase, configured logistics, attributable fixed cost, conversion/setup/overhead/surge and markup are capitalised | Cost policy and ledger rules | ADR-005/WP5 | Classification and roll-forward tests | Controlled-open |
| MOD-015 | Holding, horizon activation and shortage/service are not capitalised | Cost policy and objective | ADR-005/WP5 | Classification test | Controlled-open |
| MOD-016 | Every cost appears exactly once and markup uses only eligible base | Unique ledger and reconciliation | WP5/WP7 | Double-count/markup tests | Covered |
| MOD-017 | Baseline standard costs are prohibited in recursive calculation | Separate data/model path | WP7/WP8 | Hidden leakage test | Covered |
| MOD-018 | Objective is lexicographic: shortage, economic value/cost, then surplus/activation tie-break | Objective configuration/model | ADR-006/WP7 | Stage-lock and anti-dilution tests | Controlled-open |
| MOD-019 | Stage 2 includes served terminal value and closing inventory value at every node | Objective/model | ADR-006/WP7 | Objective recomputation | Covered |
| MOD-020 | MOQ, order multiples, fixed orders, activation, capacity, storage, lead time and lane capacity apply | Physical/commercial model | ADR-007/WP7 | Constraint reconciliation | Controlled-open |
| MOD-021 | Exact, relaxed, approximate and heuristic routes are permitted with disclosure | Method/status policy | ADR-012/WP9 | Metadata/report consistency | Controlled-open |
| MOD-022 | Bounds, gaps, starts, runtime and solver evidence are reported where applicable | Metadata and solver report | WP3/WP7 | Log reconciliation | Covered |
| MOD-023 | Resilience measures are student-defined and at least one intervention changes the decision | Brief, outputs and app | WP9/WP10 | Evidence and implementation review | Covered |

## 4. Scenarios

| ID | Requirement | Planned artefact/control | Plan/WP | Verification | Status |
|---|---|---|---|---|---|
| SCN-001 | BASE preserves normal data and remains immutable | Scenario engine | WP6 | Identity/hash test | Covered |
| SCN-002 | SCN-01 reduces the controlled Tier-4 silicon source to 30% in P03–P05 and 60% in P06, recovering in P07 | Scenario impacts | WP6 | Exact target/period/multiplier test | Covered |
| SCN-003 | SCN-02 applies Asia–Europe transit ×1.75, freight ×1.40 and capacity ×0.75 in P02–P07, with air available | Scenario impacts | WP6 | Exact transformation test | Covered |
| SCN-004 | SCN-03 applies Tier-1 unavailability in P04, 50% in P05 and recovery in P06 | Scenario impacts | WP6 | Exact recovery test | Covered |
| SCN-005 | SCN-04 reduces multiple Tier 2–Tier 4 nodes in one region by 20–40% | Scenario impacts | WP6 | Target and range test | Controlled-open |
| SCN-006 | SCN-05 combines SCN-01/02 with 10–15% terminal-demand uplift | Scenario impacts | WP6 | Overlap and uplift test | Controlled-open |
| SCN-007 | Impacts may target supported node, organisation, parent, region, lane, recipe, material, external-price, conversion and demand entities | Scenario schema/engine | WP1/WP6 | Target-domain tests | Covered |
| SCN-008 | Recovery is explicit and transformations are deterministic | Impact data/engine | WP6 | Repeated scenario fixture | Covered |
| SCN-009 | `STRESS_ONLY` and `REOPTIMISE` are distinguished in metadata, results and app | Run-mode vocabulary | WP1/WP7/WP9 | Cross-output comparison | Covered |
| SCN-010 | All six scenarios are evaluated; recourse and shortage are explainable | Reference and student result contracts | WP7/WP9 | Evidence inventory | Covered |

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
| DAT-009 | `supply_contracts.csv` | Pricing method, MOQ, multiples, fixed and activation controls | WP5 | Covered |
| DAT-010 | `incoterm_rules.csv` | Cost responsibility abstraction | WP5 | Covered |
| DAT-011 | `import_duty_rates.csv` | Origin/destination/material-family duty | WP5 | Covered |
| DAT-012 | `source_capacity.csv` | External/intermediate source capacity by period | WP6 | Covered |
| DAT-013 | `transformation_capacity.csv` | Regular/surge processing capacity | WP6 | Covered |
| DAT-014 | `shipping_lanes.csv` | Mode, lead time, capacity and logistics costs | WP5 | Covered |
| DAT-015 | `external_source_prices.csv` | Boundary-source price only | WP5 | Covered |
| DAT-016 | `conversion_costs.csv` | Conversion, setup, overhead, surge and markup inputs | WP5 | Covered |
| DAT-017 | `cost_allocation_rules.csv` | Capitalisation, stage, allocation basis, markup and ledger | WP5 | Covered |
| DAT-018 | `inventory_policies.csv` | Storage, holding and terminal policies | WP6 | Covered |
| DAT-019 | `opening_inventory.csv` | Opening quantity, unit cost and value | WP6 | Covered |
| DAT-020 | `terminal_demand.csv` | Plant-terminal-material-period demand and service weight | WP6 | Covered |
| DAT-021 | `supplier_performance_history.csv` | Exploratory performance evidence | WP6 | Covered |
| DAT-022 | `incident_history.csv` | Exploratory disruption evidence | WP6 | Covered |
| DAT-023 | `disruption_scenarios.csv` | BASE/SCN-01–05 metadata | WP6 | Covered |
| DAT-024 | `disruption_impacts.csv` | Targeted period impacts and recovery | WP6 | Covered |
| DAT-025 | `fx_rates.csv` | Currency-to-EUR rates | WP5 | Covered |
| DAT-026 | `baseline_standard_costs.csv` | Baseline-only standard costs | WP5 | Covered |

For every `DAT` row, acceptance requires schema validation, dictionary coverage, deterministic generation, foreign-key/domain checks, model-ingestion test and at least one targeted negative test.

## 6. Scale, generation and validation

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| GEN-001 | Private deterministic seed strategy and synthetic entities | Generator config | WP4–WP6 | Byte-identical regeneration | Covered |
| GEN-002 | Dimensions precede facts; physical feasibility precedes economics | Build graph | WP4–WP6 | Pipeline integration | Covered |
| GEN-003 | Target scale: 4 plants, 4 tiers, 32–40 nodes, 30–40 materials, 6–8 terminals, 40–60 recipes, 120–180 approvals/contracts, 90–150 lanes, 12 periods and 6 scenarios | Generation config | WP4–WP8 | Counts and runtime profile | Controlled-open |
| GEN-004 | Network contains controlled multi-sourcing and hidden dependencies | Graph generator | WP4 | Path/concentration tests | Covered |
| GEN-005 | BASE is physically feasible with zero shortage and selected binding constraints | Feasibility construction | WP6/WP7 | Reference result | Covered |
| GEN-006 | Fixed and recursive models make explainably different decisions | Commercial calibration | WP5/WP7/WP8 | Baseline comparison | Controlled-open |
| GEN-007 | Bounds and epsilon are constructed from safe theoretical envelopes | Bound propagation | WP5/WP8 | Bound report/adversarial tests | Controlled-open |
| GEN-008 | Scenario severity creates meaningful cost/service/resilience consequences | Scenario calibration | WP6/WP8 | Plausibility review | Controlled-open |
| VAL-001 | Keys, FKs, domains, periods, dates, UOM and currencies validate | Structural validator | WP1/WP4–WP6 | Positive/negative fixtures | Covered |
| VAL-002 | Network and material graph are valid and acyclic | Graph validator | WP4 | Cycle/orphan fixtures | Covered |
| VAL-003 | Approved paths, contracts, lanes and effective dates align | Cross-file validator | WP4/WP5 | Invalid-path fixtures | Covered |
| VAL-004 | Physical balances, lead times, capacities, MOQ/multiples, storage and service reconcile | Post-solve validator | WP7 | Independent recomputation | Covered |
| VAL-005 | Every pool, shipment, transformation, inventory and terminal flow reconciles in value | Recursive reconciler | WP2/WP7 | Equation output | Covered |
| VAL-006 | Cost ledger has no double count, disappearance or invalid markup | Ledger validator | WP5/WP7 | Adversarial tests | Covered |
| VAL-007 | Zero-pool, common-outflow-cost and anti-dilution controls hold | Adversarial validator | WP2/WP8 | Targeted negative tests | Covered |
| VAL-008 | Default tolerances are applied consistently | Shared tolerance config | WP1/WP7/WP10 | Boundary fixtures | Covered |
| REL-001 | No release before fixture, generator, schemas, both references and acceptance checks pass cleanly | No-release pipeline gate | WP9 | Deliberate failing build | Covered |
| REL-002 | Release contains no private seed, model result, range, hidden test, prompt or calibration evidence | Allow-list/private scanner | WP9 | Leak fixtures | Covered |

## 7. Miniature fixture and reference stack

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| FIX-001 | Five-period, four-layer (Tier 4/3/2 + plants) hand-worked fixture with multi-sourcing at three hops is supplied (amended by CN-002) | Fixture pack | WP2 | File inventory | Covered |
| FIX-002 | Published quantity/value/unit-cost and Stage-2 totals reproduce, including the closing value-conservation identity (capitalised cost + opening book value = Stage 2) | Expected reconciliation | WP2 | Regression tests | Covered |
| FIX-003 | Negative variants detect accounting and physical errors | Private fixture suite | WP2/WP8 | Intended-failure tests | Covered |
| REF-001 | Reference language is Python 3.12 or approved consultancy runtime | Locked environment | WP3/WP7 | Environment manifest | Covered |
| REF-002 | Algebraic model uses Pyomo or approved solver-neutral equivalent | Model adapter | WP3/WP7 | Architecture review | Covered |
| REF-003 | Accessible fixed-price MILP route is available | HiGHS/approved equivalent | WP3/WP9 | Clean benchmark | Covered |
| REF-004 | Recursive solver route, licence/access and fallback are approved by ADR | Solver adapter/policy | ADR-010 | Benchmark and approval | Controlled-open |
| REF-005 | Fixture completes within 2 minutes; baseline within 5 minutes; recursive budgets follow calibrated policy | Runtime configuration | WP3/WP8 | Reference hardware profile | Controlled-open |
| REF-006 | Private reference set retains fixture exact results, baseline exact results and recursive best-known incumbent/bounds/logs | Reference ledger | WP7/WP8 | Independent review | Covered |

## 8. Student deliverables, application and outputs

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| STU-001 | Student builds a valid 12-week Tier-N plan, compares baseline/recursive methods, evaluates scenarios and recommends resilience action | Controlled brief | WP9 | Brief/spec comparison | Covered |
| STU-002 | Learning pack includes task requirements, context, glossary, AI-native guide, dictionary, schemas, default case, cost policy, scenario catalogue and fixture | Student release | WP9 | Release inventory | Covered |
| STU-003 | Submission includes code, locked dependencies, tests, model/solver/validation reports, recommendation, production note, slides and AI disclosure | Starter/manifest | WP9/WP10 | Required-path test | Covered |
| STU-004 | App contains executive, network, input/policy, baseline, recursive, waterfall/lineage, comparison, scenario, resilience, solver/validation and decision views | App contract | WP9 | View probe | Covered |
| STU-005 | App identifies result age, version, scenario, state, method and solver status | App contract | WP9/WP10 | Stored/async result fixtures | Covered |
| STU-006 | App distinguishes stress-only from re-optimised results | App/output contract | WP9/WP10 | Cross-view check | Covered |
| STU-007 | App exposes infeasibility, solver failure, stale results and failed validation | Failure-state contract | WP9/WP10 | Failure probes | Covered |
| OUT-001 | `run_metadata.json` | Output schema/writer | WP1/WP7 | Schema/log comparison | Covered |
| OUT-002 | `metrics.json` | Output schema/writer | WP1/WP7 | Independent recomputation | Covered |
| OUT-003 | `orders.csv` | Output schema/writer | WP1/WP7 | Order constraint checks | Covered |
| OUT-004 | `shipments.csv` | Output schema/writer | WP1/WP7 | Flow/value/lead-time checks | Covered |
| OUT-005 | `production.csv` | Output schema/writer | WP1/WP7 | Recipe/value checks | Covered |
| OUT-006 | `inventory_cost_rollforward.csv` | Output schema/writer | WP1/WP7 | Pool reconciliation | Covered |
| OUT-007 | `demand_service.csv` | Output schema/writer | WP1/WP7 | Service reconciliation | Covered |
| OUT-008 | `cost_component_ledger.csv` | Output schema/writer | WP1/WP7 | Unique-class test | Covered |
| OUT-009 | `cost_lineage.csv` | Output schema/writer | WP1/WP7 | Contribution reconciliation | Covered |
| OUT-010 | `recursive_cost_reconciliation.csv` | Output schema/writer | WP1/WP7 | LHS/RHS/tolerance test | Covered |
| OUT-011 | `constraint_report.csv` | Output schema/writer | WP1/WP7 | Independent LHS/RHS | Covered |
| OUT-012 | `reconciliation_summary.json` | Common run-level reconciliation summary | WP1/WP7 | Detailed/summary comparison | Covered |
| OUT-013 | `baseline_comparison.csv` | Output schema/writer | WP1/WP7 | Run comparison | Covered |
| OUT-014 | `scenario_comparison.csv` | CAP-specific detailed scenario comparison | WP1/WP7 | Scenario evidence check | Covered |
| OUT-015 | `scenario_results.csv` | Common method-scenario evaluation summary | WP1/WP7 | Detailed/summary comparison | Covered |

## 9. Assessment and AI-assisted evaluation

| ID | Requirement | Planned artefact/control | WP | Verification | Status |
|---|---|---|---|---|---|
| ASM-001 | Rubric weights are 8/8/16/14/15/14/10/7/5/3 | Rubric schema/addendum | WP10 | Total and version check | Covered |
| ASM-002 | Deterministic environment and quality checks run before AI scoring | Evaluation controller | WP10 | Stage-order test | Covered |
| ASM-003 | Hard physical, value and ledger failures cannot be hidden by qualitative strength | Gate policy/engine | WP10 | Defective submission | Policy-open |
| ASM-004 | AI scores cited evidence with criterion rationale and confidence | Structured evaluator | WP10 | Citation/calibration tests | Covered |
| ASM-005 | AI flags invalid flows, omitted logic, chart mismatch, non-implemented resilience, concealed infeasibility and unsupported optimality | Evaluator and deterministic flags | WP10 | Targeted defective samples | Covered |
| ASM-006 | Human review triggers for contradictions, uncertainty and within three points of key boundaries | Review workflow | WP10 | Trigger fixtures | Policy-open |
| ASM-007 | Technical defence tests ownership of formulation, reconciliation, solver interpretation and AI use | Defence guide | WP10 | Defence record | Covered |
| ASM-008 | Resubmission, appeal, partial-credit and gate-cap policies are approved before release | Assessment operations policy | Mobilisation/WP10 | Governance approval | Policy-open |
| ASM-009 | Strong, weak and defective calibration submissions score reproducibly | Calibration suite | WP8/WP10 | Repeat-run analysis | Covered |
| ASM-010 | Evaluation output is auditable and records evidence, missing evidence, flags, human changes and final decision | Assessment report schema | WP10 | Record completeness | Covered |

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

They must not remain in schemas, starter code, brief text, reference models or evaluator logic except as clearly labelled historical material.

## 12. Traceability conclusion

The v0.3 delivery plan covers every material requirement group in the CAP-001 v0.3 specification and the inherited common standard v0.2.

The open items are intentional release controls:

1. ADR-001 through ADR-012;
2. exact calibrated counts, coefficients, bounds, epsilon, solver and runtime policy;
3. exact scenario coefficients where the specification gives a range; and
4. quality-gate, partial-credit, boundary-review, resubmission and appeal policy.

None may be resolved by silently changing the fixed Tier-N network, weighted-average recursive-cost policy, fixed-price baseline, scenario catalogue, output contract or AI-native evidence standard.
