# CAP-001 Whole-Dataset Viability Audit Plan

## Document control

| Field | Value |
|---|---|
| Purpose | Decide whether the frozen CAP-001 datasets can sustain the intended optimisation-and-application capstone |
| Status | Executed; accepted at 10/10 gates |
| Date | 25 August 2026 |
| Frozen input checkpoint | Recalibrated package hashes in §2; supersedes Git commit `320345a` |
| Scope | Whole-dataset feasibility, decision richness, recursive-accounting viability, configuration sensitivity, scenario materiality and broad computational accessibility |
| Explicit non-scope | A reference allocation, a preferred recommendation, a full reference application, exhaustive optimisation, student-release promotion or tuning toward a hidden answer |

## Audit outcome — 25 August 2026

The audit was executed against the six recalibrated package hashes below and
passed all ten gates. The common fixed-price MILP accepted every complete
dataset, all six default cases were certified zero-shortage feasible and every
case used 300 units of boundary replenishment. Disabling boundary sourcing in
BASE makes zero shortage infeasible.

Independent replay of a valid BASE witness against each replacement dataset
proved that every scenario requires physical adaptation. The policy matrix
demonstrated concentration, expedited-eligibility, authorised-approval and
service-weight configuration; the unauthorised exception was rejected. Three
conditioned recursive-cost MINLP cases reconciled with a maximum accounting
residual below 0.001 and without a global-optimality claim.

The result accepts the datasets as sufficiently deep examination inputs. It
does not approve an optimiser, retain a reference allocation, choose a business
policy or promote the packages into the student release.

Each audit run treats its selected package as a deterministic planning case
whose full P01–P12 facts are known at P01. Replay of the BASE witness against a
replacement package proves that a different horizon-wide plan is required; it
does not simulate a disruption being revealed during execution.

## 1. Decision to be made

The audit answers one authoring question:

> Do the six frozen datasets contain enough coherent physical, temporal,
> commercial and disruption depth for a student to build and defend an
> explicit MILP or MINLP decision system with configurable policies and
> interpretable outputs?

WP4–WP6 have already established that the component data is valid, connected,
choice-rich at source and complete over the planning window. WP7 does not
repeat those generators or use the amount of author-side code as evidence of
quality. It tests their combined effect only far enough to accept or reject the
dataset as an examination input.

The audit is successful when it demonstrates credible decision pressure and
trade-offs. It is not required to discover the best business answer, reproduce
what a strong student might build or retain a hidden allocation for grading.

## 2. Frozen audit inputs

WP7 reads the six complete packages accepted in WP6. It does not edit their
CSV files, seed, thresholds or manifests.

| Package | Frozen SHA-256 |
|---|---|
| BASE | `b5791a694ae6e218bf5bae75bb26f1654191d4baf0613b681664e60de6cf072d` |
| SCN-01 | `bf400d705a3f93867c5ef7cecd16358cb7a8a9d258d69262b967ae7e11537737` |
| SCN-02 | `5bdb02514df4d9194c018df92c601beaee9a163745dc84a2560b081a864de885` |
| SCN-03 | `7ac8db5bddaea5c2750e05e0134218ee6ca9a81c30ec237a1687ba5f0855579b` |
| SCN-04 | `db1d3249ddada268afe564f34eb712675f1ac0272ca23cd7396892b9fd9b8c80` |
| SCN-05 | `13c44aba34a724a6dc54330a1a062b111278f5df2a3488fb6b78309d78e67ebb` |

The audit also inherits, rather than re-proves:

- the accepted WP4 network scorecard and lineage witnesses;
- the accepted WP5 commercial scorecard and conditional cost envelopes;
- the accepted WP6 planning profile, package checks and zero-shortage BASE
  physical MILP smoke result; and
- the frozen WP2/WP3 fixture-scale recursive-cost and reconciliation evidence.

If an inherited check drifts, WP7 stops and reports that regression before
running decision-behaviour probes.

## 3. Questions answered by the audit

The retained evidence establishes:

1. whether all five stress packages remain solvable or produce explainable
   minimum shortage through one common explicit formulation;
2. whether the combined commercial and planning facts admit materially
   different cost, inventory, service, mode and concentration choices;
3. whether resilience rules, approval exceptions and other declared policy
   parameters can change decisions without changing the selected dataset;
4. whether recursive value propagation remains bounded and reconcilable at the
   full generated scale; and
5. whether the resulting computational burden is broadly reasonable for the
   intended student engagement.

These were the only gaps the audit was authorised to close.

## 4. Audit method

### 4.1 Establish full formulation bounds

Combine accepted capacity, inventory, demand and lead-time facts with the WP5
commercial envelopes to produce finite safe bounds for shipment, production,
inventory, pool quantity, pool value and common unit cost. Test that retained
feasible incumbents do not depend on an artificial bound.

This is a formulation-safety calculation, not a cheapest-path model or a
reference allocation.

### 4.2 Run a common fixed-price MILP viability probe

Construct the same explicit fixed-price MILP from each complete package. For
the pinned default, first test zero-shortage feasibility; a feasible witness
combined with the non-negative service lower bound certifies the service stage,
after which the economic stage is solved under that lock. The
probe must include the controlled physical, timing, approval, capacity,
inventory and service rules. It may use Pyomo, PuLP or another suitable
algebraic modelling library; the evidence is formulation-based, not
library-based.

The probe records only:

- package and configuration hashes;
- solver and termination classification;
- runtime and model size;
- weighted and unweighted shortage;
- broad totals or bands for cost, inventory, expedited transport and
  concentration; and
- named active constraint families needed to explain the result.

No row-level allocation, exact expected objective or preferred route is
retained.

### 4.3 Demonstrate genuine policy configuration

Use a deliberately small matrix of configuration variants. Each variant is a
separate, hashed run-policy input; none edits a dataset.

| Probe | Dataset focus | Capability being tested |
|---|---|---|
| Pinned default | BASE and all stresses | Common loader, approvals, objective hierarchy and comparable outputs |
| Concentration or diversity rule | BASE and SCN-04 | A quantitative resilience rule changes the feasible region or exposes a real cost/service trade-off |
| Expedited intervention | SCN-02 or SCN-05 | Mode eligibility or an intervention parameter changes service, timing and cost through generic data |
| Authorised approval exception | One case with a genuine alternate | Original rule, effective rule, authority and decision consequence are auditable; an unauthorised exception is rejected |
| Service sensitivity within the controlled hierarchy | SCN-05 | Permitted within-stage parameters alter explainable recourse without diluting higher-priority service rules |

Not every variant must be run against every package. The matrix is complete
when each capability is demonstrated once in a data context where it is
relevant and the common implementation remains applicable elsewhere.

### 4.4 Demonstrate an opposed trade-off

Use explicit MILP or MINLP runs to retain at least two feasible, materially
different aggregate strategies. One may be cost-oriented under the pinned
service hierarchy; another may add a resilience or intervention constraint.
The evidence must show an opposed aggregate consequence, such as lower cost
versus lower concentration or higher intervention cost versus improved
service. This establishes that the data supports a decision, rather than a
single universally dominant route.

The audit does not need to enumerate every alternative or declare either
strategy correct.

### 4.5 Run a bounded recursive-cost MINLP probe

Use the existing private model-viability harness for BASE and one materially
relevant stress package. An accepted result is a finite, independently
reconciled feasible incumbent from an explicit recursive-cost MINLP; global
optimality is not required.

The retained evidence is limited to:

- formulation and solver classification;
- bound and epsilon checks;
- aggregate quantity/value conservation residuals;
- broad component-value bands; and
- whether the recursive and fixed-price formulations produce an explainable
  aggregate decision difference.

If a full-scale recursive incumbent cannot be obtained within the bounded
author run, the audit must distinguish a modelling defect, an unsafe bound, a
solver-access limitation and genuine computational difficulty. It must not
convert the required recursive model into a heuristic and call that proof.

### 4.6 Classify data participation

Every raw-data family receives one declared role:

- **mathematical input** — directly creates a set, parameter, constraint or
  objective component;
- **configuration evidence** — supports a student-derived resilience rule,
  override or sensitivity parameter; or
- **interpretive/audit evidence** — supports explanation, validation or
  reconciliation without silently changing the model.

The goal is not to force every row into an objective. Historical performance
and incidents, for example, remain exploratory evidence. A file is decorative
only if the engagement cannot use it in its declared role.

## 5. Scenario-specific evidence

Each stress package must change at least one designated aggregate outcome or
constraint family relative to BASE under a comparable configuration.

| Dataset | Required materiality evidence |
|---|---|
| SCN-01 | Surge use, timing, advance inventory, concentration, cost or service response attributable to the polymer-resin source constraint |
| SCN-02 | Transit, dispatch timing, expedited use, landed cost or service response attributable to the affected corridors |
| SCN-03 | Tier-1 site eligibility, alternate production, inventory or service response attributable to site unavailability |
| SCN-04 | Regional/parent concentration, constrained recourse, cost or service response attributable to correlated capacity loss |
| SCN-05 | Service-priority, intervention, inventory or explainable-shortage response under combined supply, logistics and demand pressure |

A different numerical result is not enough by itself. The audit must connect
the changed data, affected model construct and aggregate consequence. An exact
minimum percentage change is intentionally not prescribed before the first
runs; the owner judges materiality against broad, predeclared bands and the
business question, not against a desired allocation.

## 6. Acceptance gates

| Gate | Pass condition |
|---|---|
| G1 — Identity | All six inputs match the frozen package hashes and all inherited checks still pass. |
| G2 — Common formulation | One explicit fixed-price MILP construction and solve path accepts all six complete packages after state reset. |
| G3 — Feasibility and service | BASE retains zero shortage; every stress package has a classified feasible result or an explainable, independently checked minimum shortage. |
| G4 — Scenario materiality | Each stress package meets its scenario-specific evidence requirement through traceable data → construct → outcome evidence. |
| G5 — Configurability | The selected policy matrix demonstrates resilience, intervention, approval and within-hierarchy parameter handling without editing datasets. |
| G6 — Decision richness | At least two explicit-formulation incumbents exhibit a genuine opposed aggregate trade-off; no single strategy is asserted to dominate every allowed configuration. |
| G7 — Recursive viability | BASE and one stress case produce a finite, independently reconciled recursive-cost MINLP incumbent. Failure triggers a specific reject-or-reopen decision rather than a weaker substitute. |
| G8 — Bounds and accounting | Full-scale bounds are finite and safe; retained incumbents do not touch invalid artificial bounds; quantity and value residuals meet the controlled tolerances. |
| G9 — Data usefulness | Every raw-data family has evidence for its declared mathematical, configuration or interpretive role. |
| G10 — Accessibility and privacy | Runs complete within recorded bounded author budgets, and retained evidence contains no reference allocation, hidden answer or student-release leakage. |

WP7 passes only when all ten gates pass and the capstone owner accepts the
evidence. A technically valid solve is not enough if the business trade-offs
remain trivial or uninterpretable.

## 7. Minimal implementation boundary

The default implementation route is to reuse `cap001_model` and the existing
independent reconciliation code. WP7 does not create a second model package.
Add only the smallest orchestration or aggregate-reporting code needed to run
the audit reproducibly.

Permitted retained artefacts are:

- a machine-readable audit manifest containing input/configuration hashes,
  commands, solver classifications and gate results;
- aggregate feasibility, trade-off, scenario and reconciliation evidence;
- safe bound derivations and broad plausibility bands; and
- a concise owner-facing acceptance report.

Prohibited retained artefacts are a full allocation, exact expected student
objective, preferred supplier/route plan, reference UI, production solver
service or a bundle of model-solution outputs.

## 8. Change control and stop rules

The frozen datasets are not tuned merely because an author probe prefers a
different answer.

1. If a failure is caused by the audit harness, repair the smallest private
   authoring component and rerun the affected checks.
2. If a failure proves a data defect or materially trivial scenario, record the
   failed gate, reopen the originating WP4–WP6 control, regenerate every
   dependent package, assign new hashes and obtain renewed owner acceptance.
3. Never hand-edit a generated CSV, weaken an acceptance gate after seeing a
   result or add a scenario-specific equation.
4. Stop implementation once the ten gates have enough evidence for an owner
   decision. Do not continue toward a polished reference solution.
5. Student-release packaging, consultant instructions, application evidence
   and grading policy remain WP8–WP10 responsibilities.

## 9. Implementation sequence

1. Freeze the audit matrix, broad materiality bands and retained-evidence
   allow-list before solving.
2. Re-run inherited controls and verify all six input hashes.
3. Complete and challenge full-scale quantity, value and unit-cost bounds.
4. Run the common fixed-price MILP across all six packages.
5. Run only the selected configuration probes and opposed-trade-off comparison.
6. Run the bounded recursive-cost MINLP for BASE and one selected stress case,
   then reconcile it independently.
7. Classify data-family participation and review broad business plausibility.
8. Produce the ten-gate report and request owner acceptance or controlled
   reopening of the specific failed dataset control.

This sequence is evidence-driven: no new code is justified until an existing
check or harness cannot produce one of the named gate results.
