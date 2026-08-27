# CAP-001 Consultant Engagement and Assessment Design Contract

## Document control

| Field | Value |
|---|---|
| Purpose | Define what CAP-001 asks a candidate to decide, build, demonstrate and defend |
| Status | Frozen 1.0 — accepted WP8 design contract |
| Date | 27 August 2026 |
| Work package | WP8 — consultant engagement and assessment design |
| Governing sources | CAP-001 specification v0.3; common control standard v0.2; decision configuration v0.3.1; approved ADRs; accepted WP4–WP7 evidence |
| Inputs | Six accepted complete dataset packages; miniature fixture; raw and output contracts; accepted network, commercial, planning and viability decisions |
| Explicit non-scope | Student-release packaging, a reference optimiser, a prescribed reference allocation, a reference application, evaluator implementation and grading against an exact objective |

This document is the frozen authoring contract for WP9 and WP10. It does not
itself populate the student brief or alter the student release; those controlled
downstream changes must preserve the meaning fixed here.

## Requirement form

The student-facing engagement must read like a client brief. Except for the
controlled technical boundaries below, requirements must describe a user need,
an observable system behaviour or a decision outcome. They must not prescribe
classes, modules, endpoints, page names, database products, frontend frameworks,
deployment patterns or internal application architecture.

The controlled technical boundaries are limited to:

1. the explicit algebraic MILP or MINLP formulation required by CAP-001;
2. the data-handling instructions in §7, which protect history, integrity and
   reproducibility; and
3. the application-wide non-functional baseline in §8.

Assessment evidence and submission formats may be specified where an assessor
needs them to verify an outcome. They are evidence contracts, not instructions
to reproduce the author's implementation. When a functional requirement can be
met in materially different defensible ways, the candidate owns that design
choice.

## 1. Engagement outcome

Asterion Industrial Controls Group needs a decision-support capability for its
multi-tier supply chain. The consultant is asked to determine:

> What sourcing, shipment, production and inventory plan should Asterion use
> over the supplied 12-week planning horizon; how do recursive end-to-end cost,
> service and resilience affect that decision; and how should the decision
> change under a different complete dataset or an authorised policy
> configuration?

The expected outcome is not an isolated optimisation script. It is a
well-reasoned decision system comprising:

- an explicit algebraic MILP or MINLP formulation;
- a justified solution method and honest solver classification;
- independent physical and recursive-accounting validation;
- a configurable application through which a business user can inspect and
  visually explore the supply graph, edit data, publish a versioned data
  reality, apply authorised policy, solve against that version and understand
  the resulting trade-offs;
- an evidence-backed recommendation with limitations; and
- reproducible code, tests and run artefacts.

The candidate is acting as a consultant. They own the design and must be able to
defend why their system is mathematically valid, operationally useful and
appropriately cautious about uncertainty and optimality.

## 2. Planning and information semantics

Each supplied package is one complete deterministic planning case. The full
P01–P12 horizon, including dated disruptions and recoveries, is known when the
P01 plan is constructed. The optimiser produces a horizon-wide plan and may
therefore make advance commitments or position inventory for a later event.

A scenario is not a one-period allocation and is not information revealed
partway through execution. Surprise revelation, frozen decisions from an
earlier run, stochastic programming and non-anticipativity are outside the
required engagement.

The application must keep five kinds of state distinct:

```text
supplied/imported CSVs    -> starting extracts for 25 logical master tables
versioned master records -> effective-dated business facts and history
published dataset version -> resolved as-of state across all 25 masters
run-policy configuration -> authorised rules, preferences and overrides
solution-method settings -> formulation route, solver and runtime controls
```

Importing a supplied file creates an initial version of the records in its
logical master table. Create, update and delete operations append effective-
dated master-record versions rather than overwriting history. A published
dataset version resolves the applicable records from all 25 masters into one
complete as-of planning reality. A solve reads exactly one published dataset
version and rebuilds the model from it. Changing policy means changing a
separately versioned configuration. None of these actions permits silent
mutation of another, and an existing run must remain reproducible from its
recorded master-data, dataset, policy and method versions.

The supplied business data is leg-local. It may state an external boundary
quote, one contract, one lane, one transformation and its local value-add, the
rules applying to those facts, and opening inventory book value. It must never
supply an authoritative intermediate pool cost, cumulative path cost,
downstream landed cost or terminal end-to-end cost. Those are derived outcomes
that the candidate must calculate from the selected network decisions inside
their mathematical formulation. They are not a separate supplied or required
recursive-cost dataset.

BASE and SCN-01 through SCN-05 are supplied examples of coherent planning
conditions. They demonstrate the range of changes that the application must be
able to handle; they are not the complete set of scenarios that a user may
create and must not be hard-coded as such.

## 3. Intended users and decision rights

The primary users are Asterion's European supply-planning and category-
management teams. Senior operational and commercial stakeholders consume the
recommendation and approve material exceptions.

| Matter | System or consultant may | Required authority |
|---|---|---|
| Approved suppliers, materials, recipes and lanes | Enforce the selected dataset | Dataset owner |
| Demand, capacity, lead time, cost and opening stock | Optimise around the selected dataset | Dataset owner |
| Incoterm rules and active selection | View current and historical master records, perform governed CRUD and publish an effective dataset version | Commercial data owner |
| Other decision-relevant facts | Create, update or retire versioned master records and publish after validation | Relevant data owner |
| Sourcing, shipment, production and inventory quantities | Recommend through the formulation | Planning user |
| Quantitative resilience rule | Define, configure and compare | Planning or risk owner |
| Within-stage objective parameter | Configure and test within the controlled hierarchy | Planning owner |
| Approval or eligibility exception | Apply only when explicit, named, reasoned and authorised | Named commercial authority |
| Raw-data correction | Create a traceable successor record version; never rewrite historical evidence or an active run | Data owner |
| Optimality or solution-status claim | Report only what solver evidence supports | Consultant accountability |

An override is not a hidden modelling convenience. It must record the original
rule, effective rule, reason, authority, configuration version and affected
result.

## 4. Business questions the system must answer

The engagement must enable a business user to answer all of the following:

1. Can the supplied terminal demand be served over P01–P12, and where is
   service at risk?
2. What orders, shipments, transformations and inventory movements support the
   proposed plan across the multi-tier network?
3. How is a selected supplier, plant, material or demand point connected to the
   rest of the supply graph, and what lies upstream and downstream of it?
4. What is the recursively formed end-to-end value of served demand and closing
   inventory, and where is that value added?
5. Which capacities, approvals, lanes, materials, suppliers or shared resources
   constrain the decision?
6. Does the submitted BASE decision faithfully reproduce the published
   reference controls, and what explains any material aggregate differences?
7. When the complete dataset is replaced, what facts changed and what did the
   system consequently change in the horizon-wide plan?
8. If an Incoterm, price or other business fact is changed, which contracts,
   cost responsibilities, network choices and results are affected?
9. What resilience intervention is worth considering, and what cost, service,
   inventory and concentration trade-off does it create?
10. Which recommendation should Asterion adopt, under what dataset version and
    configuration, and with what caveats or operational follow-up?

The application and reports may answer several questions in one coherent view.
The assessment must not require a separate chart or page merely to satisfy an
inventory of labels.

## 5. Mandatory optimisation outcomes and technical boundary

### 5.1 Horizon-wide planning outcome

For any selected complete, published dataset version, the user must be able to
obtain a horizon-wide plan or an honest explanation of why no valid plan was
produced. Selecting one package must never cause the system to borrow missing or
convenient facts from BASE or another package. A new schema-valid dataset
identifier must work without a product change or special scenario mode.

The resulting plan must respect all applicable physical and commercial facts,
including approved flows, periods, lead times, capacity, production recipes,
yield, shared resources, MOQ and multiples, setup and activation, inventory,
storage, service, logistics and the controlled cost policy. The user must be
able to understand how those facts constrain the recommendation.

### 5.2 BASE reference benchmark

The user must be able to compare the submitted BASE decision with the published
BASE reference incumbent at a consistent service, objective-quality,
aggregate-plan and validation grain. The reference is public calibration
evidence. It is not a model input, prescribed allocation or global-optimality
claim. A different allocation can pass when it is independently valid, meets
the published controls and explains material aggregate differences.

### 5.3 Assessed recursive-cost route

The assessed economic semantics are the bounded recursive weighted-average
quantity-and-value pools defined by the specification and fixture. Every
claimed solution route must remain grounded in an explicit algebraic MILP or
MINLP formulation. This is a controlled technical boundary of the engagement,
not a prescription of application architecture.

All intermediate pool value, dispatched value, transformation value, receipt
value and terminal value must be derived by the candidate. No intermediate,
cumulative-path or end-to-end cost field may be treated as an authoritative
assessed-model input.

Pyomo, PuLP and other suitable algebraic modelling libraries are permitted.
The library is not assessed in itself. A candidate may use an exact, relaxed,
approximate or heuristic strategy around the formulation, provided that they:

- state the formulation and method classification accurately;
- preserve or explicitly identify any departure from required accounting and
  integer semantics;
- report the incumbent, bound or gap when available;
- validate feasibility and recursive accounting independently; and
- do not claim global optimality without supporting evidence.

### 5.4 Objective hierarchy

The controlled lexicographic order remains:

1. weighted shortage and service priority;
2. recursive served and closing value plus non-capitalised cost; and
3. surplus and unnecessary-activation tie-break.

Configuration may alter permitted within-stage parameters or add a declared
resilience rule. It may not silently dilute a higher-priority objective.

## 6. Supplied examples and open-ended scenario capability

BASE and SCN-01 through SCN-05 are examples, acceptance fixtures and useful
business cases. They are not a closed runtime enumeration. The application
must allow a user or assessor to provide another complete schema-valid dataset
version and receive the same supported behaviours without a product change.

The accepted assessment burden is:

| Evidence | Frozen minimum |
|---|---|
| Example compatibility | Import and validate all six supplied packages through one path |
| BASE decision | Submitted recursive result and faithful-reproduction evidence against the published BASE benchmark |
| Supplied-example analysis | Solve and compare at least two supplied stress examples selected and justified by the candidate |
| User-authored data reality | Use the application to create, validate and publish at least one materially changed dataset version |
| Versioned solve | Solve the user-authored version and compare it with its parent |
| Incoterm demonstration | Change Incoterm availability or responsibility in a draft, publish it and show its model and business consequence |
| Generality challenge | Accept an assessor-created schema-valid version whose identifier and changes were not hard-coded by the candidate |
| Resilience intervention | Test at least one quantitative policy against an unchanged published dataset version |
| Additional configuration | Compare at least one authorised override or within-stage parameter change without editing the dataset |

This makes the supplied scenarios instructional examples while directly
testing whether the application supports new business conditions. Stored
results may support expensive supplied-example comparisons only when they are
strictly version-pinned, visibly classified and stale-safe. The user-authored
version must include an application-launched solve.

## 7. Concrete technical data-handling instructions

### 7.1 Versioned master-data model

The supplied 25 CSV files are starting extracts from 25 logical master-data
tables. Each imported row must be associated with a record version that states
what business fact it represented and when that version was effective. The CSV
file itself is not the versioned object.

The application must preserve each supplied file unchanged as source evidence,
record its package identity, schema version and cryptographic hash, and import
its contents into persistent master-data storage. Version history, drafts,
published data and run lineage must survive an application-process restart.
Storage technology and internal schema design remain candidate choices.

Each logical master record must retain:

- a stable business key;
- an immutable record-version identifier;
- business-valid `effective_from` and `effective_to` values;
- an explicit active or retired state where applicable;
- the preceding version identifier, when one exists;
- recorded and superseded timestamps for audit history;
- author and reason for change;
- source import and schema version; and
- validation state.

The application must distinguish business-valid time from audit time. Business-
valid time answers which rule, price or capacity was intended to apply to a
planning date or period. Audit time answers when that version was entered or
superseded in the application.

The following conventions are mandatory:

- business-valid intervals use an inclusive `effective_from` and exclusive
  `effective_to`; a missing end means that the version remains effective;
- audit timestamps are recorded in UTC and retain their timezone;
- a stable business key is never reassigned to a different business fact;
- the current recorded view cannot contain overlapping effective intervals for
  the same business key; a retroactive correction preserves the superseded
  record in audit history;
- every successor identifies the record version it succeeds, and a stale or
  conflicting update must be rejected rather than silently winning;
- source evidence, superseded record versions and published dataset versions
  are append-only for the duration of the assessment; and
- referential, temporal and schema validation is enforced at the trusted data
  boundary rather than relying only on browser controls.

CRUD is version-preserving:

- **Create** adds the first version of a new business key.
- **Read** exposes current, historical and as-of versions.
- **Update** creates a successor and closes or supersedes the prior version; it
  does not overwrite it.
- **Delete** retires or end-dates the record from an effective point; it does
  not erase its history.

A published dataset version is a named, immutable as-of selection across all 25
logical masters. It records the master-record versions used, its parent dataset
version where applicable, author, publication time, purpose, validation result
and content hash. It must resolve to a complete cross-file-valid 25-table view
without reaching into BASE or another supplied scenario.

Publication must be atomic: either the complete validated selection becomes
available or no new published version is created. Its content hash must be
calculated by a documented deterministic procedure. A published version can be
withdrawn from future use, but its contents and lineage cannot be rewritten.
Exports must carry enough identity and version metadata for a clean instance of
the submitted application to reproduce the same resolved data.

Changing one cost at one point therefore creates a successor version of that
cost record and, once validated, a new published dataset version. Unchanged
master records retain their existing versions. Every solve records the exact
published dataset version and the resolved master-record-version set, together
with run-policy and method versions.

### 7.2 Mandatory Incoterm management

The application must display every current and historical Incoterm record in
the master `incoterms` table and provide governed create, read, update and
delete operations using the version-preserving semantics above. A user must be
able to:

- inspect the code, description, responsibility flags, risk-transfer stage,
  active state and affected contracts;
- create a valid uniquely identified Incoterm rule;
- edit its commercial-responsibility fields and active state;
- delete an unreferenced draft rule;
- deactivate or retire a referenced rule from an effective point without
  destroying history; and
- preview and compare the consequences before and after solving.

The revised raw-data contract requires an `active_flag` on Incoterm rules.
Effective contract eligibility requires both the contract and its referenced
Incoterm to be active. Deactivation must therefore affect the formulation rather
than acting as a display filter. Deleting a referenced rule is blocked by
referential validation; the user must instead deactivate it or update the
dependent contracts explicitly.

Changing carriage, insurance or duty responsibility changes the controlled
receipt-cost construction for contracts using that rule. The application must
show those affected relationships and must never present the simplified
Incoterm abstraction as legal guidance.

### 7.3 Other editable business facts

The data-authoring capability must not be a special-purpose editor for the five
supplied scenario patterns. At minimum, a user must be able to create successor
master-record versions and publish a dataset version containing valid changes
to forward cost, capacity, demand, logistics, contract/approval availability
and opening inventory facts. A valid new identifier or period target must be
accepted through the same user-facing behaviour as an existing one, without a
product change.

Before publication, the application must show:

- changed master records, versions and fields relative to the prior dataset;
- affected references and any invalid dependencies;
- the contracts, lanes, nodes, materials or periods directly touched;
- whether model reconstruction is required; and
- validation errors that block publication or solving.

After solving, it must compare the parent and successor dataset versions at a
consistent business and solver-evidence grain. This is the principal way users
visualise the impact of changing data.

## 8. Application-wide non-functional baseline

These are the only general implementation-quality constraints to be carried
into the client brief. They define the minimum credible quality of the product,
not its architecture. Candidates may choose their stack and demonstrate these
outcomes with proportionate tests, measurements, operational evidence and the
technical defence.

| Quality | Required outcome and frozen minimum |
|---|---|
| Product form and operability | The submission runs as an end-to-end application with an interactive business interface, persistent data handling and integrated solve/result behaviour. It is not a static report, notebook-only analysis or disconnected chart gallery. |
| Data integrity and durability | Committed changes, audit history and published versions survive restart. Publication is atomic, failed writes leave no partial business state, and a run never changes the data it consumed. |
| Security and authority | All imported and edited values are validated at the trusted boundary. Mutating data, publishing versions and applying overrides enforce the declared authority model. Secrets are excluded from source, exports and logs. |
| Accessibility and usability | Core journeys target WCAG 2.2 AA: they are keyboard operable, have programmatic labels and visible focus, do not rely on colour alone, and present errors with an actionable explanation. No formal certification is required. |
| Interactive responsiveness | On the declared assessment environment, ordinary non-solver interactions acknowledge or complete within two seconds. Longer imports, validation and solve work remain non-blocking and expose progress or state rather than appearing frozen. Solver duration is reported separately. |
| Failure safety | Invalid, stale, infeasible, interrupted and failed states are visible and cannot be mistaken for a current valid recommendation. A user can recover or retry without losing the last committed state. |
| Auditability and observability | Data changes, publication, policy changes and solve runs record who or what acted, when, against which versions, and with what outcome. Logs and application status provide a common run or operation identifier without leaking secrets. |
| Reproducibility and portability | A fresh assessor environment can install, initialise, import, test and run the submitted product using declared commands and locked dependencies. A documented backup/export and restore/import journey reproduces a published version and its lineage. |
| Supported presentation environment | The candidate declares the supported browser and viewport. All core business journeys must work in a current Chromium-based desktop browser at 1280 × 720 without loss of essential information; broader responsive support may be demonstrated but is not mandatory. |

The two-second interaction target does not impose a solver-time target and does
not require a synchronous solve. Security is assessed as a credible capstone
control, not as production penetration certification. The candidate should
state material limitations and the controls that would be strengthened before
production use.

## 9. Configuration outcomes

The user must be able to select and understand a versioned policy configuration
independently of the selected data. The application must:

- enforce dataset approvals and eligibility by default;
- support a candidate-defined quantitative resilience intervention;
- support meaningful parameters without editing raw data or source code;
- reject unauthorised overrides before model construction;
- show the active dataset version/hash and configuration version/hash with
  every result;
- make the original and effective rule visible when an override is authorised;
  and
- ensure reports, exports and application views refer to the same configuration.

The candidate owns the choice and justification of resilience measure. CAP-001
does not prescribe a concentration formula or preferred intervention.

Data edits and policy configuration are not interchangeable. Changing an
Incoterm, cost, capacity or demand creates a dataset version. Changing risk
appetite, an objective parameter or an authorised exception creates a policy
configuration version.

## 10. Validation outcomes

Validation is part of the user outcome, not a post-hoc assertion. Before a
recommendation is presented as valid, the application and submitted evidence
must enable a user and assessor to determine whether it satisfies:

- schema, key, domain, unit and cross-file integrity;
- the miniature fixture and published reconciliation totals;
- physical balances, timing, capacity, approvals, MOQ, storage and service;
- quantity, value and unit-cost roll-forward at every active pool;
- common outflow cost, zero-pool behaviour and anti-dilution;
- in-model recursive calculation without a dedicated recursive-cost or
  equation-grain value-reconciliation file;
- exactly-once ledger classification and markup eligibility;
- exclusion of precomputed intermediate, cumulative-path and end-to-end cost inputs;
- integrality and formulation bounds where applicable;
- dataset-version lineage, Incoterm CRUD and referential integrity;
- publication-state controls and immutability of source/published versions;
- arbitrary valid dataset replacement, state reset and configuration
  provenance;
- reported metric and application-view consistency; and
- at least one deliberately failing or adversarial case relevant to the
  product's claimed behaviour.

Passing the miniature fixture does not prove that the full plan is correct. It
proves that the accounting semantics are understood before they are applied at
scale.

## 11. Application outcome and user journeys

The assessed product must let a business user complete the required journeys in
a runnable decision-support application. It may solve live, submit an
asynchronous job or retrieve controlled stored results, but the user must always
be able to see the relevant state and provenance.

The application must support these user journeys:

1. Import a complete package as starting record versions in 25 logical master
   tables, or select an existing published dataset version and inspect its
   identity, resolved master-record versions, lineage, publication state and
   validation.
2. Explore the selected published or draft dataset as an intuitive visual
   supply graph: locate a business entity, traverse its upstream and downstream
   relationships and inspect the business facts attached to relevant nodes and
   connections.
3. Create draft successor versions of master records and inspect their complete
   effective-dated and audit history relative to the selected parent dataset.
4. View all Incoterm records and perform governed CRUD, including selection of
   active terms and visibility of affected contracts.
5. Edit other supported business facts, preview affected relationships,
   validate the draft master-record versions and publish an immutable successor
   dataset version.
6. Inspect and version the active policy configuration, including any authority
   required for an override.
7. Select a published dataset version and policy version, start or retrieve a
   run, and see job, solver, formulation and result status.
8. Inspect the horizon-wide plan across sourcing, logistics, production,
   inventory and service.
9. Relate authored data changes and solve results back to the affected parts of
   the supply graph.
10. Trace recursive cost and material lineage from terminal demand to external
   sources and value-add stages.
11. Compare the submitted BASE result with the published reference, parent and
    successor datasets, and policy configurations at a consistent grain.
12. Inspect binding constraints, residuals, failed checks, uncertainty and stale
    or failed result states.
13. Produce a decision summary connecting data changes, evidence, trade-offs,
    recommendation and limitations.

These are behaviours, not mandated screen names. A candidate may combine them
into a smaller number of well-designed views. The application must make clear
which evidence is a business result and which evidence describes how the
system produced or validated it. CAP-001 does not prescribe a graph library,
layout algorithm, visual encoding or interaction pattern. The assessed outcome
is whether a business user can orient themselves in the multi-tier supply
structure, follow relevant relationships and connect the graph to the selected
data version, its changes and the resulting decision.

## 12. Two-level explanation contract

Every material scenario or policy explanation must cover two distinct levels:

| Explanation level | Required content |
|---|---|
| Business and data | The parent-to-successor data changes, affected network exposure, service/cost/inventory/resilience consequence and recommended action |
| System interaction | Dataset-version lineage, configuration identity, affected model constructs, active gates or overrides, solver status, validation evidence and reason the decision changed |

A statement such as "cost increased" is insufficient without the business
mechanism. A technically detailed solver narrative is also insufficient if it
does not explain the decision consequence.

## 13. Evidence and deliverables

The candidate must submit enough evidence for an assessor to reproduce,
validate and challenge the work. The controlled deliverables remain:

- runnable source code and locked dependencies;
- automated tests and declared setup, test, model and application commands;
- model specification and solver-strategy report;
- validation and assumptions/limitations reports;
- standard machine-readable run and solution artefacts;
- machine-readable master-record version history, dataset-version manifests,
  resolved record-version sets and parent-to-successor change sets;
- the interactive application and controlled application evidence;
- a resilience recommendation and decision summary;
- a production-readiness note;
- a 10–12 slide client presentation;
- AI-usage disclosure; and
- participation in a 20–30 minute technical defence.

The current thirteen output contracts must be reorganised according to the
frozen application and evidence contract: per-run core evidence,
per-recursive-run evidence and once-per-comparison-set evidence.
`scenario_comparison.csv` becomes dataset/configuration comparison evidence and
`scenario_results.csv` is retired. No output survives merely because a schema
already exists.

Existing run metadata must be extended so that outputs identify an arbitrary
published dataset version and its resolved master-record-version set rather
than relying on a closed six-value scenario enum.

## 14. Assessment design

### 14.1 Quality gates before scoring

Deterministic gates precede qualitative scoring. At minimum:

- the declared commands and application run in the controlled environment;
- the selected input is complete, read-only and hash-identifiable;
- the selected input is a published immutable dataset version with a complete,
  reproducible as-of selection across all 25 logical master tables;
- Incoterm edits and activity changes pass referential and commercial-semantic
  validation;
- an independently validated BASE result and benchmark-reproduction record are
  present;
- hard physical, approval and integrality rules pass;
- recursive quantity and value accounting reconciles within tolerance;
- ledger uniqueness, zero-pool and derived-intermediate-input isolation controls
  pass;
- required dataset-version and configuration evidence is present;
- solver status and optimality language match the evidence; and
- machine outputs, reports and application views do not contradict one another.

WP8 defines and freezes the gate and evidence meaning. WP10 assessment
governance owns the calibrated score, resubmission and failure consequences.

### 14.2 Rubric

The existing 100-point structure is the frozen WP8 basis:

| Category | Points | Principal judgement |
|---|---:|---|
| Business framing and user value | 8 | Decision clarity, user need and material recommendation |
| Data understanding and preparation | 8 | Tier-N relationships, governed data authoring, version lineage and package/configuration separation |
| Mathematical formulation | 16 | Explicit and complete physical, recursive-value, objective and bound semantics |
| Method selection and implementation | 14 | Fit-for-purpose strategy, honest classification and controlled implementation |
| Validation, benchmarking and robustness | 15 | Independent evidence, fixture, failure cases, reconciliation and scenario/configuration testing |
| Interactive application | 14 | Intuitive visual supply-graph exploration, Incoterm CRUD, dataset versioning, coherent user journeys, interpretability, provenance and failure handling |
| Software engineering and reproducibility | 10 | Maintainability, configuration, tests, dependencies, commands, non-functional quality and observability |
| Presentation and recommendation | 7 | Evidence-backed client narrative, trade-offs and appropriate claims |
| Production readiness and limitations | 5 | Integration, security, scale, monitoring, fallback and limitations |
| Technical defence | 3 | Demonstrated ownership of formulation, implementation and AI-assisted work |
| **Total** | **100** | |

Full credit must be available to materially different valid formulations and
solution strategies. No criterion scores proximity to a private allocation or
exact expected objective.

### 14.3 Technical defence

The defence samples ownership rather than memory. It should ask the candidate
to explain or modify selected evidence involving:

- one physical balance and one recursive value pool;
- one cost-capitalisation or markup decision;
- one upstream or downstream supply-graph exploration from a selected entity;
- one Incoterm or other data edit from draft through published solve;
- the submitted BASE result versus the published reference controls;
- one scenario or configuration-induced decision change;
- solver status, gap, bounds and limitations;
- one failed or adversarial test; and
- one material AI-assisted contribution that was checked, corrected or
  rejected.

## 15. Explicit non-requirements

The engagement does not require candidates to:

- reproduce an author allocation, exact objective or preferred policy;
- use `cap001_model`, Pyomo, HiGHS or IPOPT specifically;
- use a prescribed database, persistence product, web framework, component
  structure or deployment pattern;
- prove global optimality for the non-convex recursive formulation;
- build separately named application pages for every required user journey;
- use a prescribed graph library, layout, visual encoding or interaction
  technique;
- solve live inside a web request when controlled asynchronous or stored-result
  behaviour is more appropriate;
- provide production identity federation, penetration certification, high
  availability infrastructure or mobile support beyond the §8 baseline;
- model unexpected mid-horizon revelation;
- copy the author's private viability probes; or
- conceal an infeasible, local, approximate, time-limited or failed result.

The application itself must not be limited to the six supplied identifiers and
must not rewrite imported master-record history or mutate a published dataset
version in place.

## 16. Frozen decision record and downstream handoffs

The capstone owner accepts the following WP8 positions:

1. import and validate all six supplied packages, reproduce BASE, analyse at
   least two justified supplied stress examples and solve one user-authored
   version;
2. attempt an application-launched recursive route for an assessor-created
   dataset without requiring success or global optimality;
3. version and expose all 25 masters, while requiring governed authoring for
   Incoterms and the decision-material cost, capacity, demand, logistics,
   contract/approval and opening-inventory facts;
4. permit new schema-valid Incoterm abstractions with unique codes and full
   effective-dating, authority, history and referential controls;
5. make `STRESS_ONLY` optional;
6. demonstrate resilience, one within-stage sensitivity and both a rejected and
   an authorised override;
7. permit synchronous, asynchronous or strictly version-pinned, stale-safe
   stored results, while requiring live data journeys and at least one
   application-launched user-authored solve;
8. reorganise run evidence by purpose, replace closed scenario comparisons with
   dataset/configuration comparisons and retire `scenario_results.csv`;
9. freeze the two-second non-solver interaction target and current Chromium at
   1280 x 720 presentation minimum;
10. permit documented role simulation with trusted-boundary enforcement and
    audit evidence; and
11. hand score caps, grade-boundary rules, resubmission, partial credit and
    calibration to WP10 assessment governance without changing WP8 gate
    meanings.

CN-004 and CN-005 already completed the controlled removal of derived-cost
inputs and dedicated recursive-cost outputs and published the solved BASE
benchmark. The following older control artefacts require WP9 alignment:

- `config/cap001_decision_config.json` does not yet state the P01 full-horizon
  information assumption as a machine-readable planning rule;
- the configuration and output schemas currently treat the six supplied
  scenario identifiers as a closed enum rather than examples;
- `incoterm_rules.csv` has no `active_flag`, restricts codes to the current six
  terms and has no effective-dated master-record version contract;
- the current dataset manifest records file hashes but does not identify the
  resolved effective master-record versions, parent or published as-of dataset
  version;
- run metadata records a scenario ID and input hash but not the published
  dataset-version lineage required by this design; and
- `CAP-001_REQUIREMENTS_TRACEABILITY_MATRIX.md` repeats those superseded
  scenario facts and the former 23-gate WP6 state.

The accepted package data, ADR-008 clarification, CN-004/CN-005 changes and
WP6/WP7 evidence govern the intended position. Correcting shared configuration
and schemas requires controlled versioning and regeneration rather than an
undocumented text edit. ADR-010 is handed to WP9 for accessible solver routes
and assessment-environment budgets; ADR-012 is handed to WP10 for calibrated
assessment consequences and defence workflow.

## 17. Progress gates

1. **Engagement framed — passed:** client, users, decision rights, planning
   semantics and business questions are stated.
2. **Candidate obligations bounded — passed:** concrete data controls, the
   application-wide non-functional baseline and the mandatory formulation are
   separated from functional outcomes and candidate-owned design choices.
3. **Assessment burden approved — passed:** dataset runs, output artefacts and
   narrative depth are proportionate and solver-accessible.
4. **Evidence and rubric aligned — passed:** every obligation maps to a quality
   gate, rubric criterion or defence prompt without duplicate burden.
5. **Owner accepted — passed:** the contract is frozen as the controlled basis
   for student-brief, task-requirement and release work in WP9.
