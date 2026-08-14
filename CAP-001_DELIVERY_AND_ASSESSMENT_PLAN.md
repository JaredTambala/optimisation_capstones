# CAP-001 Delivery and Assessment Implementation Plan

## Document control

| Field | Value |
|---|---|
| Plan | CAP-001 Supplier Allocation Under Disruption Risk — Tier-N End-to-End Cost and Resilience Optimisation |
| Plan version | 0.3 |
| Status | Updated implementation plan; release blocked pending ADR and reference-fixture acceptance |
| Date | 30 July 2026 |
| Governing specification | *CAP-001 Tier-N End-to-End Cost Model, Modelling Decisions and Dataset Generation Specification* v0.3 |
| Governing specification SHA-256 | `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` |
| Inherited standard | *Optimisation, Search and Decision Intelligence Capstone Control Standard* v0.2 |
| Inherited standard SHA-256 | `2741ebd6b1e01e4102c39c9f43de3a9f05b081aa61a3efd2838a431024a45637` |
| Precedence | CAP-001 v0.3 governs business, network, model, data, output and CAP-specific assessment semantics; approved ADRs and the shared decision configuration govern implementation detail; the common standard governs shared repository, submission and AI-native assessment controls |
| Controlled versions | Capstone/data/model configuration `0.3.0`; common rubric `0.2.0`; final student-release identifier to be assigned at release approval |
| Audience | Capstone owner, domain lead, data lead, optimisation lead, application lead, evaluation lead, technical reviewer and pilot facilitators |

### Implementation status

| Work package | Status | Evidence |
|---|---|---|
| WP1 — Decision configuration and schemas | Completed and accepted on 31 July 2026 | `docs/WP1_ACCEPTANCE_REPORT.md` |
| WP2 — Miniature recursive-cost fixture | Implementation complete; formal acceptance pending | `CAP-001_MINIATURE_FIXTURE_TOPOLOGY_CHANGE_NOTES.md`; `tooling/validate_fixture.py`; `tests/test_miniature_fixture.py` |

The no-release gate remains. ADR approval, outstanding CN-002 stakeholder
approvals, formal fixture acceptance, the full generator, reference models and
later acceptance evidence remain required before any student release.

## 1. What changed

This plan supersedes the earlier CAP-001 delivery plan based on the two-tier, fixed-price MILP assessment.

The principal changes are:

1. The assessed network is now a generic Tier-N directed acyclic graph instantiated as four supplier tiers plus four Asterion plants.
2. The assessed economic formulation is a bounded, non-convex recursive-cost model using weighted-average quantity-and-value pools by node, material and period.
3. The fixed-price MILP remains mandatory, but only as a diagnostic baseline using `baseline_standard_costs.csv`.
4. Students may use an exact, relaxed, approximate or heuristic solution route. They must classify the route honestly, preserve the required accounting semantics, reconcile the result and qualify any optimality claim.
5. Physical and financial reconciliation is now central to release acceptance and assessment. Every active pool, shipment, transformation, inventory balance and terminal service flow must reconcile.
6. The release must include a hand-worked miniature fixture, expected reconciliation outputs and negative variants before the full generator is accepted.
7. The data contract expands to 26 raw CSVs and a generic node, transformation, commercial-cost and scenario model.
8. The application contract expands to include recursive-cost lineage, a cost waterfall, solver-confidence evidence and stress-only versus re-optimised scenario results.
9. The assessment rubric has been updated to give greater weight to mathematical formulation, validation/reconciliation, method selection and the interactive application.
10. A 20–30 minute technical defence and a detailed AI-usage record are mandatory parts of the evidence model.

## 2. Purpose and release outcome

The purpose of this plan is to create, validate, pilot and release everything required for a junior consultant to engage meaningfully with CAP-001, while also creating the deterministic, AI-assisted and human-review controls needed to assess the work fairly.

CAP-001 is a controlled advanced capstone. The student is not expected to prove global optimality for every recursive run. The student is expected to:

- understand the end-to-end sourcing decision and nominated-source commercial context;
- build a correct generic Tier-N physical-flow model;
- implement or faithfully approximate the required recursive weighted-average cost policy;
- compare the recursive result with a fixed-price MILP baseline;
- validate physical quantities, values, ledger classification and terminal lineage;
- evaluate BASE and all supplied disruption scenarios;
- design at least one resilience intervention and explain the cost-service-inventory-resilience trade-off;
- communicate solver status and residual uncertainty honestly;
- deliver a usable decision-support application and client recommendation; and
- demonstrate ownership of AI-assisted work in a technical defence.

The evaluator must be able to:

- reproduce the declared baseline and assessed/default result without editing source;
- distinguish exact, relaxed, approximate and heuristic methods;
- validate feasibility and reconciliation independently of the student’s claims;
- compare outputs with controlled references or best-known bounds;
- collect evidence against every rubric category;
- apply deterministic quality gates before qualitative scoring;
- use AI to synthesise and score only from cited evidence;
- route contradictions, boundary cases and material uncertainty to a human; and
- produce an auditable assessment record.

## 3. Delivery principles

The implementation must follow these principles:

1. **One semantic source.** Approved ADRs must flow into one machine-readable decision configuration consumed or verified by the brief, schemas, dictionary, generator, models, validators and evaluator.
2. **Fixture before scale.** Pooling and recursive-value semantics must be proved on the miniature fixture before the large generator or student release is accepted.
3. **Physical feasibility before economics.** Generate a valid Tier-N physical network first, then add commercial costs and calibrate economic trade-offs.
4. **Two controlled model routes.** Maintain a fixed-price MILP baseline and at least one bounded recursive-cost reference route with the same physical, timing and commercial controls.
5. **Reconciliation before scoring.** Deterministic quantity, value, unit-cost, ledger and constraint checks run before AI-assisted qualitative assessment.
6. **Method neutrality with disclosure.** Do not create an undeclared grading advantage for licensed solvers. Reward correctness, evidence, honest classification and defensible results.
7. **Private/public separation.** Private seeds, generation code, reference results, bounds, hidden checks, adversarial fixtures, evaluator prompts and calibration submissions never enter the student release.
8. **Application-led evidence.** The application must explain decisions, lineage, trade-offs, solver confidence and failure states; it is not merely a visual wrapper.
9. **AI-native accountability.** AI use is expected, but the consultant owns every equation, test, result claim and recommendation.
10. **No release by prose alone.** A work package is complete only when its artefacts, tests and acceptance evidence pass from a clean environment.

## 4. Fixed scope and modelling baseline

### 4.1 Fixed business and planning scope

| Area | Controlled position |
|---|---|
| Organisation | Asterion Industrial Controls Group |
| Intended user | European supply-planning and category-management team operating nominated-source/open-cost arrangements |
| Plants | Birmingham, Dortmund, Katowice and Zaragoza |
| Reporting currency | EUR |
| Horizon | 12 weekly periods, 4 January–28 March 2027 |
| Network | Generic Tier-N DAG; release instance has four supplier tiers plus plants |
| Pooling | Weighted average by node, material and period |
| Timing | Same-period transformation; arrivals and production are available in the same week; no WIP |
| Horizon boundary | No post-P12 arrivals |
| External prices | Permitted only at external boundary sources |
| Intermediate prices | Tier 1–Tier 3 values are calculated recursively |
| Baseline | Fixed-price MILP using isolated `baseline_standard_costs.csv` |
| Assessed model | Bounded non-convex recursive-cost MINLP semantics |
| Objective | Lexicographic: weighted shortage; recursive served/closing value plus non-capitalised costs; surplus/unnecessary activation tie-break |
| Scenarios | BASE and SCN-01 through SCN-05 |
| Resilience | Student defines quantitative measures and implements at least one intervention |

### 4.2 Fixed cost-accounting policy

The assessed route must implement one controlled ledger.

Capitalised into pool or transformation value where configured:

- external purchase cost;
- freight, duty and insurance;
- attributable fixed order or shipment cost;
- conversion, setup, eligible overhead and surge cost; and
- supplier markup applied only to the configured eligible base.

Reported but not capitalised:

- holding cost;
- horizon-level relationship or activation cost; and
- shortage or service measures.

Each cost component must appear exactly once. Baseline standard costs are prohibited from the recursive calculation.

### 4.3 Required recursive accounting invariants

For every active node-material-period pool:

- pool quantity equals opening/previous inventory plus receipts plus production;
- pool value equals opening/previous inventory value plus receipt value plus production value;
- pool value equals weighted-average unit cost multiplied by pool quantity;
- all outflows from the same pool use the same unit cost;
- outflow quantity and value, terminal service and closing inventory reconcile;
- zero-quantity pools have zero value and controlled unit cost;
- production input value, configured value-add and output value reconcile;
- shipment dispatch value plus capitalised lane/receipt additions equals receipt value;
- closing inventory retains value at every node, not only at plants;
- artificial dilution, value disappearance and double counting are impossible or detected; and
- every terminal served-value result is traceable to external source and value-add contributions.

### 4.4 Student method freedom

Permitted approaches include:

- direct non-convex MINLP;
- spatial relaxation;
- piecewise-linear approximation;
- decomposition;
- iterative MILP;
- another algebraically equivalent formulation; or
- a clearly described heuristic.

The submission must label the formulation as `EXACT`, `RELAXED`, `APPROXIMATE` or `HEURISTIC`, describe any approximation, retain a feasible incumbent where possible, report bounds and gaps when available, and avoid unsupported global-optimality language.

### 4.5 Explicit release-1 exclusions

- open purchase orders and in-transit commitments;
- frozen near-term decisions and rolling-horizon replanning;
- WIP valuation or processing lags;
- finished-product demand forecasting and final-assembly scheduling;
- supplier onboarding, new approvals and contract negotiation;
- purchase-order execution, ERP write-back and real-time tracking;
- student-created assessed scenarios;
- optimised safety-stock policy;
- final-component substitution;
- carbon optimisation; and
- supplier markup bargaining.

## 5. Product architecture and separation controls

```text
capstone-control/                              # private
  config/                                      # approved decision configuration
  adrs/
  schemas/
  generator/
  fixtures/
  reference_models/
  validators/
  evaluator/
  calibration/
  release_builder/

CAP-001-tier-n-release/                        # student-facing
  brief/
  data/raw/
  data/miniature_fixture/
  reference/                                   # permitted guidance only
  schemas/
  starter/
  templates/
  release_manifest.json
  CHECKSUMS.sha256

submission/                                    # produced by student
  app/
  src/
  tests/
  config/
  outputs/
  reports/
  presentation/
  evidence/
  submission.yaml
```

The release builder must be allow-list based. It must fail on any private seed, generator implementation, main-case reference allocation, expected objective range, hidden test, adversarial fixture, evaluator prompt or calibration example.

## 6. Governance, roles and decision rights

| Role | Primary accountabilities |
|---|---|
| Capstone owner | Learning outcomes, scope, assessment policy, release approval and exception decisions |
| Domain lead | Business realism, terminology, nominated-source workflow, cost policy and scenario plausibility |
| Optimisation lead | Equations, bounds, solver routes, baseline, recursive reference, benchmark interpretation and permitted claims |
| Data lead | Shared configuration, schemas, generator, dictionary, lineage, checksums and release data |
| Application lead | Student user journey, required views, evidence capture, accessibility and failure states |
| Evaluation lead | Submission contract, deterministic gates, evidence collector, AI evaluator, calibration and reviewer guide |
| Technical reviewer | Independent verification of code, security separation, reproducibility, solver evidence and clean release |
| Pilot facilitators | Student observation, support issues, defence rehearsal and feedback synthesis |

Release approval requires sign-off from the capstone owner, domain lead, optimisation lead, evaluation lead and independent technical reviewer. No reference implementation or hidden test is self-approved.

## 7. Decisions that must be closed before release

The v0.3 direction is fixed, but these implementation choices remain controlled-open:

| Decision | Required evidence |
|---|---|
| Exact entity counts | Runtime profile and coverage of all scale/network requirements |
| Material and recipe catalogue | Unit, coefficient, yield and lineage validation |
| Fixed-cost allocation | Hand-worked examples and single-ledger tests |
| Holding and terminal policy | Objective and anti-dilution tests |
| Blendable versus exclusive recipes | Integer/formulation tests |
| Quantity/value/unit-cost bounds | Bound propagation report and adversarial checks |
| Epsilon and zero-pool treatment | Fixture and numerical-stability evidence |
| Reference solver and access route | Benchmark, licence/access record and reproducible settings |
| Main-case gap/runtime policy | Solver trials and fair fallback policy |
| Exact scenario coefficients | Scenario transformation tests and business review |
| Output precision and empty cases | Schema, rounding and reconciliation tests |
| Quality-gate consequences | Approved grading, resubmission and appeal policy |

ADRs must be completed in the prescribed order:

1. ADR-001 — narrative and scope;
2. ADR-002 — network and time;
3. ADR-003 — pooling and opening value;
4. ADR-004 — recursive value equations;
5. ADR-005 — cost classification;
6. ADR-006 — objective and anti-dilution;
7. ADR-007 — MOQ, setup and capacity;
8. ADR-008 — scenarios;
9. ADR-009 — generator and bounds;
10. ADR-010 — solver, runtime, access and fallback;
11. ADR-011 — outputs and tolerances; and
12. ADR-012 — approximation, assessment access and technical defence.

Each ADR must record context, decision, alternatives, mathematical/accounting consequences, data consequences, assessment consequences, affected artefacts, owner, reviewers and approval date.

## 8. Delivery sequence

The implementation follows ten specification work packages plus mobilisation and release. The dependency is:

```text
Mobilise and freeze ADR sequence
        |
        v
WP1 configuration and schemas
        |
        +------> WP2 miniature fixture ------> WP3 solver proof
        |                                      |
        +------> WP4 Tier-N graph generation --+
        |                                      |
        +------> WP5 commercial/cost generation
        |                                      |
        +------> WP6 planning/scenarios -------+
                                               |
                                               v
                                     WP7 reference models
                                               |
                                               v
                                  WP8 calibration/adversarial
                                               |
                         +---------------------+--------------------+
                         v                                          v
               WP9 student release                         WP10 evaluator
                         +---------------------+--------------------+
                                               v
                                      pilot and release gate
```

Large-instance generation must not outrun WP2 and WP3. The fixture and solver proof are deliberate feasibility gates for the capstone design itself.

## 9. Work-package plan

### Mobilisation — governance and semantic baseline

**Activities**

- Record governing-document hashes and precedence.
- Convert the approved v0.3 decisions into requirement identifiers.
- Name owners and independent reviewers.
- Approve the ADR template and decision sequence.
- Define student prerequisites, target effort and support boundaries.
- Freeze the repository, versioning, release and change-control conventions.
- Create the risk register and assessment-policy decision log.

**Outputs**

- requirements traceability matrix;
- ADR register and templates;
- responsibility matrix;
- change-control procedure;
- initial risk register; and
- approved mobilisation record.

**Exit condition**

Every mandatory requirement has an owner, planned artefact and verification route. No unresolved decision silently changes the controlled modelling direction.

### WP1 — Decision configuration and schemas

**Activities**

- Create the versioned YAML/JSON source of truth for business, network, time, pooling, cost, bounds, scenarios, tolerances, outputs and assessment flags.
- Define typed schemas for all 26 raw files, the miniature fixture, submission metadata and required outputs.
- Generate the human data dictionary and empty valid contract examples.
- Establish stable identifiers, foreign keys, units, currencies, effective periods and null rules.
- Define common status, run-mode and formulation-classification vocabularies.
- Scaffold private control, student release and submission repositories.

**Outputs**

- decision configuration `0.3.0`;
- ADR-001 through ADR-012 records;
- raw/output JSON schemas;
- generated data dictionary;
- empty valid fixture set;
- repository skeletons; and
- schema and configuration tests.

**Acceptance**

- configuration emits empty valid raw and output contracts;
- every frozen policy is represented;
- generated artefacts agree with the source configuration;
- unsupported fields or semantic drift fail validation; and
- the raw-data directory can be mounted read-only.

### WP2 — Miniature recursive-cost fixture

Amended by change note CN-002 (`CAP-001_MINIATURE_FIXTURE_TOPOLOGY_CHANGE_NOTES.md`): the fixture uses a richer four-layer, multi-sourced topology in place of the single-chain fixture originally described in v0.3 §12.8/Appendix E, in order to demonstrate weighted-average anti-dilution at more than one point in the network. This amendment is scoped to the fixture only; it does not change `network.release_instance_supplier_tiers`, `network.plant_count`, `target_scale`, or any recursive-cost accounting equation.

**Activities**

- Build the controlled five-period, four-layer miniature network: three Tier-4 external boundary sources, five Tier-3 nodes, two Tier-2 nodes and three Asterion plants, connected by fifteen approved arcs with genuine multi-sourcing at three separate hops (a three-way pool at Tier 3, a two-way pool at Tier 2, and a two-way pool at one plant). Tier 1 is not instantiated as a distinct layer; Tier-2 output ships directly to plants.
- Encode the hand calculation for external purchases, freight, fixed order cost, duty, opening inventory, weighted-average pooling, transformations, yield loss, setup, conversion, markup, receipts, service and closing inventory.
- Create expected output files at the same grain as the main assessment, including the value-conservation identity (total capitalised cost plus opening book value equals total served value plus total closing inventory value).
- Create negative variants for omitted cost, double count, wrong markup base, inconsistent outflow cost, value loss, artificial dilution, zero-pool error, infeasible flow and deliberate shortage.
- Document the accounting walk-through for students without exposing main-case reference results.

**Outputs**

- `data/miniature_fixture/inputs/`;
- `data/miniature_fixture/expected_reconciliation/`;
- hand-worked calculation (105 control totals);
- fixture validator (`tooling/validate_fixture.py`);
- negative fixtures; and
- regression tests.

**Acceptance**

The fixture reproduces, within configured tolerances, the full 105-row control-totals set (`fixture_control_totals.csv`); the fifteen headline figures are:

| Control total | Expected |
|---|---:|
| Tier-3 pool quantity (3-way fan-in) | 150.0000000 units |
| Tier-3 pool value | EUR 402.0000000 |
| Tier-3 weighted-average unit cost | EUR 2.6800000/unit |
| Tier-3 transformation output value (yield 0.80) | EUR 540.0000000 |
| Tier-3 closing inventory value (capacity-stranded) | EUR 33.8000000 |
| Tier-2 pool unit cost (2-way fan-in) | EUR 5.1714286/unit |
| Tier-2 transformation output value (node A) | EUR 1122.0000000 |
| Tier-2 transformation output value (node B) | EUR 731.5000000 |
| Tier-2 closing inventory value (BOM-stranded) | EUR 32.0000000 |
| Plant pool unit cost — opening stock + single receipt | EUR 20.1000000/unit |
| Plant pool unit cost — dual-sourced fan-in | EUR 20.6750000/unit |
| Plant pool unit cost — single-sourced | EUR 22.1000000/unit |
| Total served value, three plants, two demand periods | EUR 2073.0000000 |
| Total terminal-period closing inventory value | EUR 166.3000000 |
| **Stage-2 value before non-capitalised cost** | **EUR 2239.3000000** |

The value-conservation identity (total capitalised cost EUR 1945.30 plus opening book value EUR 294.00 equals total served value EUR 2073.00 plus terminal closing value EUR 166.30, both sides EUR 2239.30 exactly) is checked first, before any finer-grained total. All negative variants must fail for the intended reason.

### WP3 — Solver proof of concept

**Activities**

- Implement the fixture-scale fixed-price MILP.
- Implement at least one bounded recursive-cost adapter.
- Exercise exact/local, relaxed or approximate routes as needed to validate solver integration.
- Capture standardized termination, objective stages, incumbent, bounds, gaps, starts, runtime, hardware, residuals and logs.
- Benchmark supported and fallback solver routes.
- Decide how stored results and asynchronous execution will be handled in the application.

**Outputs**

- solver-neutral modelling adapter;
- fixture MILP and recursive models;
- solver configuration;
- benchmark report;
- run-metadata writer;
- solver-log capture; and
- ADR-010/ADR-012 evidence.

**Acceptance**

- both fixture models solve and reconcile;
- the recursive route is demonstrably bounded;
- unsupported global claims are not emitted;
- the accessible baseline/fallback route is documented; and
- the miniature fixture completes within two minutes on the reference environment.

### WP4 — Tier-N graph generation

**Activities**

- Generate organisations, generic nodes, plants, materials, recipes, transformation inputs and material-flow approvals.
- Enforce a connected acyclic graph with four supplier tiers plus plants.
- Add controlled multi-sourcing, multi-tier organisations, alternate routes and hidden shared dependencies.
- Generate blendable and exclusive recipe groups according to approved ADRs.
- Maintain stable lineage from terminal material to external boundary sources.
- Validate units, coefficients, yields, effective periods and approved paths.

**Outputs**

- graph-generation modules;
- organisation/node/material/recipe/approval datasets;
- graph and lineage validators;
- network summary; and
- deterministic generation tests.

**Acceptance**

- graph is connected and acyclic;
- no hard-coded tier-specific model families are required;
- every assessed terminal material has at least two broad feasible sourcing combinations;
- all recipes and approvals are dimensionally valid; and
- concentration and hidden-dependency structures are intentional and measurable.

### WP5 — Commercial and cost generation

**Activities**

- Generate supply contracts, Incoterm abstractions, duty, lanes, external prices, conversion costs, cost-allocation rules, FX and baseline standard costs.
- Restrict external unit prices to boundary sources.
- Classify every component as capitalised or non-capitalised, assign its stage and markup eligibility, and map it to a unique ledger class.
- Generate finite theoretical quantity, value and unit-cost envelopes.
- Calibrate fixed versus variable costs, freight alternatives, MOQ/order multiples, setup, surge, overhead and markup.
- Prove that baseline standard costs cannot enter the recursive route.

**Outputs**

- commercial and cost-generation modules;
- `COST_POLICY.md`;
- cost ledger dictionary;
- bounds report;
- anti-double-count controls; and
- cost plausibility report.

**Acceptance**

- every cost is classified exactly once;
- all theoretical envelopes are finite and safely bounded;
- receipt and transformation allocation rules reproduce hand-worked tests;
- external/internal pricing boundaries are enforced; and
- baseline and recursive models can differ for explainable economic reasons.

### WP6 — Planning facts and disruption scenarios

**Activities**

- Generate source and transformation capacity, inventory policy, opening quantity/book value, terminal demand, supplier history and incident history.
- Generate BASE plus SCN-01 through SCN-05 as deterministic impact data.
- Implement immutable scenario views supporting node, organisation, parent, region, lane, recipe, material, external-price, conversion-cost and terminal-demand targets.
- Implement explicit recovery rows and deterministic overlap rules.
- Distinguish `STRESS_ONLY` evaluation from `REOPTIMISE`.
- Construct BASE physical feasibility before economic tuning.

**Outputs**

- planning-fact and scenario generators;
- `SCENARIO_CATALOGUE.md`;
- scenario transformation engine;
- scenario fixtures;
- feasibility-construction report; and
- physical/scenario validation suite.

**Acceptance**

- BASE is physically feasible and designed for zero shortage;
- scenario views do not mutate BASE;
- exact target/period/multiplier/recovery tests pass;
- severe scenarios expose meaningful recourse or explainable shortage;
- demand, inventory and capacity remain dimensionally coherent; and
- repeated generation is deterministic.

### WP7 — Full reference models and standard outputs

**Activities**

- Implement the full fixed-price MILP using the same physical, commercial and timing controls.
- Implement the full bounded recursive-cost reference route.
- Solve BASE and all scenarios within controlled budgets, retaining incumbents and logs.
- Emit all standard output files from both routes.
- Recompute physical and financial results independently from decision-variable exports.
- Produce baseline-versus-recursive explanations and best-known reference evidence.

**Outputs**

- fixed-price MILP;
- recursive-cost reference model;
- post-solve reconciliation engine;
- standard output writers;
- BASE/scenario reference results;
- private bounds/objective ranges; and
- solver benchmark logs.

**Acceptance**

- BASE reaches zero shortage;
- all active pools, shipments, transformations, inventory and service reconcile;
- the two formulations produce meaningful and explainable differences;
- result classification matches solver evidence;
- no baseline-standard-cost leakage occurs; and
- reference results are repeatable within the declared policy.

### WP8 — Calibration and adversarial validation

**Activities**

- Profile exact entity counts within approved ranges.
- Calibrate scarcity, commercial trade-offs, resilience exposure and scenario severity.
- Run multiple starts and bound/gap experiments.
- Tune numeric scaling, epsilon and bounds without weakening semantics.
- Test dilution, value disappearance, double counting, wrong markup, prohibited baseline leakage, invalid paths, post-horizon arrival, scenario leakage and unsupported optimality claims.
- Create strong, weak and deliberately defective private sample submissions.

**Outputs**

- calibration report;
- runtime/hardware profile;
- plausibility bands;
- adversarial test suite;
- reference result ledger;
- quality-gate thresholds; and
- approved final generation configuration.

**Acceptance**

- reference results are stable enough for assessment;
- negative tests fail correctly;
- alternative supported methods can earn marks fairly;
- thresholds distinguish rounding noise from material error;
- no hidden requirement is needed to pass; and
- all controlled-open modelling decisions are closed by ADR.

### WP9 — Student release and application contract

**Activities**

- Produce the controlled brief, narrative, learning path, glossary and model-accounting guide.
- Package the 26 raw files, miniature fixture, dictionaries, schemas, cost policy and scenario catalogue.
- Provide a starter repository, manifest, commands, output schemas and report templates.
- Document accessible baseline and recursive solver routes, runtime budgets, stored-result policy and permitted status language.
- Provide application requirements, evidence-capture guidance, AI-usage template and technical-defence guidance.
- Build the allow-list release and private-content scanner.
- Run a clean-room student journey.

**Outputs**

- versioned student release;
- release manifest and checksums;
- starter repository;
- `solver_report_template`;
- `AI_USAGE_TEMPLATE.md`;
- model/reconciliation report templates;
- application evidence guide;
- technical-defence guide; and
- learner FAQ.

**Acceptance**

- a fresh user can install, test, run the baseline, run or retrieve an assessed result and launch the app;
- all release files match manifest hashes and row counts;
- every student-facing requirement maps to a rubric or quality gate;
- no private artefact leaks;
- the fixture can be reproduced from the released guidance; and
- no student needs a licensed solver to demonstrate assessable competence.

### WP10 — Evaluation harness

**Activities**

- Validate `submission.yaml`, required paths, commands, dependencies and release versions.
- Run install, tests, baseline, assessed/default result and application probes in isolation.
- Recompute constraints, balances, recursive-value equations, ledger classification, terminal lineage and scenario transformations.
- Compare reported metrics with raw outputs and controlled references.
- Build a cited evidence bundle for the rubric.
- Run AI-assisted scoring only after deterministic checks.
- Implement contradiction, unsupported-claim and boundary-review triggers.
- Produce the technical-defence question pack and post-defence adjustment record.
- Calibrate against strong, weak and defective submissions.

**Outputs**

- submission runner;
- deterministic quality-gate engine;
- evidence collector;
- CAP-001 rubric addendum;
- versioned AI evaluator prompt and structured output;
- reviewer guide;
- defence guide;
- calibration report; and
- auditable assessment report.

**Acceptance**

- sample submissions score reproducibly;
- AI evidence citations resolve to actual files, rows, model components, app views or slides;
- failed gates constrain scoring according to approved policy;
- close-to-boundary and contradictory cases route to a human;
- the same evidence does not receive materially different scores without an explainable reason; and
- no AI score can override a deterministic physical or financial failure silently.

### Pilot and release

**Activities**

- Run at least one clean-room build and two pilot student journeys.
- Observe setup, modelling, reconciliation, application and defence failure points.
- Re-run calibration after pilot fixes.
- Freeze capstone, data, model, rubric and evaluator versions.
- Sign manifests, hashes, benchmark environment and release approval.
- Archive the private reference and evaluation evidence.

**No-release gate**

No student release may be issued until the miniature fixture, generator, schemas, fixed-price MILP, recursive-cost reference route and every physical, financial, scenario, security and clean-environment acceptance check pass.

## 10. Student learning and support pack

The student release must contain enough support to make the challenge difficult for the right reasons.

| Artefact | Purpose |
|---|---|
| `CAPSTONE_BRIEF.md` | Controlled task, user, decision, scope, deliverables and evidence |
| `TASK_REQUIREMENTS.md` | Normative student obligations, quality gates and required outputs |
| `BUSINESS_CONTEXT.md` | Asterion workflow, nominated-source authority and decision cadence |
| `LEARNING_PATH.md` | Recommended order: data audit, fixture, baseline, recursive method, validation, scenarios, resilience, app |
| `GLOSSARY.md` | Pooling, value flow, transformations, tiers, formulations, solver status and commercial terms |
| `AI_NATIVE_WORKING_GUIDE.md` | Expected uses of AI, validation duties and evidence examples |
| `DATA_DICTIONARY.md` | Generated field-level definitions, units, domains, keys and relationships |
| machine-readable schemas | Early structural validation of all inputs and outputs |
| `config/default_case.yaml` | Fixed scenario, horizon, method defaults, seeds and runtime budgets |
| `COST_POLICY.md` | Capitalisation, non-capitalised items, markup base and single-ledger rules |
| `SCENARIO_CATALOGUE.md` | BASE/SCN-01–05 definitions, stress-only and re-optimisation semantics |
| miniature fixture | Hand-worked recursive accounting and expected reconciliation |
| `MODEL_REQUIREMENTS.md` | Required physical/economic semantics without releasing the main solution |
| `SOLVER_AND_STATUS_GUIDE.md` | Supported routes, budgets, method classification and permitted claims |
| starter repository | Manifest, config, tests, commands and output paths |
| report templates | Model, solver, validation, recommendation and production-readiness evidence |
| `AI_USAGE_TEMPLATE.md` | Material AI assistance, validation, changes, rejections and accountability |
| application evidence guide | Required views, interactions, exports, failures and screenshots |
| technical-defence guide | Expected 20–30 minute format and evidence to retain |
| `PRODUCTION_EXTENSION.md` | Required production architecture, integration, monitoring and fallback topics |
| learner FAQ | Operational clarification without exposing private results |

The learning path should require students to pass the miniature fixture before attempting the full recursive model.

## 11. Student submission contract

The submission must provide one declared command for each of:

1. installing dependencies;
2. running automated tests;
3. solving the default fixed-price MILP baseline;
4. solving the assessed default model or producing a documented time-limited incumbent;
5. launching the application; and
6. optionally regenerating standard reports from stored controlled outputs.

A reference layout is:

```text
submission/
  submission.yaml
  README.md
  AI_USAGE.md
  app/
  src/
    data/
    models/
    solvers/
    validation/
    reporting/
  config/
  tests/
  scripts/
    setup.sh
    run_baseline.sh
    run_model.sh
    run_app.sh
    run_tests.sh
  artifacts/
    evaluation/
      run_metadata.json
      metrics.json
      constraint_report.csv
      reconciliation_summary.json
      baseline_comparison.csv
      scenario_results.csv
    solution/
      baseline/
      recursive/
      scenarios/
    solver_logs/
    application_evidence/
  reports/
    model_specification.md
    solver_strategy.md
    validation_report.md
    resilience_recommendation.md
    assumptions_and_limitations.md
    production_readiness.md
  presentation/
    final_readout.pptx
    final_readout.pdf
  evidence/
  pyproject.toml, package-lock.json, or equivalent lockfile
```

The evaluator must mount authoritative input data read-only and must not edit student code or configuration to make it run.

## 12. Required result and evidence outputs

Every assessed run must emit:

| Output | Required grain or content |
|---|---|
| `run_metadata.json` | Version, scenario, run mode, formulation class, solver, status, objective stages, incumbent, bound/gap, starts, runtime, hardware and commit |
| `metrics.json` | Service, terminal value, incremental spend, closing inventory, non-capitalised cost, violations, residuals and resilience metrics |
| `orders.csv` | Contract-material-dispatch period |
| `shipments.csv` | Arc/lane-material-dispatch and arrival period |
| `production.csv` | Node-recipe-period |
| `inventory_cost_rollforward.csv` | Node-material-period quantity, value, unit cost, outflows and closing balance |
| `demand_service.csv` | Plant-terminal-material-period |
| `cost_component_ledger.csv` | Cost component-entity-period with capitalisation, stage, markup and unique ledger class |
| `cost_lineage.csv` | Terminal demand to external-source/value-add contribution |
| `recursive_cost_reconciliation.csv` | Equation-level LHS, RHS, residual, tolerance and pass flag |
| `constraint_report.csv` | Constraint-family/entity-period LHS, sense, RHS, slack and violation |
| `reconciliation_summary.json` | Run-level quantity, value, unit-cost, integrality and bound residual summary |
| `baseline_comparison.csv` | Method-scenario service, cost, inventory, resilience, status, runtime and caveats |
| `scenario_comparison.csv` | Plan-scenario-run-mode business, solver and resilience metrics |
| `scenario_results.csv` | Common evaluation summary at method-scenario grain, derived consistently from scenario comparison |

Default acceptance tolerances are:

- quantity: `max(1e-5 units, 1e-7 × relevant scale)`;
- value: `max(EUR 1e-3, 1e-7 × relevant value scale)`;
- unit cost: `max(EUR 1e-5/unit, 1e-7 × relevant cost scale)`;
- integrality: `1e-6`; and
- bounds: the same absolute/relative convention as the relevant quantity or value.

Any change requires ADR approval and regeneration of fixture, reference and evaluator evidence.

## 13. Application contract

The application may solve live, submit asynchronous jobs or retrieve controlled results. It must always show result age, configuration/version, scenario, job state, method classification and solver status.

Minimum views are:

1. executive overview;
2. Tier-N network explorer;
3. input and cost-policy explorer;
4. fixed-price baseline;
5. recursive-cost result;
6. recursive cost waterfall and terminal lineage;
7. baseline comparison;
8. scenario analysis with stress-only/re-optimised distinction;
9. resilience design and intervention trade-off;
10. solver and validation evidence; and
11. decision summary.

The app must expose failure states, stale/precomputed result status, violated checks and uncertainty. It must never relabel a local, approximate or time-limited result as globally optimal.

## 14. Solver fairness and runtime policy

Provisional calibration targets are:

| Run | Budget |
|---|---|
| Miniature fixture | Complete and reconcile within 2 minutes |
| Fixed-price MILP BASE or scenario | Complete within 5 minutes per run |
| Recursive BASE | Up to three starts; 20 minutes per start; retain incumbent |
| Recursive scenario re-optimisation | One warm-started run up to 15 minutes per scenario, unless calibration freezes another budget |
| Application | Stored controlled results permitted; asynchronous jobs must expose state and version |

The release must provide at least one equally accessible route. Commercial solver access may improve a result, but it cannot be a hidden prerequisite for a passing submission. Grading must distinguish formulation and validation quality from raw solver performance.

The standard result statuses are:

- `globally_optimal`;
- `locally_optimal`;
- `feasible_time_limited`;
- `best_found`;
- `infeasible`; and
- `solver_failed`.

## 15. Assessment design

### 15.1 Rubric

| Category | Points | CAP-001 evidence |
|---|---:|---|
| Business framing and user value | 8 | Nominated-source workflow, intended user, decision cadence and recommendation |
| Data understanding and preparation | 8 | Tier-N joins, units, effective dates, scenarios, cost mapping and data quality |
| Mathematical formulation | 16 | Physical flows, integer logic, weighted-average pooling, recursive value, objective and bounds |
| Method selection and implementation | 14 | Baseline and recursive/relaxed/approximate strategy with justified controls |
| Validation, benchmarking and robustness | 15 | Fixture, baseline, reconciliation, adversarial tests, scenarios, sensitivity and multi-start evidence |
| Interactive application | 14 | Network, allocation, lineage, scenarios, resilience, solver and failure views |
| Software engineering and reproducibility | 10 | Modular code, baseline isolation, tests, configuration, logging and commands |
| Presentation and recommendation | 7 | Client narrative, trade-offs, evidence, caveats and permitted claims |
| Production readiness and limitations | 5 | Integration, data ownership, security, scale, async solving, monitoring and fallback |
| Technical defence | 3 | Ownership of AI-assisted formulation, validation and interpretation |
| **Total** | **100** | |

### 15.2 Assessment stages

1. **Submission and environment checks** — manifest, versions, hashes, required files, installation, commands and application launch.
2. **Deterministic model checks** — schemas, physical feasibility, quantity/value reconciliation, ledger uniqueness, baseline isolation, scenario transformations and metric recomputation.
3. **AI-assisted evidence scoring** — qualitative rubric scoring from an evidence bundle with citations and confidence.
4. **Human review and technical defence** — mandatory defence plus review of contradictions, gate failures, low-confidence scoring and grade-boundary cases.

### 15.3 Quality gates

The assessment policy must define the score consequence of each gate before release. At minimum, the following are gates:

- application launches and its controlled result evidence is retrievable;
- release and input versions/checksums match;
- fixed-price baseline is present;
- assessed result or documented incumbent is present;
- declared commands run;
- all mandatory physical constraints pass;
- active pools and transformations reconcile in quantity and value;
- ledger entries are unique and cost components are counted once;
- zero-pool, common-outflow-cost and anti-dilution checks pass;
- baseline standard costs do not leak into recursive results;
- required BASE and scenario evidence exists;
- results reproduce within declared tolerances or the variance is explained;
- solver classification and optimality language match the evidence;
- charts, tables and machine outputs agree; and
- the consultant can defend material AI-assisted work.

### 15.4 AI evaluation controls

The AI evaluator must:

- receive deterministic results before reports or code are scored;
- cite exact evidence paths and, where practical, rows, model components, views or slides;
- distinguish absent evidence from poor evidence;
- flag contradictions rather than resolving them in the student’s favour;
- produce criterion scores, rationales, evidence citations, confidence and review flags in structured form;
- never infer global optimality from a low residual alone;
- never override a failed hard constraint or reconciliation check silently; and
- route submissions within three points of pass, distinction or top-grade boundaries to a human reviewer, together with any other configured triggers.

### 15.5 Technical defence

The 20–30 minute defence must sample:

- one Tier-N physical balance;
- one weighted-average pool and value roll-forward;
- one cost-capitalisation or markup decision;
- the baseline-versus-recursive difference;
- method classification, bound/gap and runtime interpretation;
- one failed or adversarial test;
- one scenario and resilience trade-off; and
- one material AI contribution that the student corrected, rejected or independently validated.

## 16. Verification strategy

Testing must include:

- schema and contract tests;
- dimensional and graph tests;
- deterministic regeneration and checksum tests;
- miniature hand-calculation regression tests;
- physical balance tests;
- recursive value and common-unit-cost tests;
- single-ledger and anti-double-count tests;
- bound and zero-pool tests;
- baseline-isolation tests;
- scenario target, overlap, recovery and immutability tests;
- solver status/bound/gap interpretation tests;
- standard-output and metric recomputation tests;
- app launch, navigation, stale-result and failure-state tests;
- release privacy scans;
- clean-environment end-to-end tests; and
- evaluator calibration and repeatability tests.

The clean-environment acceptance run must execute the same public commands supplied to students.

## 17. Indicative delivery calendar

The dates should be set after owner availability is known. The dependency-based sequence below is the planning baseline.

| Stage | Indicative duration | Exit |
|---|---:|---|
| Mobilisation and ADR framing | 1 week | Requirements, owners and ADR register approved |
| WP1 configuration and contracts | 1–2 weeks | Empty raw/output contracts validate |
| WP2 miniature fixture | 1 week | Hand totals and negative variants pass |
| WP3 solver proof | 1–2 weeks | Bounded fixture routes solve and reconcile |
| WP4–WP6 generator streams | 2–3 weeks | Physically feasible deterministic instance and scenarios |
| WP7 full references | 2–3 weeks | Baseline and recursive outputs reconcile |
| WP8 calibration/adversarial | 2 weeks | Bounds, runtime, difficulty and negative tests accepted |
| WP9 student release | 1–2 weeks | Clean-room learner journey passes |
| WP10 evaluator | 2 weeks, overlapping WP9 | Calibration submissions score reproducibly |
| Pilot and release | 1–2 weeks | No-release gate and sign-offs pass |

WP4–WP6 can run in parallel only after WP1 contracts are stable and WP2/WP3 have established viable recursive semantics.

## 18. First implementation sprint

### Sprint objective

Prove the capstone’s semantic and computational core before investing in the large generator.

### Sprint backlog

1. Approve the requirement baseline and document precedence.
2. Create ADR-001 through ADR-012 shells and assign owners.
3. Implement the first decision-configuration schema.
4. Define common node, material, recipe, approval, contract and cost-rule identifiers.
5. Create raw and output schema skeletons.
6. Build the miniature fixture inputs and expected outputs.
7. Encode the published control totals as regression tests.
8. Implement independent quantity/value reconciliation for the fixture.
9. Implement fixture-scale fixed-price MILP and one bounded recursive route.
10. Capture solver metadata, logs, bounds/gaps and standard status.
11. Create at least four negative accounting variants.
12. Review solver access and approve the next-step feasibility decision.

### Sprint exit

- the fixture solves and reconciles within two minutes;
- hand totals match within default tolerances;
- each negative case fails for the expected reason;
- the recursive route is bounded;
- baseline and recursive standard costs are isolated;
- configuration, model and reconciler agree on semantics; and
- the optimisation, data and evaluation leads approve progression to large-instance generation.

## 19. Principal risks and controls

| Risk | Control |
|---|---|
| Recursive MINLP is too difficult for the intended cohort | Fixture-first learning path, permitted approximations, reference solver route, time-limited incumbent acceptance and formulation-focused grading |
| Solver access creates unfairness | Accessible MILP/fallback route, declared budgets, method-neutral rubric and explicit access metadata |
| Weak bounds make the model unstable | Propagated envelopes, bound report, miniature tests and adversarial stress |
| Costs are double-counted or disappear | Unique ledger, stage/markup classification, roll-forward outputs and independent reconciliation |
| Weighted-average pooling permits dilution | Closing inventory value in Stage 2, anti-dilution tests, zero-pool controls and tie-break objective |
| Dataset is physically infeasible | Construct feasibility before economics and prove BASE with reference models |
| Baseline contaminates recursive results | Separate ingestion/model modules and hidden leakage tests |
| Scenario results are confused with re-optimisation | Explicit run mode in metadata, outputs and app |
| Students overclaim optimality | Controlled status vocabulary, bound/gap checks, app language checks and defence questions |
| App hides stale or failed results | Mandatory result age, version, state, method and failure views |
| AI-generated code is not understood | AI usage evidence, targeted defence, cited tests and ownership scoring |
| Private references leak | Allow-list builder, token/signature scan and independent release review |
| AI evaluation becomes inconsistent | Deterministic evidence first, structured scoring, calibration and boundary human review |

## 20. Definition of done

CAP-001 is ready for controlled student release only when:

1. all 12 ADRs and assessment-policy decisions are approved;
2. the shared configuration drives or verifies every derived artefact;
3. all 26 raw-data contracts and all standard outputs validate;
4. the miniature fixture and negative variants pass from a clean environment;
5. fixed-price and recursive reference routes are bounded, reproducible and reconciled;
6. BASE is feasible with zero shortage and all scenarios behave as intended;
7. the full physical, value, ledger, lineage and anti-gaming suite passes;
8. solver access, budgets, fallback and permitted status language are documented;
9. the student pack contains the full learning, data, modelling, application, AI and defence support set;
10. the private/public separation scan passes;
11. the evaluator correctly handles strong, weak and defective calibration submissions;
12. AI scores are evidence-cited and human-review triggers operate;
13. at least two pilot journeys complete without an undisclosed requirement;
14. the release manifest, hashes, row counts, commands and output contracts agree; and
15. the capstone owner, domain lead, optimisation lead, evaluation lead and technical reviewer sign the release.
