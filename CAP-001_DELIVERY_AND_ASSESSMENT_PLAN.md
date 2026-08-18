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
| WP3 — Model-viability proof | Frozen at sufficient author-side evidence on 18 August 2026; not a model-solution deliverable | `docs/WP3_IMPLEMENTATION_STATUS.md`; retained private smoke tests |

The no-release gate remains. ADR approval, outstanding CN-002 stakeholder
approvals, formal fixture acceptance, the full generated dataset, calibration
and later acceptance evidence remain required before any student release.

## 1. What changed

This plan supersedes the earlier CAP-001 delivery plan based on the two-tier, fixed-price MILP assessment.

The principal changes are:

1. The assessed network is now a generic Tier-N directed acyclic graph instantiated as four supplier tiers plus four Asterion plants.
2. The assessed economic formulation is a bounded, non-convex recursive-cost model using weighted-average quantity-and-value pools by node, material and period.
3. The fixed-price MILP remains mandatory, but only as a diagnostic baseline using `baseline_standard_costs.csv`.
4. Every accepted solution route must be grounded in an explicit algebraic MILP or MINLP formulation. Exact, relaxed, approximate or heuristic solution strategies remain permissible around those formulations, but must be classified honestly, preserve the required accounting semantics, reconcile the result and qualify any optimality claim.
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
4. **Two controlled formulation requirements.** Require candidates to construct an explicit fixed-price MILP baseline and an explicit bounded recursive-cost MINLP with the same physical, timing and commercial controls; private author code is needed only for viability checks.
5. **Reconciliation before scoring.** Deterministic quantity, value, unit-cost, ledger and constraint checks run before AI-assisted qualitative assessment.
6. **Toolchain neutrality with disclosure.** Require the controlled MILP/MINLP semantics without mandating one modelling package. Do not create an undeclared grading advantage for a particular library or licensed solver; reward correctness, evidence, honest classification and defensible results.
7. **Private/public separation.** Private seeds, generation code, calibration evidence, bounds, hidden checks, adversarial fixtures, evaluator prompts and pilot submissions never enter the student release.
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

Every submission must construct an explicit algebraic MILP or MINLP. A
simulation, reconciliation script, procedural valuation engine or unconstrained
search routine cannot substitute for the optimisation formulation.

The private authoring harness uses Pyomo, but the assessment imposes no
reference modelling library. Pyomo, PuLP or another algebraic modelling
library is acceptable when it can express the declared formulation, variable
domains, constraints and staged objectives without changing the controlled
semantics. Library choice and any material translation limitations must be
disclosed.

Permitted solution strategies around the declared formulation include:

- direct non-convex MINLP;
- an algebraically equivalent MILP reformulation;
- spatial or other documented relaxation of the MINLP;
- piecewise-linear MILP approximation;
- decomposition or iterative MILP/NLP solution;
- another algebraically equivalent MILP or MINLP; or
- a clearly described heuristic that generates or selects candidates whose
  feasibility and objective are evaluated against the declared MILP/MINLP.

HiGHS is the reference MILP solver. IPOPT is a supported solver for continuous
nonlinear subproblems or relaxations. IPOPT alone does not discharge integer
feasibility: a recursive MINLP route that uses it must also show how discrete
decisions are enforced, for example through a disclosed decomposition or
integer-enumeration controller. Alternative compatible solvers may be proposed
through ADR-010; they are not an alternative to the formulation requirement.

The submission must label the solution route as `EXACT`, `RELAXED`,
`APPROXIMATE` or `HEURISTIC`, describe any approximation, retain a feasible
incumbent where possible, report bounds and gaps when available, and avoid
unsupported global-optimality language. That classification describes how the
MILP/MINLP was solved; it does not permit a formulation-free methodology.

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
        +------> WP2 miniature fixture ------> WP3 model viability
        |                                      |
        +------> WP4 Tier-N graph generation --+
        |                                      |
        +------> WP5 commercial/cost generation
        |                                      |
        +------> WP6 planning/scenarios -------+
                                               |
                                               v
                                 WP7 dataset viability
                                               |
                                               v
                           WP8 consultant engagement design
                                               |
                         +---------------------+--------------------+
                         v                                          v
        WP9 release and app contract                  WP10 evaluation controls
                         +---------------------+--------------------+
                                               v
                                      pilot and release gate
```

Large-instance generation must not outrun WP2 and WP3. The fixture and frozen
model-viability proof are deliberate feasibility gates for the capstone design
itself.

### Progress-reporting lens

Subsequent progress is reported against three design outcomes:

1. **Dataset quality** — whether the generated case is structurally deep,
   commercially plausible, temporally meaningful and rich in genuine choices.
2. **Consultant engagement quality** — whether the business ask requires a
   well-reasoned explicit MILP or MINLP, validation, scenario judgement and a
   defensible recommendation while allowing legitimate method choice.
3. **Submission and assessment quality** — whether the required full-stack
   application explains decisions and uncertainty, and whether assessors can
   validate and score the evidence without matching one author solution.

Lines of model code, solver features and reference-output coverage are not
progress measures. Private implementation is reported only when it resolves a
specific uncertainty about dataset viability, fairness or assessability.

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
- Document the accounting walk-through for students without exposing private
  calibration outputs.

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

### WP3 — Frozen model-viability proof

**Purpose**

WP3 is an author-side confidence check, not the production of an exemplar
submission. Its purpose is limited to showing that the controlled contracts and
miniature fixture can support a coherent, non-trivial optimisation exercise.
The student brief, assessment standard and generated dataset remain the
deliverables; the private reference code has no normative authority.

**Frozen decision — 18 August 2026**

WP3 is frozen at the evidence currently implemented. No further fixture output
pipeline, solver abstraction, proof-case matrix, benchmark harness or reference
application is required. Formal release acceptance remains subject to the
governing WP1/WP2 controls and later generated-dataset checks; freezing WP3 does
not waive those controls.

The existing private implementation is retained because it provides a useful
oracle for dataset generation and calibration:

- it reads the 26 raw contracts independently of the hand-worked reconciler;
- it instantiates a shared physical formulation and fixed-price MILP;
- it instantiates the bounded recursive-cost equations and checks their
  accounting;
- it solves the miniature fixture through licence-accessible HiGHS/IPOPT routes;
  and
- it validates extracted quantities and values independently of live model
  expressions.

It is not student starter code, a required modelling architecture, a preferred
submission, or a promise to produce a polished reference solution. Pyomo is
used only by the private authoring harness. Students may use PuLP or another
suitable algebraic modelling library where it can express their chosen explicit
MILP or MINLP formulation.

**Frozen evidence boundary**

| Question | Evidence | Position |
|---|---|---|
| Can the raw contracts construct an optimisation model without importing solved fixture values? | Independent loader and explicit algebraic model construction | Demonstrated |
| Are the physical flow, timing, capacity, lot, transformation, inventory and service rules jointly feasible? | Shared physical formulation, canonical solve and independent balance checks | Demonstrated |
| Are the recursive weighted-average cost semantics internally coherent? | Bounded recursive formulation, EUR 2,239.30 conservation identity and 105 control totals | Demonstrated |
| Does the specification permit meaningful optimisation behaviour rather than only arithmetic reproduction? | Small sourcing, shortage, infeasibility and bound probes | Demonstrated at fixture scale |
| Is at least one accessible implementation route available for author calibration? | HiGHS MILP and honestly classified HiGHS/IPOPT recursive routes | Demonstrated in the authoring environment |

These checks establish semantic viability only. They do not establish that the
future 12-period generated dataset is sufficiently deep, well calibrated or
computationally representative. Those questions belong to WP4–WP6 and the
later whole-dataset calibration run.

**Retained private artefacts**

- the `cap001_model` authoring and calibration package;
- focused regression tests for the frozen evidence above; and
- the small private proof-case manifests already implemented.

The solution-bundle and solver-adapter code may remain because it is tested and
can help diagnose future generator changes, but it is optional infrastructure.
It must not drive additional WP3 scope.

**No longer required from WP3**

- complete schema-valid fixture result exports;
- exhaustive time-limit, fallback and status probes;
- all originally proposed `SP-01` through `SP-08` cases;
- production-grade logs, checksums, benchmarks or solver-neutral execution;
- a full-scale reference optimiser; or
- any reference full-stack application.

The required-output schemas continue to define what a consultant submission
must communicate. They do not oblige the capstone author to manufacture a
complete reference output bundle at fixture scale.

**Reopen criteria**

WP3 is reopened only if a controlled contract or accounting policy changes, the
full generator exposes a feasibility or valuation defect, the calibrated
dataset fails to create meaningful decisions, or the retained smoke test can no
longer run in the authoring environment. Otherwise work proceeds to generation,
calibration and assessment design.

### WP4 — Network structure and dependency depth

**Design question**

Does the generated network create a credible multi-tier supply-chain problem
with material path choice, concentration and dependency exposure?

**Activities**

- Generate organisations, generic nodes, plants, materials, recipes,
  transformation inputs and material-flow approvals.
- Enforce a connected acyclic graph with four supplier tiers plus plants.
- Create controlled multi-sourcing, multi-tier organisations, alternate routes,
  shared parents and hidden common dependencies.
- Create blendable and exclusive recipe groups where they generate a genuine
  planning choice.
- Maintain stable lineage from terminal demand to external boundary sources.
- Profile depth, fan-in, fan-out, path diversity, concentration and dependency
  overlap rather than relying on entity counts alone.

**Outputs**

- deterministic graph generator and generated structural datasets;
- graph, unit, recipe, approval and lineage validators;
- network-depth and dependency scorecard; and
- visual and tabular network summary for author review.

**Acceptance**

- the graph is connected, acyclic and dimensionally coherent;
- every assessed terminal material has more than one credible end-to-end supply
  strategy, except where an intentional single point of failure is documented;
- multi-sourcing differs from superficial duplicate lanes by price, lead time,
  capacity, ownership or risk;
- concentration and shared dependencies are measurable and relevant to later
  scenarios; and
- the network is understandable enough to support explanation in an
  interactive application without being reducible to a two-tier example.

### WP5 — Commercial and economic decision depth

**Design question**

Do the commercial facts create decisions that require optimisation, rather than
one source or route being obviously best in every circumstance?

**Activities**

- Generate supply contracts, Incoterm abstractions, duty, lanes, external
  prices, conversion costs, cost-allocation rules, FX and baseline standard
  costs.
- Restrict external unit prices to boundary sources and preserve the recursive
  cost policy for intermediate flows.
- Calibrate fixed versus variable costs, freight, lead time, MOQ/order
  multiples, setup, surge, overhead and markup so alternatives cross over at
  plausible volumes.
- Classify each cost component once as capitalised or non-capitalised, assign
  its stage and markup eligibility, and map it to a unique ledger class.
- Generate finite theoretical quantity, value and unit-cost envelopes.
- Review economic plausibility with ranges and comparisons, not a preferred
  allocation.

**Outputs**

- deterministic commercial and cost datasets;
- `COST_POLICY.md` and cost-ledger dictionary;
- cost plausibility, dominance and crossover report;
- finite bound report; and
- anti-double-count and baseline-isolation checks.

**Acceptance**

- every cost component is classified exactly once;
- no unintended source, route or recipe dominates across all relevant volumes
  and scenarios;
- at least several material decisions exhibit explainable fixed/variable,
  local/imported, lead-time/cost or regular/surge trade-offs;
- costs, margins, duties and freight remain within credible business ranges;
- baseline standard costs cannot enter recursive valuation; and
- the data supports explanation of why two reasonable formulations or policies
  may choose differently.

### WP6 — Planning-window and disruption depth

**Design question**

Does the planning window make timing, inventory, capacity and resilience
material to the decision?

**Activities**

- Generate source and transformation capacity, inventory policy, opening
  quantity/book value, terminal demand, supplier history and incident history.
- Shape demand, capacity and inventory over the 12 periods so that lead times,
  early commitments, storage, setup, surge and shortages can matter.
- Generate BASE plus SCN-01 through SCN-05 as deterministic impact data.
- Implement immutable scenario views with explicit targets, periods,
  multipliers, overlap and recovery rules.
- Distinguish `STRESS_ONLY` evaluation from `REOPTIMISE`.
- Construct BASE feasibility first, then calibrate scarcity and recourse.

**Outputs**

- deterministic planning and scenario datasets;
- `SCENARIO_CATALOGUE.md`;
- scenario transformation engine and validation suite;
- planning-window profile; and
- scenario materiality report.

**Acceptance**

- BASE has at least one feasible zero-shortage strategy without excessive
  artificial slack;
- important decisions cannot all be made period by period without considering
  lead time or future demand;
- scenarios do not mutate BASE and recover exactly as specified;
- each scenario tests a distinct business exposure and causes a measurable
  change in feasible options, service, cost, inventory or concentration;
- severe scenarios leave meaningful recourse or an explainable shortage; and
- repeated generation is deterministic.

### WP7 — Whole-dataset viability and calibration

**Design question**

Is the combined generated dataset sufficiently deep, coherent and calibrated
to sustain the intended consultant engagement?

**Activities**

- Generate candidate full datasets from controlled seeds and profile their
  structural, commercial, temporal and scenario characteristics.
- Use the private model-viability harness only as a smoke test for feasibility,
  recursive accounting and gross decision behaviour.
- Compare a small number of feasible or solver-found plans to identify trivial
  dominance, unused data, inactive constraints and implausible values.
- Inspect whether BASE and scenarios expose meaningful cost-service-inventory-
  resilience trade-offs.
- Tune generation parameters and regenerate; do not tune a preferred answer.
- Record broad plausibility bands and hidden quality checks without publishing
  a model solution.

**Outputs**

- release-candidate generated dataset and pinned generation configuration;
- dataset depth, fidelity and decision-richness scorecard;
- feasibility and recursive-accounting certificate;
- scenario materiality and sensitivity summary;
- broad private plausibility bands; and
- calibration decision log.

**Acceptance**

- every contract validates and generation is reproducible;
- the dataset meets approved structural-depth and dependency targets;
- BASE is feasible and scenarios behave as designed;
- multiple credible strategies remain, with no accidental universal winner;
- material constraints and cost components participate in at least one
  decision or scenario;
- values and outcomes remain commercially plausible; and
- the retained private harness can perform its smoke checks, without becoming a
  required full reference optimiser or output pipeline.

### WP8 — Consultant engagement and assessment design

**Design question**

Have we specified a business engagement that asks the candidate to exercise
judgement, build an explicit optimisation formulation and communicate a
decision—not reproduce an author solution?

**Activities**

- Define the client decision, intended users, planning cadence, authority
  boundaries and material business questions.
- Specify the required data audit, assumptions, explicit MILP or MINLP
  formulation, method justification, validation, scenarios, resilience
  intervention and recommendation.
- Separate required business and accounting semantics from permitted modelling
  libraries, algorithms and solver strategies.
- Define evidence for reasoning quality, model ownership, uncertainty,
  limitations and production readiness.
- Translate application requirements into user questions and interpretable
  decisions rather than a checklist of charts.
- Map every student obligation to a rubric criterion, deterministic quality
  gate or technical-defence prompt.

**Outputs**

- controlled consultant brief and task requirements;
- business-question and decision-rights map;
- method-neutral model and validation requirements;
- application interpretation and evidence contract;
- CAP-001 rubric and technical-defence design; and
- requirement-to-evidence traceability.

**Acceptance**

- the brief states what the business needs decided and why;
- candidates must construct and defend an explicit MILP or MINLP but are not
  forced into the private authoring architecture;
- alternative defensible methods can earn full credit;
- every required output or application view answers a stated business,
  validation or interpretability question;
- scoring rewards reasoning, validation and communication rather than proximity
  to a hidden allocation; and
- no undisclosed author implementation detail is needed to pass.

### WP9 — Student release and application evidence contract

**Design question**

Can a candidate begin the engagement from a clean environment with the data,
standards and scaffolding they need, without receiving an exemplar solution?

**Activities**

- Package the 26 raw files, miniature fixture, dictionaries, schemas, cost
  policy, scenario catalogue and controlled consultant brief.
- Provide a neutral starter repository containing contracts, commands, test
  hooks and output locations, but no reference formulation or allocation.
- Document accessible solver options, runtime policy, stored-result policy and
  permitted status language without prescribing a single package.
- Specify full-stack application behaviours for exploring the network,
  explaining decisions, tracing costs, comparing scenarios and exposing
  failures or uncertainty.
- Provide AI-usage and technical-defence guidance.
- Build the allow-list release and private-content scanner.
- Run a clean-room candidate onboarding journey.

**Outputs**

- versioned student release and manifest;
- neutral starter repository;
- data, model, validation and solver guidance;
- output and application evidence contracts;
- `AI_USAGE_TEMPLATE.md`;
- technical-defence guide; and
- learner FAQ.

**Acceptance**

- a fresh user can install the environment, validate the supplied data, inspect
  the fixture and understand every required deliverable;
- all files match manifest hashes and row counts;
- the release contains no private generator, calibration harness, hidden
  thresholds or reference result;
- every requirement maps to the rubric or a quality gate;
- no licensed solver is a hidden prerequisite; and
- the application contract requires interpretable business evidence, including
  stale, failed, local and time-limited result states.

### WP10 — Evaluation controls and assessor workflow

**Design question**

Can assessors distinguish a correct, well-reasoned and useful submission from a
plausible-looking one without requiring candidates to match a single hidden
solution?

**Activities**

- Validate submission structure, declared commands, dependencies and release
  versions.
- Recompute physical balances, recursive value equations, ledger
  classification, terminal lineage, scenario transformations and reported
  metrics from submitted outputs.
- Check formulation evidence, method/status claims and consistency between
  code, reports and application views.
- Use feasibility, reconciliation, broad plausibility bands and disclosed
  benchmark evidence without treating one allocation as the only valid answer.
- Build cited evidence for rubric scoring and route contradictions, boundary
  cases and material uncertainty to a human.
- Produce technical-defence prompts targeted to each submission.
- Calibrate the workflow through pilot submissions and deliberately defective
  artefacts rather than an author-built exemplar application.

**Outputs**

- submission runner and deterministic quality-gate engine;
- independent physical and financial validation tools;
- evidence collector and CAP-001 rubric implementation;
- versioned AI evaluator prompt and structured output;
- reviewer and defence guides; and
- auditable calibration and assessment records.

**Acceptance**

- feasible alternative solutions are not penalised for differing from private
  smoke-test results;
- physical, financial and reporting defects are detected independently;
- rubric evidence citations resolve to actual submission artefacts;
- failed gates constrain scoring according to approved policy;
- close-to-boundary, contradictory and low-confidence cases reach a human;
- sample and pilot submissions score reproducibly; and
- no AI score can silently override a deterministic failure.

### Pilot and release

**Activities**

- Run at least one clean-room build and two pilot student journeys.
- Observe setup, modelling, reconciliation, application and defence failure points.
- Re-run calibration after pilot fixes.
- Freeze capstone, data, contracts, rubric and evaluator versions.
- Sign manifests, hashes, benchmark environment and release approval.
- Archive the private calibration and evaluation evidence.

**No-release gate**

No student release may be issued until the miniature fixture, generated dataset,
schemas, dataset-depth scorecard, consultant brief, application evidence
contract and every physical, financial, scenario, security and clean-environment
acceptance check pass. The private model-viability harness must confirm
feasibility and accounting, but a complete author solution is not a release
prerequisite.

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

Dates should be set after owner availability is known. Progress is measured by
authoring outcomes rather than the amount of solution code produced.

| Stage | Indicative duration | Exit |
|---|---:|---|
| Mobilisation and ADR framing | 1 week | Requirements, owners and ADR register approved |
| WP1 configuration and contracts | 1–2 weeks | Raw and output contracts validate |
| WP2 miniature fixture | 1 week | Hand totals and negative variants pass |
| WP3 model viability | Frozen | Sufficient private fixture-scale evidence retained |
| WP4 network depth | 1–2 weeks | Connected, choice-rich multi-tier structure passes its scorecard |
| WP5 economic depth | 1–2 weeks | Plausible commercial trade-offs and cost controls pass |
| WP6 planning/scenario depth | 1–2 weeks | Temporal decisions and distinct material scenarios pass |
| WP7 whole-dataset calibration | 1–2 weeks | Release-candidate dataset is viable, non-trivial and pinned |
| WP8 engagement and assessment design | 1–2 weeks | Business ask, evidence contract and rubric align |
| WP9 student release and app contract | 1–2 weeks | Clean-room candidate onboarding passes |
| WP10 evaluation controls | 2 weeks, overlapping WP9 | Pilot evidence scores reproducibly without exact-solution matching |
| Pilot and release | 1–2 weeks | No-release gate and sign-offs pass |

WP4–WP6 may iterate in parallel, but WP7 is the point at which their combined
effect is judged. Passing each generator independently is not sufficient if the
combined dataset is trivial, implausible or fails to produce material business
trade-offs.

## 18. Next delivery tranche

### Objective

Produce and review the first full candidate dataset, then decide whether it
creates the depth of analysis, optimisation and interpretation expected from
the consultant engagement.

### Backlog

1. Freeze measurable target ranges for network depth, path diversity,
   concentration and shared dependency.
2. Generate the first full structural network and review its lineage visually
   and quantitatively.
3. Add commercial data and test for accidental dominance and credible cost
   crossovers.
4. Add the planning window, capacity, inventory, demand and scenarios.
5. Produce the combined dataset-depth, fidelity and decision-richness
   scorecard.
6. Run contract, physical-feasibility and recursive-accounting smoke checks
   using the retained private harness.
7. Compare several credible plans or solver-found candidates only far enough to
   expose inactive data, trivial choices and scenario materiality.
8. Draft the client decision questions and map them to required analyses,
   application evidence and rubric criteria.
9. Tune generator parameters and regenerate where the evidence is weak; do not
   tune toward a preferred allocation.
10. Hold an author review of whether the dataset can sustain a suitably deep
    consultant submission.

### Exit

- the generated dataset is deterministic, valid and physically feasible;
- structural, commercial and temporal depth targets are met;
- multiple credible strategies and material scenario responses exist;
- recursive value semantics remain coherent;
- no major table, cost component or scenario is merely decorative;
- the intended business questions can be answered from the supplied data;
- the application evidence contract can explain decisions and uncertainty; and
- reviewers agree that the challenge tests consultant reasoning rather than
  reproduction of an author solution.

## 19. Principal risks and controls

| Risk | Control |
|---|---|
| Dataset is large but optimisation choices are trivial | Decision-richness scorecard, dominance checks, alternative-plan review and regeneration |
| Network complexity is decorative rather than decision-relevant | Path-diversity, dependency, active-constraint and scenario-participation measures |
| Generated data is physically infeasible or financially incoherent | Constructive generation, fixture invariants, private feasibility smoke tests and independent reconciliation |
| Commercial values are implausible | Business-range review, crossover analysis and cost-component plausibility bands |
| Scenarios repeat the same exposure or have negligible effect | Distinct scenario hypotheses, materiality measures and author review |
| Recursive MINLP is too difficult for the intended cohort | Fixture-first guidance, explicit formulation requirement, permitted justified strategies, time-limited incumbents and formulation-focused grading |
| Solver access creates unfairness | Accessible examples, declared budgets, method-neutral rubric and explicit access/status disclosure |
| Assessment overfits a hidden solution | Feasibility and reconciliation gates, broad plausibility evidence, alternative-method calibration and no exact-allocation requirement |
| Costs are double-counted, disappear or are diluted | Unique ledger policy, recursive roll-forward checks, zero-pool controls and independent validation |
| Application becomes a chart gallery | Business-question-to-view mapping, lineage and explanation requirements, uncertainty and failure-state evidence |
| Students overclaim optimality | Controlled status vocabulary, bound/gap checks, report/app consistency checks and defence questions |
| AI-generated work is not understood | AI usage evidence, targeted technical defence, cited validation and ownership scoring |
| Private authoring artefacts leak | Allow-list release builder, signature scan and independent review |
| AI evaluation becomes inconsistent | Deterministic evidence first, structured scoring, pilot calibration and human review near boundaries |

## 20. Definition of done

CAP-001 is ready for controlled student release only when:

1. all 12 ADRs and assessment-policy decisions are approved;
2. the shared configuration drives or verifies every derived artefact;
3. all 26 raw-data contracts and all standard outputs validate;
4. the miniature fixture and negative variants pass from a clean environment;
5. the full dataset passes approved network-depth, dependency, commercial,
   planning-window and scenario-materiality criteria;
6. BASE is feasible, multiple credible strategies remain and all scenarios
   behave as intended;
7. private smoke tests confirm physical and recursive-accounting viability
   without requiring a complete author solution;
8. the consultant brief states a credible business decision and requires a
   defended explicit MILP or MINLP formulation;
9. every required analysis, output and application behaviour maps to a
   business question, quality gate or rubric criterion;
10. solver access, budgets, permitted methods and status language are fair and
    documented;
11. the student pack contains the necessary data, modelling, application, AI
    and defence support without leaking private authoring artefacts;
12. the evaluator validates feasibility and accounting independently while
    allowing defensible alternative solutions;
13. AI scores are evidence-cited and human-review triggers operate;
14. at least two pilot journeys complete without an undisclosed requirement;
15. the release manifest, hashes, row counts, commands and output contracts
    agree; and
16. the capstone owner, domain lead, optimisation lead, evaluation lead and
    technical reviewer sign the release.
