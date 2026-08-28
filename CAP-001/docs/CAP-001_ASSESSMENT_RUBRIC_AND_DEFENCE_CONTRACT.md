# CAP-001 Historical Assessment Rubric and Technical Defence Contract

> **Superseded on 27 August 2026.** This WP8 design record is retained for
> decision history only. Its deterministic quality gates, evaluator workflow
> and defence prompt bank do not govern candidate assessment. The published
> rubric is `docs/CAP-001_CANDIDATE_ASSESSMENT_RUBRIC.md`; assessor-side review
> is governed by
> `evaluation/AI_SUBMISSION_REVIEW_SYSTEM_PROMPT.md` under the
> WP9 professional release contract 1.1.

## Document control

| Field | Value |
|---|---|
| Purpose | Preserve the superseded WP8 assessment design decision for audit history |
| Status | Historical — superseded by WP9 professional release contract 1.1 |
| Date | 27 August 2026 |
| Candidate requirements | `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md` |
| Evidence contract | `docs/CAP-001_APPLICATION_AND_EVIDENCE_CONTRACT.md` |

## 1. Assessment principles

CAP-001 assesses the quality of a consultant's decision system and reasoning. It
does not assess proximity to a hidden allocation, private objective value,
preferred application design or prescribed resilience policy.

Assessment follows this order:

1. establish whether required evidence is runnable and internally identifiable;
2. apply deterministic quality gates to claimed data and results;
3. score the quality of formulation, method, product, evidence and business
   recommendation;
4. use technical defence to test ownership and resolve material uncertainty;
5. route contradictions, low confidence and boundary cases to human review.

Alternative formulations and solution strategies can earn full credit when
they satisfy the controlled semantics and are classified honestly. A feasible,
time-limited or approximate result may support strong work; an unsupported
claim of optimality may not.

## 2. Quality-gate vocabulary

Each gate records one of:

- **PASS** — the required evidence exists and the deterministic control passes;
- **FAIL** — the evidence establishes a material violation;
- **NOT_EVIDENCED** — the candidate claims the outcome but supplies
  insufficient usable evidence; or
- **NOT_APPLICABLE** — permitted only where the contract explicitly excludes
  the evidence for that run type.

The evaluator records the affected run, input versions, recomputation evidence
and materiality. A displayed pass flag never overrides independent failure
evidence.

## 3. Deterministic quality gates

| Gate | Deterministic question | Minimum evidence |
|---|---|---|
| CAP-G-01 Operability | Do declared installation, test, model and application commands run in the controlled environment? | Clean-run record, locked dependencies and declared commands |
| CAP-G-02 Data identity and publication | Is the selected input a complete immutable published version with reproducible source and master-record lineage across all 25 logical tables? | Source hashes, dataset manifest, resolved record versions and validation |
| CAP-G-03 Formulation boundary | Is each claimed decision route grounded in an explicit algebraic MILP or MINLP with its method classification disclosed? | Model specification, generated model statistics or equivalent inspectable evidence and run metadata |
| CAP-G-04 BASE reference reproduction | Does the submitted BASE run independently pass physical and recursive-value validation and meet the published service and objective-quality controls without consuming the reference solution as model input? | Candidate BASE run bundle, benchmark contract and reproduction evidence |
| CAP-G-05 Physical feasibility | Do balance, timing, approval, capacity, MOQ/multiples, setup, storage, service, integrality and bound checks pass for each result claimed as valid? | Standard run artefacts and independent recomputation |
| CAP-G-06 Recursive value | Do quantity, value and common unit-cost roll-forwards reconcile at every active pool within controlled tolerance? | Recursive reconciliation and independent recomputation |
| CAP-G-07 Cost ledger | Is every realised cost treated exactly once with correct capitalisation and markup eligibility and no precomputed intermediate-cost leakage? | Cost ledger, policy resolution and adversarial checks |
| CAP-G-08 Run lineage | Can the selected dataset, resolved records, policy, method, solver and outputs reproduce each material claim? | Run metadata, hashes, logs and restore/rerun evidence |
| CAP-G-09 Functional product | Can the user complete the controlled data, Incoterm, graph, configuration, solve, comparison, failure and decision journeys? | Running application and controlled demonstrations |
| CAP-G-10 Generality and state reset | Can the product handle a valid unseen dataset identity without fallback, scenario-specific behaviour or stale state? | Assessor dataset probe and before/after state evidence |
| CAP-G-11 Cross-channel consistency | Do application views, standard outputs, reports, presentation, solver status and optimality language agree? | Recomputed values and cross-artefact comparison |

Application-wide non-functional requirements contribute to rubric scoring.
Where a failure also destroys data integrity, authority, reproducibility or the
validity of a recommendation, it is recorded against the relevant gate above.

WP10 assessment governance must approve the score, cap, resubmission or non-
submission consequence for each `FAIL` or `NOT_EVIDENCED` result. WP8 freezes
the gate meanings and evidence tests but does not invent those policy
consequences.

## 4. Rubric structure

The frozen WP8 rubric framework totals 100 points.

| Category | Points | Principal judgement |
|---|---:|---|
| Business framing and user value | 8 | Does the submission turn the supplied reality into a clear, material and usable client decision? |
| Data understanding and preparation | 8 | Does the candidate understand, govern and explain the multi-tier data, version lineage and relationship semantics? |
| Mathematical formulation | 16 | Is the explicit MILP/MINLP mathematically complete and faithful to physical, recursive-value and objective semantics? |
| Method selection and implementation | 14 | Is the disclosed solution strategy appropriate, controlled and honest about status, bounds, gaps and departures? |
| Validation, benchmarking and robustness | 15 | Does independent evidence establish what works, expose what fails and support the strength of the claims made? |
| Interactive application | 14 | Can a business user govern data, explore the graph, configure, solve and interpret decisions and failures coherently? |
| Software engineering and reproducibility | 10 | Does the product operate reliably, meet the proportionate NFRs and reproduce from a clean environment? |
| Presentation and recommendation | 7 | Is the client narrative concise, evidence-backed and explicit about action and trade-offs? |
| Production readiness and limitations | 5 | Does the candidate identify credible integration, security, scale, monitoring, recovery and limitation considerations? |
| Technical defence | 3 | Does the candidate demonstrate ownership of the formulation, evidence, product decisions and AI-assisted work? |
| **Total** | **100** | |

## 5. Common category standard

Assessors apply the following standard within each category rather than looking
for one preferred implementation:

| Performance | Interpretation |
|---|---|
| Excellent | Complete, internally consistent and independently supported; connects technical choices to material business outcomes; anticipates limitations and challenge. |
| Strong | Correct and well supported across the material scope, with minor omissions that do not change the decision or claimed validity. |
| Adequate | Meets the central obligation and supports a usable conclusion, but explanation, coverage, evidence or robustness is uneven. |
| Limited | Partial capability or plausible narrative with material gaps, weak validation, unclear ownership or unsupported conclusions. |
| Insufficient | Missing, unusable, contradictory, materially invalid or concealed failure. |

Point-level descriptors and any gate-related score caps are a WP10 policy and
calibration activity. They must preserve the WP8 category meanings and cannot
introduce a hidden allocation test.

## 6. Category evidence and judgement

### 6.1 Business framing and user value — 8 points

Strong evidence identifies the decision, users, authority boundaries and the
operational consequence of acting or not acting. The recommendation prioritises
material findings rather than narrating every output. Data changes, service,
cost, inventory and resilience are connected to action and caveats.

Weak evidence restates charts, treats all effects as equally important or
recommends action without showing who can authorise or operationalise it.

### 6.2 Data understanding and preparation — 8 points

Strong evidence explains the 25 logical masters, keys, units, effective dates,
network relationships and recursive dependencies. It demonstrates governed
version history, atomic publication, state reset, referential integrity and the
difference between data and policy.

Weak evidence treats supplied package names as model logic, overwrites history,
mixes package data, hides invalid references or cannot explain how a local fact
propagates through the graph.

### 6.3 Mathematical formulation — 16 points

Strong evidence presents explicit sets, indices, parameters, variables,
constraints, bounds and lexicographic stages. It covers physical flows,
lead-time indexing, recipes/yield, capacity, MOQ/multiples, activation,
inventory, service, recursive quantity/value pools, exactly-once cost and
derived-value-input isolation.

Different valid linearisations, nonlinear formulations or decompositions may
earn full credit. A black-box optimiser, diagram without algebra or formulation
that omits material business rules cannot.

### 6.4 Method selection and implementation — 14 points

Strong evidence explains why the selected workflow fits the formulation and
runtime, how integer and nonlinear semantics are controlled, how starts,
bounds, tolerances and termination are handled, and what the reported status
means. Departures are explicit and their impact is tested.

Weak evidence names a solver without method reasoning, reports an incumbent as
optimal, conceals relaxed integrality or cannot relate solver behaviour to the
recommendation.

### 6.5 Validation, benchmarking and robustness — 15 points

Strong evidence separates model construction from independent checking,
reproduces the miniature fixture and BASE benchmark controls, reconciles
physical and recursive value, checks ledger uniqueness and reference/input
isolation, and includes meaningful
failing or adversarial cases. Validation covers the full selected result, not
only aggregates that could hide defects.

Weak evidence treats solver success as validation, reports only passing tests,
uses the same faulty calculation as its own check or cannot reconcile app and
machine outputs.

### 6.6 Interactive application — 14 points

Strong evidence shows coherent completion of the controlled journeys. A user
can understand data/version state, manage Incoterms, explore the graph, preview
change impact, publish, configure, solve, compare and interpret uncertainty or
failure without needing code knowledge.

Visual polish alone is insufficient. Full credit remains available to
different information architectures and graph designs that provide an
intuitive and accessible user outcome.

### 6.7 Software engineering and reproducibility — 10 points

Strong evidence meets the declared commands and CAP-N-001 through CAP-N-010,
uses proportionate automated tests, protects committed state, exposes useful
operation/run identity and reproduces a published dataset and result context in
a clean environment.

Weak evidence depends on an undocumented local state, loses history on restart,
blocks during long work, exposes secrets, has misleading failure states or
cannot be installed and run by an assessor.

### 6.8 Presentation and recommendation — 7 points

Strong evidence gives a concise client narrative: decision, evidence,
alternatives, trade-offs, recommendation, authority, caveats and monitoring.
Statements agree with the application and machine outputs and use solver status
honestly.

Weak evidence is an implementation tour, a chart inventory or an unsupported
claim of savings, service or optimality.

### 6.9 Production readiness and limitations — 5 points

Strong evidence distinguishes the capstone prototype from a deployable product
and discusses data integration, identity/authority, security, audit, scale,
solver operations, observability, recovery, change control and fallback in the
context of Asterion.

Weak evidence claims production readiness without addressing the limitations
demonstrated by the submitted product.

### 6.10 Technical defence — 3 points

Strong performance demonstrates ownership, navigates the submitted evidence,
explains a challenged decision and can make or reason through a bounded change.
The candidate distinguishes AI assistance from verified personal judgement.

Inability to explain material submitted work creates an ownership concern for
human review; it is not handled by comparing coding style with an author model.

## 7. Technical defence design

The defence lasts 20–30 minutes. It samples material ownership and follows the
candidate's own submission rather than requiring memorised author terminology.
The assessor selects a proportionate subset of the following prompts.

| Area | Example challenge | Evidence sought |
|---|---|---|
| Physical model | Explain one balance through dispatch, lead time, receipt, transformation and inventory | Algebra, output rows and independent residual |
| Recursive value | Trace one served or closing unit back through a value pool and source | Pool equation, cost lineage and ledger |
| Cost policy | Explain why one freight, duty, setup or markup amount enters once and where | Incoterm, allocation rule and recomputation |
| Graph | Starting from an assessor-selected entity, show material upstream/downstream exposure | Running graph and connected business facts |
| Data history | Show one Incoterm or cost change from predecessor through effective version, publication and run | Master history, dataset manifest and result identity |
| Configuration | Explain why a resilience rule or override is policy rather than data | Configuration lineage, authority and comparison |
| Method | Interpret the solver termination, incumbent, bound/gap and strongest justified claim | Run metadata, log and strategy report |
| Failure | Trigger or explain one adversarial or failed case and recovery | Test/control evidence and application state |
| Recommendation | Defend one material action if a stated assumption changes | Sensitivity, trade-off and limitation reasoning |
| AI use | Identify one material AI-assisted contribution that was checked, corrected or rejected | Disclosure, evidence trail and candidate explanation |

The defence may ask the candidate to change a small parameter, locate an output
row, explain a constraint or predict the effect of a bounded change before
running it. It must not require substantial new feature development during the
session.

## 8. AI-assisted evaluation controls

AI may help an assessor locate and compare evidence, but it does not replace
deterministic gates or accountable human judgement. Any AI-assisted score must:

- cite the submitted evidence used;
- distinguish missing evidence from failed evidence;
- state criterion-level rationale and confidence;
- flag contradictions and unsupported solver claims;
- avoid inferring correctness from polish or terminology; and
- preserve the human decision and any reason for changing an automated
  recommendation.

Human review is mandatory for material contradictions, low-confidence evidence
and scores near approved grade boundaries.

## 9. WP10 assessment-policy handoff

WP8 freezes the quality-gate meanings, 100-point category structure, evidence
principles, run burden and defence areas. It also fixes these fairness rules:

- no commercial solver or particular modelling library is a hidden
  prerequisite;
- controlled stored results are permitted only when version-pinned and stale-
  safe, with the application-launched solve obligations retained;
- a documented role simulation is acceptable when the trusted boundary
  enforces authority and records auditable evidence; and
- materially different defensible formulations, methods and product designs
  can earn full credit.

WP10 assessment governance must define and calibrate:

1. consequences for each failed or not-evidenced quality gate;
2. resubmission and partial-credit rules where some work remains assessable;
3. point-level category descriptors and grade-boundary review rules;
4. assessment-environment runtime budgets and accessible solver routes within
   the WP8 fairness rules; and
5. calibration against materially different strong, adequate and defective
   submissions.

These are intentional governance responsibilities, not unresolved WP8 design
questions. WP10 may not introduce a hidden allocation test or require a
particular application architecture.
