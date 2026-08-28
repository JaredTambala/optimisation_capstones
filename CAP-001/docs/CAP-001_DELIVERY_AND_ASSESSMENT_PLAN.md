# CAP-001 Delivery and Assessment Implementation Plan

## Document control

| Field | Value |
|---|---|
| Plan | CAP-001 Supplier Allocation Under Disruption Risk — Tier-N End-to-End Cost and Resilience Optimisation |
| Plan version | 0.3 |
| Status | WP9 completed and accepted; final issue remains outside the current scope |
| Date | 28 August 2026 |
| Governing specification | *CAP-001 Tier-N End-to-End Cost Model, Modelling Decisions and Dataset Generation Specification* v0.3 |
| Governing specification SHA-256 | `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` |
| Inherited standard | *Optimisation, Search and Decision Intelligence Capstone Control Standard* v0.2 |
| Inherited standard SHA-256 | `2741ebd6b1e01e4102c39c9f43de3a9f05b081aa61a3efd2838a431024a45637` |
| Precedence | CAP-001 v0.3 governs business, network, model, data, output and CAP-specific assessment semantics; approved ADRs and the shared decision configuration govern implementation detail; the common standard governs shared repository, submission and AI-native assessment controls |
| Controlled versions | Capstone `0.3.0`; decision configuration `0.3.6`; data `0.3.3`; model `0.3.1`; schema `0.4.0`; rubric `1.1.0` |
| Audience | Capstone owner, domain lead, data lead, optimisation lead, application lead, evaluation lead, technical reviewer and pilot facilitators |

### Implementation status

| Work package | Status | Evidence |
|---|---|---|
| WP1 — Decision configuration and schemas | Completed and accepted on 31 July 2026 | `docs/WP1_ACCEPTANCE_REPORT.md` |
| WP2 — Miniature recursive-cost fixture | Implementation complete; formal acceptance pending | `docs/change-notes/CAP-001_MINIATURE_FIXTURE_TOPOLOGY_CHANGE_NOTES.md`; `tooling/validate_fixture.py`; `tests/test_miniature_fixture.py` |
| WP3 — Model-viability proof | Frozen at sufficient author-side evidence on 18 August 2026; not a model-solution deliverable | `docs/WP3_IMPLEMENTATION_STATUS.md`; retained private smoke tests |
| WP4 — Network structure and dependency depth | Completed and accepted on 18 August 2026; depth thresholds frozen | `docs/WP4_NETWORK_DESIGN_CONTRACT.md`; `docs/NETWORK_STRUCTURE_IMPLEMENTATION_STATUS.md` |
| WP5 — Commercial and economic decision depth | Completed and accepted on 18 August 2026; 19 active gates pass after CN-005 and thresholds are frozen; formal ADR-005 review remains pending | `docs/COMMERCIAL_ECONOMIC_DESIGN_CONTRACT.md`; `docs/COMMERCIAL_ECONOMIC_IMPLEMENTATION_STATUS.md` |
| WP6 — Planning-window and disruption depth | Recalibrated and accepted on 25 August 2026; 24/24 gates pass and package hashes are frozen | `docs/PLANNING_AND_SCENARIO_DESIGN_CONTRACT.md`; `docs/PLANNING_AND_DATASET_PACKAGE_IMPLEMENTATION_REPORT.md`; generated package evidence; accepted `adrs/ADR-008.md` |
| WP7 — Whole-dataset viability audit | Completed and accepted on 25 August 2026; all 10 gates pass | `docs/WHOLE_DATASET_VIABILITY_AUDIT_PLAN.md`; `generated/viability/WHOLE_DATASET_VIABILITY_REPORT.md` |
| WP8 — Consultant engagement and assessment design | Completed and accepted on 27 August 2026; design contract and all six controlled deliverables frozen at 1.0 | `docs/CONSULTANT_ENGAGEMENT_AND_ASSESSMENT_DESIGN_CONTRACT.md`; `docs/WP8_DELIVERABLE_REGISTER.md`; `docs/CAP-001_WP8_ACCEPTANCE_REPORT.md` |
| WP9 — Professional candidate release | Completed and accepted on 27 August 2026; repository-layout amendment completed on 28 August 2026 | `docs/CAP-001_WP9_PROFESSIONAL_RELEASE_CONTRACT.md`; `docs/WP9_DELIVERABLE_REGISTER.md`; `docs/CAP-001_WP9_ACCEPTANCE_REPORT.md`; `docs/change-notes/CAP-001_REPOSITORY_LAYOUT_CHANGE_NOTES.md` |

Final issue remains subject to the later release decision. WP9's professional
candidate pack, release controls and acceptance evidence are complete.

## 1. What changed

This plan supersedes the earlier CAP-001 delivery plan based on the two-tier, fixed-price MILP assessment.

The principal changes are:

1. The assessed network is now a generic Tier-N directed acyclic graph instantiated as four supplier tiers plus four Asterion plants.
2. The assessed economic formulation is a bounded, non-convex recursive-cost model using weighted-average quantity-and-value pools by node, material and period.
3. A solved, independently validated BASE reference incumbent is published as
   calibration evidence. It is not model input, a prescribed allocation or a
   global-optimality claim.
4. Every accepted solution route must be grounded in an explicit algebraic MILP or MINLP formulation. Exact, relaxed, approximate or heuristic solution strategies remain permissible around those formulations, but must be classified honestly, preserve the required accounting semantics, reconcile the result and qualify any optimality claim.
5. Physical and financial reconciliation is now central to release acceptance and assessment. Every active pool, shipment, transformation, inventory balance and terminal service flow must reconcile.
6. The release must include a hand-worked miniature fixture, expected reconciliation outputs and negative variants before the full generator is accepted.
7. The data contract contains 25 raw CSVs and a generic node, transformation, commercial-cost and scenario model.
8. The application contract requires governed data authoring, intuitive supply-
   graph exploration, configuration, recursive-cost lineage, comparison,
   solver-confidence and failure-state outcomes without prescribing named
   views.
9. The assessment rubric has been updated to give greater weight to mathematical formulation, validation/reconciliation, method selection and the interactive application.
10. A 20–30 minute technical defence and a detailed AI-usage record are mandatory parts of the evidence model.

## 2. Purpose and release outcome

The purpose of this plan is to create, validate, pilot and release everything required for a junior consultant to engage meaningfully with CAP-001, while also creating the deterministic, AI-assisted and human-review controls needed to assess the work fairly.

CAP-001 is a controlled advanced capstone. The student is not expected to prove global optimality for every recursive run. The student is expected to:

- understand the end-to-end sourcing decision and nominated-source commercial context;
- build a correct generic Tier-N physical-flow model;
- implement or faithfully approximate the required recursive weighted-average cost policy;
- reproduce the published BASE service and objective-quality controls with an
  independently valid recursive result and explain material aggregate
  differences;
- validate physical quantities, values, ledger classification and terminal lineage;
- import and validate every supplied package, evaluate BASE and use a
  proportionate candidate-justified set of supplied examples;
- demonstrate user-authored and assessor-authored complete dataset versions
  without hard-coded scenario behaviour;
- design at least one resilience intervention and explain the cost-service-inventory-resilience trade-off;
- communicate solver status and residual uncertainty honestly;
- deliver a usable decision-support application and client recommendation; and
- demonstrate ownership of AI-assisted work in a technical defence.

The assessor-side AI review guide must enable an agent to:

- reproduce the published BASE benchmark controls without editing source or
  consuming the reference solution as model input;
- distinguish exact, relaxed, approximate and heuristic methods;
- validate feasibility and reconciliation independently of the student’s claims;
- compare outputs with controlled references or best-known bounds;
- collect evidence against every rubric category;
- use proportionate inspection to test material claims without turning checks
  into deterministic submission gates;
- synthesise and score only from cited evidence against the published rubric;
- route contradictions, boundary cases and material uncertainty to a human; and
- produce an auditable assessment record.

## 3. Delivery principles

The implementation must follow these principles:

1. **One semantic source.** Approved ADRs must flow into one machine-readable decision configuration consumed or verified by the brief, schemas, dictionary, generator, models, validators and assessment guide.
2. **Fixture before scale.** Pooling and recursive-value semantics must be proved on the miniature fixture before the large generator or student release is accepted.
3. **Physical feasibility before economics.** Generate a valid Tier-N physical network first, then add commercial costs and calibrate economic trade-offs.
4. **One controlled formulation boundary plus known-case calibration.** Require
   candidates to construct an explicit bounded recursive-cost MILP or MINLP and
   reproduce the published BASE benchmark controls; private author code is
   needed only for viability and benchmark generation.
5. **Evidence before scoring.** The AI reviewer examines proportionate physical,
   value, ledger and constraint evidence before exercising rubric judgement;
   no fixed automated gate determines the submission score.
6. **Toolchain neutrality with disclosure.** Require the controlled MILP/MINLP semantics without mandating one modelling package. Do not create an undeclared grading advantage for a particular library or licensed solver; reward correctness, evidence, honest classification and defensible results.
7. **Private/public separation.** Private seeds, generation code, hidden checks,
   adversarial fixtures, AI review prompts and pilot submissions never enter
   the student release. The controlled BASE benchmark and its limitations are
   intentionally public.
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
| BASE calibration | Published heuristic recursive-value incumbent with service and objective-quality controls; solution evidence is never model input |
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

Each cost component must appear exactly once. Precomputed intermediate,
cumulative-path and terminal costs, and the reference solution itself, are
prohibited as recursive-model inputs.

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
  data/datasets/
    BASE/                                      # manifest + all 25 raw CSVs
    SCN-01/                                    # manifest + all 25 raw CSVs
    SCN-02/
    SCN-03/
    SCN-04/
    SCN-05/
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

The release builder must be allow-list based. It must fail on any private seed,
generator implementation, unapproved reference allocation, hidden expected-
objective range, hidden test, adversarial fixture, AI review prompt or
calibration example. The approved public BASE benchmark is an explicit
allow-list exception and must retain its non-prescriptive benchmark contract.

## 6. Governance, roles and decision rights

| Role | Primary accountabilities |
|---|---|
| Capstone owner | Learning outcomes, scope, assessment policy, release approval and exception decisions |
| Domain lead | Business realism, terminology, nominated-source workflow, cost policy and scenario plausibility |
| Optimisation lead | Equations, bounds, solver routes, private physical seed, BASE benchmark interpretation and permitted claims |
| Data lead | Shared configuration, schemas, generator, dictionary, lineage, checksums and release data |
| Application lead | Student user journey, required views, evidence capture, accessibility and failure states |
| Evaluation lead | Rubric, private AI-agent review prompt, moderation and reviewer calibration |
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
| Assessment operations | Approved moderation, resubmission and appeal policy |

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
- Define typed schemas for all 25 raw files, the miniature fixture, submission metadata and required outputs.
- Generate the human data dictionary and empty valid contract examples.
- Establish stable identifiers, foreign keys, units, currencies, effective periods and null rules.
- Define common status, run-mode and formulation-classification vocabularies.
- Scaffold private control, student release and submission repositories.

**Outputs**

- decision configuration `0.3.1`;
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

Amended by change note CN-002 (`docs/change-notes/CAP-001_MINIATURE_FIXTURE_TOPOLOGY_CHANGE_NOTES.md`): the fixture uses a richer four-layer, multi-sourced topology in place of the single-chain fixture originally described in v0.3 §12.8/Appendix E, in order to demonstrate weighted-average anti-dilution at more than one point in the network. This amendment is scoped to the fixture only; it does not change `network.release_instance_supplier_tiers`, `network.plant_count`, `target_scale`, or any recursive-cost accounting equation.

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

- it reads the 25 raw contracts independently of the hand-worked reconciler;
- it instantiates a private local-fact physical-seed MILP;
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

These checks establish semantic viability only. WP4–WP6 supplied and froze the
12-period datasets; the bounded WP7 whole-dataset viability audit has now
accepted their combined depth and computational accessibility at all ten gates.

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

Design contract: `docs/WP4_NETWORK_DESIGN_CONTRACT.md`. Current implementation
evidence: `docs/NETWORK_STRUCTURE_IMPLEMENTATION_STATUS.md`.

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
- multi-sourcing uses distinct seller nodes and retains evidence of genuinely
  different upstream organisational lineages; WP5 must then prove that the
  alternatives differ commercially;
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
  prices, conversion costs, cost-allocation rules and FX.
- Restrict external unit prices to boundary sources and preserve the recursive
  cost policy for intermediate flows.
- Calibrate fixed versus variable costs, freight, lead time, MOQ/order
  multiples, setup, overhead and markup so alternatives cross over at
  plausible volumes. Source and transformation surge premiums are generated
  with the corresponding WP6 capacities.
- Classify each cost component once as capitalised or non-capitalised, assign
  its stage and markup eligibility, and map it to a unique ledger class.
- Generate finite conditional commercial cost envelopes at explicit order
  quantities. Complete formulation bounds follow in WP7 after WP6 supplies
  capacities, storage, demand and opening inventory.
- Review economic plausibility with ranges and comparisons, not a preferred
  allocation.

**Outputs**

- deterministic commercial and cost datasets;
- `COST_POLICY.md` and cost-ledger dictionary;
- cost plausibility, dominance and crossover report;
- conditional commercial-envelope report and WP7 bound hand-off; and
- anti-double-count and derived-value-input-isolation checks.

**Acceptance**

- every cost component is classified exactly once;
- no unintended source, route or recipe dominates across the representative
  commercial order quantities; scenario-sensitive dominance is judged in WP7;
- at least several material decisions exhibit explainable fixed/variable,
  local/imported or lead-time/cost trade-offs;
- costs, margins, duties and freight remain within credible business ranges;
- precomputed intermediate, cumulative-path or terminal values cannot enter
  recursive valuation; and
- the data contains documented ranking conflicts that could make two reasonable
  formulations or policies choose differently; solved decision differences are
  demonstrated only during WP7 calibration.

### WP6 — Planning-window and disruption depth

**Design question**

Does the planning window make timing, inventory, capacity and resilience
material to the decision?

**Activities**

- Generate source and transformation capacity, inventory policy, opening
  quantity/book value, terminal demand, supplier history and incident history.
- Shape demand, capacity and inventory over the 12 periods so that lead times,
  early commitments, storage, setup, surge and shortages can matter.
- Treat the complete P01–P12 contents of the selected package, including dated
  impacts and recovery, as known when the P01 horizon-wide plan is constructed.
  Do not present supplied scenarios as surprises revealed during execution.
- Assemble BASE plus SCN-01 through SCN-05 as six complete, independently
  checksummed 25-file dataset packages with no cross-package fallback.
- Include only the selected package's scenario metadata and any package-local
  period impacts needed where another raw table is not period-grained.
- Require the same loader, validation and model-construction path to accept all
  six packages after a complete state reset.
- Distinguish `STRESS_ONLY` evaluation from `REOPTIMISE`.
- Construct BASE feasibility first, then calibrate scarcity and recourse.

**Outputs**

- six deterministic, self-contained planning and scenario dataset packages;
- `SCENARIO_CATALOGUE.md`;
- dataset manifests, package-local preparation rules and validation suite;
- planning-window profile; and
- scenario materiality report.

**Acceptance**

- BASE has at least one feasible zero-shortage strategy without excessive
  artificial slack;
- important decisions cannot all be made period by period without considering
  lead time or future demand;
- every scenario is presented as one deterministic P01–P12 planning case fully
  known at P01, rather than as a single-period allocation or mid-run revelation;
- every package contains all 25 files, validates independently and requires no
  lookup into BASE or another package;
- the same loader and formulation-construction entry point accepts every
  package without stale state, while package-local impacts recover exactly as
  specified;
- each scenario tests a distinct business exposure and causes a measurable
  change in feasible options, service, cost, inventory or concentration;
- severe scenarios leave meaningful recourse or an explainable shortage; and
- repeated generation is deterministic.

### WP7 — Whole-dataset viability audit

**Design question**

Do the six frozen datasets contain enough combined depth for a student to build
and defend an explicit MILP or MINLP decision system with configurable policies
and interpretable outputs?

**Activities**

- Treat the accepted WP4–WP6 outputs as frozen inputs and verify their hashes
  and inherited checks before any solve.
- Combine planning facts and commercial envelopes into finite, challenged
  full-scale formulation bounds.
- Run one common private physical-seed MILP path across all six complete
  packages and classify feasibility, shortage, broad outcomes and active
  constraint families. Its proxy economics are author-side diagnostics, not a
  candidate economic formulation.
- Run a small, predeclared matrix of resilience, intervention, approval and
  within-hierarchy policy configurations without editing any dataset.
- Use explicit MILP or MINLP runs to demonstrate at least one opposed aggregate
  trade-off rather than a universally dominant strategy.
- Obtain and independently reconcile a bounded recursive-cost MINLP incumbent
  for BASE and one material stress case; global optimality is not required.
- Classify every data family as mathematical, configuration or
  interpretive/audit evidence and record broad plausibility only.

**Outputs**

- frozen-input and audit manifest;
- ten-gate whole-dataset viability scorecard;
- full-scale bound, feasibility and recursive-reconciliation summaries;
- aggregate configuration, trade-off and scenario-materiality evidence;
- data-participation classification and broad private plausibility bands; and
- owner acceptance or a specific controlled-reopen decision.

**Acceptance**

- all six inputs retain the accepted hashes and pass inherited controls;
- one explicit private physical-seed MILP path accepts all six packages, with BASE
  retaining zero shortage and every stress result honestly classified;
- every scenario has traceable data-to-construct-to-outcome materiality;
- configuration probes demonstrate resilience, intervention, approval and
  objective-parameter behaviour without editing the data;
- at least two feasible explicit-formulation incumbents show an opposed
  aggregate trade-off;
- full-scale recursive bounds are safe and BASE plus one stress MINLP incumbent
  reconcile within tolerance;
- every data family is useful in its declared mathematical, configuration or
  interpretive role; and
- the retained evidence contains no allocation, hidden answer, preferred plan
  or reference application.

The detailed scope, ten gates and change-control rules are fixed in
`docs/WHOLE_DATASET_VIABILITY_AUDIT_PLAN.md`.

### WP8 — Consultant engagement and assessment design

Frozen design contract:
`docs/CONSULTANT_ENGAGEMENT_AND_ASSESSMENT_DESIGN_CONTRACT.md`.

Frozen WP8 deliverables:

- `docs/WP8_DELIVERABLE_REGISTER.md`;
- `docs/CAP-001_CONSULTANT_ENGAGEMENT_BRIEF.md`;
- `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md`;
- `docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md`;
- `docs/CAP-001_ASSESSMENT_RUBRIC_AND_DEFENCE_CONTRACT.md`;
- `docs/CAP-001_WP8_REQUIREMENT_EVIDENCE_TRACEABILITY.md`; and
- `docs/CAP-001_WP8_ACCEPTANCE_REPORT.md`.

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
- Write application requirements as user capabilities and observable business
  outcomes. Reserve concrete technical instructions for data integrity,
  effective dating, lineage and reproducibility, plus a concise application-wide
  non-functional baseline.
- Define evidence for reasoning quality, model ownership, uncertainty,
  limitations and production readiness.
- Require governed in-application data authoring: treat each of the 25 supplied
  files as a starting extract for its logical master table, provide full
  Incoterm visibility and version-preserving CRUD, publish an immutable as-of
  dataset version across all 25 masters and solve against that explicitly
  selected version.
- Treat BASE and SCN-01 through SCN-05 as example data realities rather than a
  closed scenario menu; require the application to accept another complete
  schema-valid dataset version without a product change.
- Require intuitive visual exploration of the selected supply graph and its
  upstream and downstream relationships, while leaving the graph technology,
  visual design and interaction model to the candidate.
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
- data-handling instructions are technically concrete enough to make version
  history, effective dating, atomic publication and solve lineage unambiguous;
- application-wide non-functional requirements set proportionate, testable
  expectations for accessibility, responsiveness, resilience, security,
  auditability and reproducibility;
- all remaining application requirements describe actor-visible behaviours and
  outcomes without prescribing internal architecture, pages or frameworks;
- candidates must construct and defend an explicit MILP or MINLP but are not
  forced into the private authoring architecture;
- alternative defensible methods can earn full credit;
- every required output or application view answers a stated business,
  validation or interpretability question;
- a user can change Incoterm or other supported business facts, understand the
  draft's impact, create traceable successor master-record versions, publish a
  complete as-of dataset version, then solve against it;
- a user can orient themselves visually in the supply graph, follow relevant
  upstream and downstream relationships and connect data changes and results to
  affected graph elements without a mandated implementation;
- supplied scenarios are examples and application behaviour is not hard-coded
  to their identifiers or transformations;
- scoring rewards reasoning, validation and communication rather than proximity
  to a hidden allocation; and
- no undisclosed author implementation detail is needed to pass.

### WP9 — Student release and application evidence contract

**Design question**

Can a candidate begin the engagement from a clean environment with the data,
standards and scaffolding they need, without receiving an exemplar solution?

**Activities**

- Package the 25 raw files, miniature fixture, dictionaries, schemas, cost
  policy, scenario catalogue and controlled consultant brief.
- Present the student brief as functional client requirements, with separately
  identified technical data-handling instructions and a concise non-functional
  application baseline.
- Provide a neutral starter repository containing contracts, commands, test
  hooks and output locations, but no reference formulation or allocation.
- Document accessible solver options, runtime policy, stored-result policy and
  permitted status language without prescribing a single package.
- Specify full-stack application behaviours for intuitively exploring the
  supply graph, explaining decisions, tracing costs, comparing dataset versions
  and exposing failures or uncertainty, without prescribing a graph library or
  layout.
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
- every requirement maps to a business purpose, evidence obligation or rubric
  category;
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

- private versioned AI submission-review system prompt;
- concise candidate-facing 100-point rubric;
- evidence-citation and structured review guidance;
- reviewer and moderation guidance; and
- auditable calibration and assessment records.

**Acceptance**

- feasible alternative solutions are not penalised for differing from private
  smoke-test results;
- material physical, financial and reporting claims are examined against cited
  evidence;
- rubric evidence citations resolve to actual submission artefacts;
- close-to-boundary, contradictory and low-confidence cases reach a human;
- sample and pilot submissions demonstrate reasonable reviewer calibration;
  and
- the workflow contains no deterministic submission evaluator or hidden model
  answer.

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
| `TASK_REQUIREMENTS.md` | Normative functional, mathematical, data and non-functional obligations |
| `BUSINESS_CONTEXT.md` | Asterion workflow, nominated-source authority and decision cadence |
| `LEARNING_PATH.md` | Recommended order: data audit, fixture, recursive method, BASE benchmark reproduction, validation, data realities, resilience, app |
| `GLOSSARY.md` | Pooling, value flow, transformations, tiers, formulations, solver status and commercial terms |
| `AI_NATIVE_WORKING_GUIDE.md` | Expected uses of AI, validation duties and evidence examples |
| `DATA_DICTIONARY.md` | Generated field-level definitions, units, domains, keys and relationships |
| machine-readable schemas | Early structural validation of all inputs and outputs |
| `config/default_case.yaml` | Default supplied data identity, horizon, method defaults, seeds and runtime budgets |
| `COST_POLICY.md` | Capitalisation, non-capitalised items, markup base and single-ledger rules |
| `SCENARIO_CATALOGUE.md` | BASE/SCN-01–05 as example complete data realities and any retained run-mode semantics |
| miniature fixture | Hand-worked recursive accounting and expected reconciliation |
| `MODEL_REQUIREMENTS.md` | Required physical/economic semantics without releasing the main solution |
| `SOLVER_AND_STATUS_GUIDE.md` | Supported routes, budgets, method classification and permitted claims |
| starter repository | Manifest, config, tests, commands and output paths |
| report templates | Model, solver, validation, recommendation and production-readiness evidence |
| `AI_USAGE_TEMPLATE.md` | Material AI assistance, validation, changes, rejections and accountability |
| application evidence guide | Required functional journeys, reproducible evidence, exports and failure behaviours |
| technical-defence guide | Expected 20–30 minute format and evidence to retain |
| `PRODUCTION_EXTENSION.md` | Production-readiness outcomes covering integration, security, scale, monitoring, recovery and fallback |
| learner FAQ | Operational clarification without exposing private results |

The learning path should require students to pass the miniature fixture before attempting the full recursive model.

## 11. Student submission contract

The submission must provide one declared command for each of:

1. installing dependencies;
2. running automated tests;
3. reproducing the published BASE reference controls through the submitted
   assessed model or producing an honestly classified failure record;
4. solving another selected published dataset or producing a documented
   time-limited incumbent;
5. launching the application; and
6. optionally regenerating standard reports from stored controlled outputs.

The submission manifest declares the commands and locations of required
machine evidence, reports, presentation and AI disclosure. The candidate owns
the internal source-tree, application, test and configuration layout; the
student brief must not turn an indicative repository structure into a hidden
architecture requirement.

The evaluator must mount authoritative input data read-only and must not edit student code or configuration to make it run.

## 12. Required result and evidence outputs

The frozen WP8 burden is organised by evidence purpose:

- every run supplies metadata, metrics, orders, shipments, production,
  inventory/value roll-forward, demand/service, constraint evidence and a
  reconciliation summary;
- every assessed recursive run additionally supplies the cost-component ledger
  and cost lineage; detailed recursive equalities are independently calculated
  in working memory and summarised, not emitted as a dedicated file; and
- BASE benchmark-reproduction, dataset-version and configuration comparisons
  are generated once per declared comparison set rather than duplicated inside
  every run.

The detailed grain and applicability rules are in
`docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md`. WP8 replaces the
closed `scenario_comparison.csv` concept with dataset/configuration comparison
evidence and retires `scenario_results.csv`. WP9 must evolve the schemas to
implement that frozen burden.

Default acceptance tolerances are:

- quantity: `max(1e-5 units, 1e-7 × relevant scale)`;
- value: `max(EUR 1e-3, 1e-7 × relevant value scale)`;
- unit cost: `max(EUR 1e-5/unit, 1e-7 × relevant cost scale)`;
- integrality: `1e-6`; and
- bounds: the same absolute/relative convention as the relevant quantity or value.

Any change requires ADR approval and regeneration of fixture, reference and evaluator evidence.

## 13. Application contract

The application may solve live, submit asynchronous jobs or retrieve controlled
stored results. It must always show the relevant dataset/configuration version,
result age, job state, method classification and solver status.

The required outcomes are functional journeys: governed data and Incoterm
authoring, immutable publication, intuitive supply-graph exploration,
configuration and authority, solve initiation/state, horizon-plan and recursive-
value interpretation, comparisons, validation/failure evidence and a decision
summary. The candidate decides how those journeys are arranged in the product.

The detailed behaviour and evidence rules are in
`docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md`. The product must expose
failure, stale/stored-result, violated-check and uncertainty states and must
never relabel a local, approximate or time-limited result as globally optimal.

## 14. Solver fairness and runtime policy

Provisional calibration targets are:

| Run | Budget |
|---|---|
| Miniature fixture | Complete and reconcile within 2 minutes |
| BASE benchmark reproduction | Up to 20 minutes; retain and validate an incumbent |
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
| Method selection and implementation | 14 | Recursive/relaxed/approximate strategy with justified controls and honest classification |
| Validation, benchmarking and robustness | 15 | Fixture, BASE benchmark reproduction, reconciliation, adversarial tests, scenarios, sensitivity and multi-start evidence |
| Interactive application | 14 | Network, allocation, lineage, scenarios, resilience, solver and failure views |
| Software engineering and reproducibility | 10 | Modular code, reference/input isolation, tests, configuration, logging and commands |
| Presentation and recommendation | 7 | Client narrative, trade-offs, evidence, caveats and permitted claims |
| Production readiness and limitations | 5 | Integration, data ownership, security, scale, async solving, monitoring and fallback |
| Technical defence | 3 | Ownership of AI-assisted formulation, validation and interpretation |
| **Total** | **100** | |

### 15.2 Assessment stages

1. **Understand the submission** — use the candidate's own instructions to
   inspect the application, formulation, evidence and recommendation.
2. **Test material claims** — select proportionate checks of data identity,
   physical feasibility, recursive value, cost treatment, solver status and
   application behaviour because they matter to the submitted claims.
3. **Rubric review** — use the private AI-agent system prompt to award each
   category score from cited evidence and explain material judgement.
4. **Moderation and technical defence** — resolve contradictions, inaccessible
   evidence, uncertainty and ownership questions through human judgement.

### 15.3 Review boundary

CAP-001 does not use a deterministic evaluator over candidate submissions.
File presence, command results, keyword matches and isolated recomputations do
not create an undisclosed pass/fail layer or automatic score cap. They are
evidence that the reviewer weighs in context.

The author-side contract builder, dataset checks, benchmark replay and
clean-room release validator remain deterministic. They prove that the
capstone materials supplied to every candidate are coherent; they do not grade
candidate work.

### 15.4 AI evaluation controls

The private AI review guide must instruct the agent to:

- use evidence-grounded professional judgement against the published rubric;
- cite exact evidence paths and, where practical, rows, model components,
  application observations, views or slides;
- distinguish absent evidence from poor evidence;
- identify contradictions rather than silently resolving them;
- produce category scores, rationales, citations and confidence in a consistent
  review format;
- never infer global optimality from a low residual alone;
- never compare the submission with a hidden allocation or preferred
  architecture;
- treat direct checks as contextual evidence rather than deterministic gates;
  and
- identify matters requiring technical defence or human moderation.

### 15.5 Technical defence

The 20–30 minute defence must sample:

- one Tier-N physical balance;
- one weighted-average pool and value roll-forward;
- one cost-capitalisation or markup decision;
- the submitted BASE result versus the published reference controls;
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
- derived-value-input and reference-solution-isolation tests;
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
| WP7 whole-dataset viability audit | Evidence-bounded | Frozen datasets are accepted as viable and non-trivial, or a specific data control is reopened |
| WP8 engagement and assessment design | 1–2 weeks | Business ask, evidence contract and rubric align |
| WP9 student release and app contract | 1–2 weeks | Clean-room candidate onboarding passes |
| WP10 evaluation controls | 2 weeks, overlapping WP9 | Pilot evidence scores reproducibly without exact-solution matching |
| Pilot and release | 1–2 weeks | No-release gate and sign-offs pass |

WP4–WP8 are now frozen and accepted. A proven data defect or materially trivial
scenario reopens only the originating control through explicit change
management, followed by full dependent regeneration, new hashes and renewed
acceptance.

## 18. Next delivery tranche

### Objective

Execute WP9 by turning the frozen WP8 authoring contracts into a coherent,
clean-room student release without exposing private generation or evaluator
material and without prescribing the candidate's implementation.

### Backlog

1. Populate the student-facing consultant brief and task requirements from the
   frozen WP8 sources.
2. Evolve configuration and schemas so supplied package IDs are provenance
   examples rather than a closed runtime, and state the full P01-known horizon
   assumption explicitly.
3. Implement the persistent master-record and published-dataset identity
   contract, including effective/audit time, lineage, resolved record versions
   and immutable content hashes.
4. Extend the Incoterm contract for active/effective state, schema-valid
   creation and version-preserving CRUD semantics.
5. Replace scenario-labelled comparison contracts with dataset/configuration
   comparison contracts and retire `scenario_results.csv`.
6. Update run metadata, release manifests, starter submission contracts and
   evidence templates to the frozen WP8 burden.
7. Document at least one accessible algebraic solver route, runtime/stored-
   result policy and honest status handling without making a commercial solver
   a prerequisite.
8. Regenerate derived artefacts and hashes, run private-leak checks and complete
   the clean-room candidate onboarding journey.

### Exit

- a candidate can start from a clean environment and understand the client ask,
  technical boundaries, supplied data, benchmark and evidence obligations;
- student-facing artefacts implement the frozen WP8 meanings without stale
  scenario enumeration or author-implementation leakage;
- data, Incoterm, publication, run-lineage and comparison contracts support an
  arbitrary complete dataset version;
- the approved BASE reference remains calibration evidence, not a prescribed
  allocation or model input;
- accessible solver and stored-result routes are fair and honestly classified;
  and
- clean-room build, manifest, checksum and private-leak gates pass.

## 19. Principal risks and controls

| Risk | Control |
|---|---|
| Dataset is large but optimisation choices are trivial | Decision-richness scorecard, opposed-trade-off probes and a controlled reopen decision |
| Network complexity is decorative rather than decision-relevant | Path-diversity, dependency, active-constraint and scenario-participation measures |
| Generated data is physically infeasible or financially incoherent | Constructive generation, fixture invariants, private feasibility smoke tests and independent reconciliation |
| Commercial values are implausible | Business-range review, crossover analysis and cost-component plausibility bands |
| Scenarios repeat the same exposure or have negligible effect | Distinct scenario hypotheses, traceable materiality measures and a controlled reopen decision |
| Recursive MINLP is too difficult for the intended cohort | Fixture-first guidance, explicit formulation requirement, permitted justified strategies, time-limited incumbents and formulation-focused grading |
| Solver access creates unfairness | Accessible examples, declared budgets, method-neutral rubric and explicit access/status disclosure |
| Assessment overfits a hidden solution | Feasibility and reconciliation gates, broad plausibility evidence, alternative-method calibration and no exact-allocation requirement |
| Costs are double-counted, disappear or are diluted | Unique ledger policy, recursive roll-forward checks, zero-pool controls and independent validation |
| Application becomes a chart gallery | Business-question-to-view mapping, intuitive graph exploration, lineage and explanation requirements, uncertainty and failure-state evidence |
| Students overclaim optimality | Controlled status vocabulary, bound/gap checks, report/app consistency checks and defence questions |
| AI-generated work is not understood | AI usage evidence, targeted technical defence, cited validation and ownership scoring |
| Private authoring artefacts leak | Allow-list release builder, signature scan and independent review |
| AI evaluation becomes inconsistent | Deterministic evidence first, structured scoring, pilot calibration and human review near boundaries |

## 20. Definition of done

CAP-001 is ready for controlled student release only when:

1. all 12 ADRs and assessment-policy decisions are approved;
2. the shared configuration drives or verifies every derived artefact;
3. all 25 raw-data contracts and all standard outputs validate;
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
   business question, evidence obligation or rubric criterion;
10. solver access, budgets, permitted methods and status language are fair and
    documented;
11. the student pack contains the necessary data, modelling, application, AI
    and defence support without leaking private authoring artefacts;
12. the AI reviewer examines feasibility and accounting evidence while
    allowing defensible alternative solutions;
13. AI scores are evidence-cited and material uncertainty is available for
    human moderation;
14. at least two pilot journeys complete without an undisclosed requirement;
15. the release manifest, hashes, row counts, commands and output contracts
    agree; and
16. the capstone owner, domain lead, optimisation lead, evaluation lead and
    technical reviewer sign the release.
