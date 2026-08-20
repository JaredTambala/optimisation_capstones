# CAP-001 Whole-Dataset Viability Audit Plan

## Document control

| Field | Value |
|---|---|
| Purpose | Decide whether the frozen CAP-001 datasets can sustain the intended optimisation-and-application capstone |
| Status | Executed; frozen dataset rejected and WP6 calibration reopened |
| Date | 19 August 2026 |
| Frozen input checkpoint | Git commit `320345a` |
| Scope | Whole-dataset feasibility, decision richness, recursive-accounting viability, configuration sensitivity, scenario materiality and broad computational accessibility |
| Explicit non-scope | A reference allocation, a preferred recommendation, a full reference application, exhaustive optimisation, student-release promotion or tuning toward a hidden answer |

## Audit outcome — 19 August 2026

The audit was executed against the six frozen package hashes below. The common
MILP path classified all six service problems, and the conditioned full-scale
MINLP cases reconciled. Those technical successes did not establish dataset
viability.

Every pinned-default incumbent used zero external boundary supply. Opening and
downstream inventory could therefore satisfy the entire horizon without
replenishment. In consequence, the silicon-source interruption and correlated
regional-capacity scenario did not produce certified aggregate materiality.
Apparent cost differences came from overlapping time-limited solver intervals
and are not accepted as evidence. The approval and service-weight probes also
changed configuration without demonstrating a material decision consequence,
and the opposed diversity/cost trade-off was not certified for the same reason.

The result is a controlled rejection at eight of ten gates, not a request for a
model solution. G4 scenario materiality and G5 complete configuration
sensitivity fail. The resilience and no-expedite probes are useful, but the
approval exception has no certified decision consequence and the service-weight
change is inactive under complete service. WP6 planning and scenario
calibration is reopened. Demand, opening inventory and scenario targets must be
recalibrated through deterministic generation, after which all six packages
require new hashes and renewed owner acceptance before this audit is rerun.

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
| BASE | `b040291ddcbac6671400732f3c2a4859ec2fd7010d45bb33f707cd0640eb88d2` |
| SCN-01 | `504d15fdfafa29112691a127de32efa066e9215b6f6cf17c57dfb317d375047d` |
| SCN-02 | `66086c534ed4fb92ec7a4112f94eb6b448796845dfba92637141784299bf19fe` |
| SCN-03 | `bdc048febb316f8f6dcb058168d1a4d44c7432c8c297972efa31ff8b927a19ae` |
| SCN-04 | `7b14ddec2ed4a504d9181da79fed77d3083cfb33f78bf68468abff62959beaa7` |
| SCN-05 | `be619dff17206d2a0d80191a0b571c48d7c009f72277be135253eb77dd3f2a3a` |

The audit also inherits, rather than re-proves:

- the accepted WP4 network scorecard and lineage witnesses;
- the accepted WP5 commercial scorecard and conditional cost envelopes;
- the accepted WP6 planning profile, package checks and zero-shortage BASE
  physical MILP smoke result; and
- the frozen WP2/WP3 fixture-scale recursive-cost and reconciliation evidence.

If an inherited check drifts, WP7 stops and reports that regression before
running decision-behaviour probes.

## 3. Questions not yet answered

The existing evidence does not yet establish:

1. whether all five stress packages remain solvable or produce explainable
   minimum shortage through one common explicit formulation;
2. whether the combined commercial and planning facts admit materially
   different cost, inventory, service, mode and concentration choices;
3. whether resilience rules, approval exceptions and other declared policy
   parameters can change decisions without changing the selected dataset;
4. whether recursive value propagation remains bounded and reconcilable at the
   full generated scale; or
5. whether the resulting computational burden is broadly reasonable for the
   intended student engagement.

These are the only gaps WP7 is authorised to close.

## 4. Audit method

### 4.1 Establish full formulation bounds

Combine accepted capacity, inventory, demand and lead-time facts with the WP5
commercial envelopes to produce finite safe bounds for shipment, production,
inventory, pool quantity, pool value and common unit cost. Test that retained
feasible incumbents do not depend on an artificial bound.

This is a formulation-safety calculation, not a cheapest-path model or a
reference allocation.

### 4.2 Run a common fixed-price MILP viability probe

Construct the same explicit fixed-price MILP from each complete package. The
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
| SCN-01 | Upstream substitution, advance inventory, concentration, cost or service response attributable to silicon-source loss |
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
