# CAP-001 Candidate Task Requirements

## 1. Requirement interpretation

`Must` denotes a required outcome. Functional requirements describe what a
user can achieve or observe. The only prescriptive technical requirements are
the explicit formulation boundary in §3, the data-handling controls in §4 and
the application-wide non-functional baseline in §5.

Requirement identifiers are stable within this release and map to business
purpose, evidence and rubric criteria. No identifier
implies a required page, endpoint, class, database, framework or deployment
topology.

### 1.1 Principal deliverable

The candidate must design, build, submit and defend a working end-to-end
full-stack decision-support application for Asterion. The application must
combine:

- an interactive interface through which the intended business users can
  complete the required journeys;
- persistent, governed data and version handling;
- an integrated algebraic MILP or MINLP optimisation workflow; and
- interpretable results, validation evidence and decision support within the
  application.

The application is the principal deliverable. A model accompanied only
by scripts, notebooks, an API, static charts or reports is insufficient.
Interface mock-ups or disconnected demonstrations of these capabilities are
also insufficient.

The candidate chooses the architecture, technologies and internal structure.
This freedom concerns how the application is built; it does not make building
the application optional.

## 2. Functional requirements

### 2.1 Data reality and authoring

| ID | Required outcome |
|---|---|
| CAP-F-001 | A user can import a complete 25-table dataset, inspect its identity and validation state, and select a published version without fallback to another package. |
| CAP-F-002 | A user can distinguish source imports, current and historical master records, drafts, published dataset versions, policy configurations and solve runs. |
| CAP-F-003 | A user can inspect changes between a draft or successor dataset and its parent, including affected records, fields, references, graph relationships and periods. |
| CAP-F-004 | A user can resolve blocking validation errors and publish a complete immutable dataset version for later selection and comparison. |
| CAP-F-005 | A user can supply another complete schema-valid dataset whose identifier and changes were not built into the product and receive the same supported behaviours. |
| CAP-F-006 | A user can create valid changes to at least forward cost, capacity, demand, logistics, contract or approval availability, and opening inventory without requiring a product change for a new valid identifier or period target. |

### 2.2 Incoterms

| ID | Required outcome |
|---|---|
| CAP-F-007 | A commercial data owner can view every current and historical Incoterm rule, including its code, description, responsibility fields, risk-transfer stage, effective state and affected contracts. |
| CAP-F-008 | A commercial data owner can create, inspect, revise, activate, deactivate and retire Incoterm rules subject to authority, history and referential validation. |
| CAP-F-009 | Before publication, a user can see which contracts and cost responsibilities an Incoterm change affects. After solving, the user can see its effect on eligible relationships, cost construction and the recommendation. |
| CAP-F-010 | A user cannot erase the history of a referenced Incoterm or silently leave a contract using an inactive or ineffective rule. |

### 2.3 Supply-graph exploration

| ID | Required outcome |
|---|---|
| CAP-F-011 | A user can explore the selected published or draft data as an intuitive visual supply graph. |
| CAP-F-012 | A user can locate a supplier, node, plant, material or demand point and traverse relevant upstream and downstream relationships. |
| CAP-F-013 | A user can inspect business facts associated with relevant graph entities and connect authored changes and solve results to affected graph elements. |

The candidate chooses the graph technology, layout, visual encoding and
interaction model. The result must let the user understand the supply
structure and decision; no preferred visual design is prescribed.

### 2.4 Configuration and authority

| ID | Required outcome |
|---|---|
| CAP-F-014 | A user can select and inspect a versioned policy configuration independently of the selected dataset version. |
| CAP-F-015 | A planning or risk owner can define and compare at least one quantitative resilience intervention without rewriting the dataset. |
| CAP-F-016 | A user can vary at least one meaningful permitted within-stage objective parameter and understand its effect without changing source code or business data. |
| CAP-F-017 | An approval or eligibility exception can take effect only when its original rule, effective rule, reason, authority, configuration version and affected result are visible and recorded. |

### 2.5 Planning and decision

| ID | Required outcome |
|---|---|
| CAP-F-018 | For a selected published dataset and policy configuration, a user can request or retrieve a horizon-wide P01–P12 plan or an honest explanation of why no valid plan was produced. |
| CAP-F-019 | The plan respects applicable approvals, periods, lead times, capacity, recipes, yield, shared resources, MOQ and multiples, setup and activation, inventory, storage, service, logistics and commercial policy. |
| CAP-F-020 | A user can compare the submitted BASE result with the published BASE reference benchmark at a consistent service, objective-quality, aggregate-plan and validation grain. |
| CAP-F-021 | A user can inspect sourcing, orders, shipments, transformations, inventory and service over the complete planning window. |
| CAP-F-022 | A user can identify material constraints, bottlenecks, approval gates and demand at risk, and understand their effect on the recommendation. |
| CAP-F-023 | A user can trace material and recursively accumulated value from terminal demand and closing inventory back through relevant receipts, transformations and external sources. |
| CAP-F-024 | A user can compare parent and successor datasets or two policy configurations at a consistent business and solver-evidence grain. |
| CAP-F-025 | A user can distinguish a valid current result from a draft, queued, running, stale, infeasible, interrupted, failed, local, approximate or time-limited result. |
| CAP-F-026 | A user can produce a decision summary that connects the selected versions, data and policy changes, plan, validation, trade-offs, recommendation, authority needs and limitations. |

### 2.6 Supplied examples and generality

| ID | Required outcome |
|---|---|
| CAP-F-027 | All six supplied packages can be imported and validated through the same user-facing capability. |
| CAP-F-028 | BASE can be reproduced through the submitted recursive-value route and compared with the published reference controls without treating the reference allocation as a model input or unique answer. |
| CAP-F-029 | A user can solve and compare selected supplied stress examples as complete P01-known planning realities. |
| CAP-F-030 | A user can author, validate, publish, solve and compare at least one materially changed data reality not limited to a supplied scenario transformation. |
| CAP-F-031 | A user can apply a policy intervention to an unchanged published dataset and distinguish that comparison from a data change. |

The candidate must solve and analyse at least two supplied stress examples of
their choice and justify why those examples are decision-material. Controlled
stored results may support expensive supplied-example comparisons when they
are version-pinned and stale-safe. The user-authored dataset journey in
`CAP-F-030` must include an application-launched solve.

## 3. Mathematical formulation boundary

| ID | Required technical outcome |
|---|---|
| CAP-M-001 | The submitted decision method is grounded in an explicit algebraic MILP or MINLP formulation. A formulation-free optimiser or opaque scoring routine does not satisfy the engagement. |
| CAP-M-002 | The submitted recursive-value route reproduces the published BASE reference service and objective-quality controls within the benchmark contract. A different independently valid allocation may pass, and the reference solution must not be used as a model input. |
| CAP-M-003 | The submitted decision route represents the bounded recursive weighted-average quantity-and-value pools and exactly-once cost treatment defined by the specification, fixture and cost policy. |
| CAP-M-004 | The objective applies the controlled lexicographic order: weighted shortage and service priority; served and closing recursive value plus non-capitalised cost; then surplus and unnecessary-activation tie-break. |
| CAP-M-005 | All material decision variables and nonlinear or integer relationships have finite, justified bounds consistent with the supported data. |
| CAP-M-006 | The candidate classifies the formulation and solution method honestly and reports incumbent, bound, gap and limitations where available. Global optimality may be claimed only when the evidence supports it. |
| CAP-M-007 | Exact, relaxed, approximate or heuristic workflows around the formulation are permitted when departures from accounting or integer semantics are identified and independently validated. |

Pyomo, PuLP and other suitable algebraic modelling libraries are permitted.
The library, solver and decomposition pattern are candidate choices subject to
the declared environment, access and evidence constraints.

The controlled benchmark is supplied under `reference/base_benchmark/`.
`benchmark_contract.json` defines the reproduction rules and
`reference_solution.json` supplies replayable result evidence. Neither file is
a model input.

## 4. Concrete technical data-handling requirements

| ID | Required technical treatment |
|---|---|
| CAP-D-001 | Preserve every supplied CSV unchanged as source evidence and record its package identity, schema version and cryptographic hash. |
| CAP-D-002 | Import supplied rows into persistent logical master-data storage. Source evidence, drafts, version history, publication state and run lineage must survive an application-process restart. |
| CAP-D-003 | Associate every logical master record with a stable business key, immutable record-version identifier, effective interval, audit timestamps, author, reason, predecessor where applicable, source/schema identity and validation state. |
| CAP-D-004 | Treat `effective_from` as inclusive and `effective_to` as exclusive; a missing end is open-ended. Record audit timestamps in UTC with timezone. |
| CAP-D-005 | Distinguish business-valid time from audit time. The current recorded view must not contain overlapping effective intervals for the same key, while superseded and retroactively corrected versions remain in audit history. |
| CAP-D-006 | Implement CRUD as version-preserving behaviour: create a first version, read current/history/as-of state, update by successor, and delete by retirement or end-dating rather than historical erasure. |
| CAP-D-007 | Require each successor to identify its predecessor and reject stale or conflicting writes rather than silently accepting the last writer. |
| CAP-D-008 | Enforce schema, referential, temporal and authority validation at the trusted data boundary rather than relying only on browser controls. |
| CAP-D-009 | Publish atomically. A published dataset version is an immutable, complete as-of selection across all 25 logical masters with parent, author, time, purpose, validation result, resolved record versions and deterministic content hash. |
| CAP-D-010 | Permit a published version to be withdrawn from future selection without rewriting its content or lineage. |
| CAP-D-011 | Pin every solve to the exact published dataset version, resolved master-record versions, policy version and solution-method settings used. A run must never change when a master record later changes. |
| CAP-D-012 | Export enough data and lineage metadata for a clean instance of the submitted application to reproduce the same published version. |
| CAP-D-013 | Retain an explicit active state for each Incoterm rule. A contract is eligible only when both it and its effective Incoterm are active; a referenced rule is retired or end-dated rather than erased. |
| CAP-D-014 | Treat model cost data as leg-local facts only. No model input may provide an authoritative intermediate pool cost, cumulative path cost, downstream landed cost or terminal end-to-end cost. Derive all such values inside the mathematical formulation; do not require or produce a dedicated recursive-cost or equation-grain value-reconciliation file. |

The candidate may choose the storage technology and internal schema. These
requirements define data semantics and integrity, not a prescribed database
design.

## 5. Application-wide non-functional requirements

| ID | Required quality outcome |
|---|---|
| CAP-N-001 | The submission runs end to end with an interactive business interface, persistent data handling and integrated solve/result behaviour. It is not a notebook-only analysis or disconnected chart gallery. |
| CAP-N-002 | Committed data changes, audit history and published versions survive restart; failed writes leave no partial published business state. |
| CAP-N-003 | Mutating data, publishing versions and applying overrides enforce the declared authority model. Secrets must not appear in source, exports or logs. |
| CAP-N-004 | Core user journeys target WCAG 2.2 AA: keyboard operation, programmatic labels, visible focus, no colour-only meaning and actionable error explanations. Formal certification is not required. |
| CAP-N-005 | In the declared operating environment, ordinary non-solver interactions acknowledge or complete within two seconds. Longer work remains non-blocking and exposes progress or state. Solver duration is reported separately. |
| CAP-N-006 | Invalid, stale, infeasible, interrupted and failed states cannot be mistaken for a current valid recommendation; the user can recover or retry without losing the last committed state. |
| CAP-N-007 | Data changes, publication, policy changes and solve runs record actor, time, input versions and outcome. Application state and logs share a run or operation identifier without leaking secrets. |
| CAP-N-008 | A fresh environment can install, initialise, import, test and run the product using declared commands and locked dependencies. |
| CAP-N-009 | Backup/export and restore/import reproduce a published dataset version and its lineage. |
| CAP-N-010 | All core journeys work in a current Chromium-based desktop browser at 1280 × 720 without loss of essential information. The candidate declares the supported browser and viewport. |

These responsiveness and presentation minimums are the release baseline.
Production identity federation, penetration certification, high availability
and mobile support are not required.

## 6. Validation outcomes

| ID | Required outcome |
|---|---|
| CAP-V-001 | A user or independent reviewer can determine whether the selected dataset satisfies schema, key, domain, unit, currency, period, temporal and cross-table integrity. |
| CAP-V-002 | The submitted method reproduces the miniature fixture's published physical and recursive-value controls within the controlled tolerances. |
| CAP-V-003 | Independent evidence reconciles physical balance, timing, capacity, approvals, MOQ, storage and service for each claimed valid run. |
| CAP-V-004 | Independent evidence reconciles quantity, value and unit cost at every active pool and detects zero-pool, common-outflow-cost and artificial-dilution failures. |
| CAP-V-005 | Independent evidence shows that every realised cost is classified exactly once, markup eligibility is respected and no precomputed intermediate, cumulative-path or terminal end-to-end cost enters recursive valuation. |
| CAP-V-006 | Dataset, policy, method and run lineage is complete enough to reproduce every claimed result. |
| CAP-V-007 | Reports, exports and application views agree at a consistent grain and use solver-status language supported by evidence. |
| CAP-V-008 | At least one deliberately invalid or adversarial case demonstrates that a material claimed control fails safely. |

Passing the miniature fixture demonstrates understanding of the accounting
semantics; it does not by itself establish that a full planning result is
correct.

## 7. Candidate-owned choices

Subject to the requirements above, the candidate owns:

- application architecture, database product, framework and deployment pattern;
- graph visual design and interaction pattern;
- algebraic modelling library and compatible solver workflow;
- exact, relaxed, approximate or heuristic strategy around the formulation;
- quantitative resilience measure and proposed intervention;
- arrangement of user journeys into views;
- live, asynchronous or controlled stored-result behaviour; and
- additional tests, sensitivities and decision evidence used to strengthen the
  recommendation.

Different defensible designs must be able to earn full credit. No candidate is
required to reproduce a private author application, allocation, exact objective
value or preferred resilience policy.
