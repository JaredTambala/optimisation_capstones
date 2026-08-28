# CAP-001 Application and Evidence Contract

## Document control

| Field | Value |
|---|---|
| Purpose | Define how candidate outcomes are demonstrated and independently checked without prescribing application views or architecture |
| Status | Current controlled authoring source |
| Date | 28 August 2026 |
| Companion requirements | `docs/CAP-001_CANDIDATE_TASK_REQUIREMENTS.md` |
| Release contract | `docs/CAP-001_RELEASE_CONTRACT.md` |

## 1. Evidence principle

The application is part of the consulting outcome, not a presentation wrapper
around files produced elsewhere. Evidence must show that the user can complete
the required business journeys and that the displayed recommendation agrees
with reproducible machine-readable results.

This contract defines behaviours and evidence. It does not require named pages,
a fixed navigation structure, a frontend framework, a graph library, a database
product or a synchronous solve. One coherent interaction may satisfy several
requirements when the evidence remains clear.

Screenshots and slideware may illustrate a result but do not establish that a
capability works. A capability is demonstrated through the running product,
repeatable automated evidence, machine-readable artefacts or a controlled
recording that exposes inputs, actions, state changes and results.

## 2. Product state visible to the user

The user must never need to infer which business reality or calculation is on
screen. Wherever relevant, the application exposes:

| State | Minimum visible identity |
|---|---|
| Source import | Package/import identity, schema version, source hashes, import time and validation state |
| Master record | Business key, record version, effective interval, active/retired state and history |
| Draft change | Parent dataset, changed records and fields, author, reason and blocking validation |
| Published dataset | Dataset-version ID, parent, publication state/time, content hash and validation result |
| Policy configuration | Configuration ID/version/hash, effective parameters, approvals and overrides |
| Solve run | Run ID, dataset/configuration/method identities, state, solver status, timestamps and evidence validity |
| Result | Run ID, result age/state, validation state, method classification and material limitations |

A result is stale whenever the application context no longer matches the data,
policy or method versions recorded by the run. A stale result may remain
available for comparison but cannot be presented as the current
recommendation.

## 3. Controlled application demonstrations

### 3.1 Complete data journey

The evidence must demonstrate that a user can:

1. import a complete supplied package into the logical masters;
2. inspect source identity, validation and master-record history;
3. select a published dataset and explore its supply graph;
4. create a draft successor change;
5. understand affected records and relationships;
6. resolve or observe a publication-blocking validation failure;
7. publish a complete immutable successor dataset; and
8. return to the parent and show that it has not changed.

At least one deliberately conflicting or stale update must be rejected without
losing the last committed state.

### 3.2 Incoterm journey

The evidence must demonstrate every Incoterm in current and historical scope,
then show a governed change from draft to published data. The user must be able
to see:

- its effective commercial-responsibility fields and active state;
- contracts and graph relationships that reference it;
- validation that blocks historical erasure or an invalid reference;
- the record-version and dataset-version change; and
- the resulting eligibility, cost-construction or decision consequence after a
  solve.

The demonstration must include creation of a schema-valid Incoterm record. A
new unique code is permitted when the record is clearly presented as a
modelling abstraction and passes the same effective-dating, authority and
referential controls as the supplied terms.

### 3.3 Supply-graph journey

Starting from an entity selected by a user or independent reviewer, the evidence must
show that the user can orient themselves, traverse relevant upstream and
downstream relationships and inspect connected business facts. The user must
then relate either a data change or a solved flow, constraint, cost or service
effect to the affected graph elements.

The graph must support intuitive understanding. No preferred visual encoding
or layout is prescribed.

### 3.4 Configuration and authority journey

Without editing the published dataset, the evidence must demonstrate:

- selection of a versioned policy configuration;
- one quantitative resilience intervention;
- one meaningful within-stage preference or another approved configurable
  matter;
- rejection of an unauthorised exception; and
- a permitted exception whose authority, reason, original rule, effective rule
  and affected result remain visible.

The same dataset under two configuration versions must remain distinguishable
from two different dataset versions.

### 3.5 Solve and explanation journey

For a selected published dataset and policy configuration, the evidence must
show the user starting or retrieving a run, following its state and inspecting
the resulting horizon-wide recommendation. The user must be able to connect:

- service and shortage;
- orders, shipments, transformations and inventory;
- material constraints and approvals;
- recursive material value and non-capitalised cost;
- published BASE reference versus submitted BASE decision differences;
- data or policy changes versus result changes;
- resilience trade-offs; and
- solver, validation and limitation evidence.

An infeasible, failed, interrupted, local, approximate or time-limited outcome
must remain intelligible and must not be presented as globally optimal.

### 3.6 Generality journey

The same submitted product must import and validate all six supplied packages.
It must also accept a complete schema-valid dataset version whose identifier
and changes were not hard-coded by the candidate.

The unseen dataset must support an application-launched decision run. The
recursive route may return an honestly classified feasible, time-limited,
failed or infeasible result within the approved runtime policy. The published
BASE benchmark calibrates the known case; it is not a fallback result for an
unseen data reality.

## 4. Live, asynchronous and stored-result behaviour

The following behaviours must be live in the submitted product:

- data import and validation;
- published/draft selection and history inspection;
- supply-graph exploration;
- Incoterm and minimum supported business-data authoring;
- draft impact inspection and publication;
- policy selection and authorised configuration changes;
- run submission or retrieval; and
- result exploration, comparison and export.

Solve execution may be synchronous or asynchronous. Controlled stored results
may be supplied for expensive example comparisons when:

1. the result records the exact dataset, resolved master-record, configuration,
   method and output hashes;
2. the application labels it as stored and shows its age and solver status;
3. it is selectable only against compatible inputs;
4. changing relevant data or policy marks it stale rather than silently reusing
   it; and
5. the candidate demonstrates at least one application-launched solve from a
   user-authored published dataset.

The application must expose queued, running, completed, failed, interrupted and
stale states where those states are applicable. Long-running work must not
freeze the business interface.

## 5. Machine-readable run evidence

### 5.1 Evidence classes

The fourteen released output schemas are organised by purpose and implement
this controlled evidence contract.

#### Per-run core evidence

Every claimed run supplies:

| Artefact | Purpose |
|---|---|
| `run_metadata.json` | Dataset, resolved record versions, configuration, formulation, method, solver, status, timing, hashes and limitations |
| `metrics.json` | Run-level service, quantity, value, inventory, cost, resilience and validation measures |
| `orders.csv` | Contract/material orders by dispatch period |
| `shipments.csv` | Dispatched and arriving flow, timing, lane and value evidence |
| `production.csv` | Recipe activity, inputs/outputs, setup and transformation value |
| `inventory_cost_rollforward.csv` | Node/material/period quantity and value pool movement |
| `demand_service.csv` | Demand, served quantity, shortage and service priority |
| `constraint_report.csv` | Material constraint-family residual, slack and binding evidence |
| `reconciliation_summary.json` | Run-level physical, recursive-value, integrality and bound validation summary |

Empty files with headers are permitted only when the artefact is structurally
applicable and the run contains no corresponding activity. An artefact cannot
be omitted merely because its evidence would expose a weak result.

#### Recursive-run evidence

Every recursive result additionally supplies:

| Artefact | Purpose |
|---|---|
| `cost_component_ledger.csv` | Exactly-once capitalised and non-capitalised realised cost classification |
| `cost_lineage.csv` | Terminal/closing value contribution traced through relevant sources and value-add stages |

Recursive quantities and values are calculated by the mathematical model in
working memory. There is no dedicated recursive-cost or equation-grain
value-reconciliation file. An independent check reconstructs the
applicable equalities from inputs and run results; only aggregate residual,
tolerance and pass/fail evidence belongs in `reconciliation_summary.json`.
The benchmark reproduction evidence must make the candidate run's validation
scope, objective quality and material aggregate differences explicit.

#### Comparison-set evidence

Comparison artefacts are produced once per declared comparison set rather than
duplicated in every run directory:

| Working artefact | Purpose |
|---|---|
| BASE benchmark reproduction record | Candidate BASE result versus the published reference controls and aggregate result evidence |
| `dataset_comparison.csv` | Parent/successor or other published-dataset comparison at a consistent grain |
| `configuration_comparison.csv` | Same dataset under different policy configurations |

The frozen contract replaces the closed-scenario name
`scenario_comparison.csv` with `dataset_comparison.csv` and retires
`scenario_results.csv`. Run-level metrics and comparison-set evidence provide
the required information without duplicating a scenario-labelled summary.

### 5.2 Identifier evolution

Machine outputs must not depend on a six-value scenario enumeration. Where a
legacy schema used `scenario_id`, the released run identity instead uses:

- `dataset_version_id`;
- `dataset_content_hash`;
- `resolved_record_versions_hash`;
- `policy_configuration_id` and `policy_configuration_hash`;
- `method_configuration_hash`; and
- `parent_dataset_version_id` where a comparison requires it.

The supplied package label may remain as source provenance, but it is not the
runtime identity of an arbitrary user-authored dataset.

## 6. Narrative and decision evidence

The candidate must provide enough narrative evidence for a client and independent reviewer
to understand the decision without reverse-engineering the application:

- mathematical formulation and notation;
- solver and method strategy with honest classification;
- validation report and material adversarial evidence;
- assumptions and limitations;
- resilience intervention and trade-off recommendation;
- production-readiness analysis;
- 10–12 slide client presentation;
- AI-usage disclosure; and
- decision summary that identifies the selected data/configuration versions.

Every material explanation has two layers:

1. **Business and data:** what changed or constrained the network and what it
   means for service, cost, inventory, resilience and action.
2. **System interaction:** which data/configuration versions, formulation
   constructs, gates, overrides, solver state and validation evidence produced
   or qualified the result.

Technical detail without a business consequence is incomplete. A business
claim without data and system evidence is unsupported.

## 7. Non-functional evidence

The candidate supplies proportionate evidence for CAP-N-001 through CAP-N-010.
At minimum this includes:

- a clean installation and application-start record;
- automated tests for data history, publication atomicity, stale/conflicting
  writes, authority checks and stale-result handling;
- an accessibility check of the core journeys and manual keyboard evidence;
- a declared environment and response-time measurement for representative
  non-solver interactions;
- one recoverable failed or interrupted operation;
- logs correlated with a demonstrated data change and solve run; and
- an export/restore demonstration for one published dataset version.

This is capstone evidence, not production certification. The production-
readiness note identifies material controls that would need strengthening for
deployment at Asterion.

## 8. Evidence consistency rules

- The application, machine outputs, reports and presentation must use the same
  run identities and cannot contradict one another.
- Values shown at a different aggregation grain must reconcile to the standard
  output evidence within controlled tolerance.
- Recomputed independent checks take precedence over a displayed success flag.
- A result with failed hard validation cannot be described as a valid plan.
- Stored evidence with incompatible data, policy or method identity is stale.
- Solver logs and raw termination conditions must be retained when they support
  a status, bound, gap or optimality claim.
- Missing or inapplicable evidence must be identified explicitly; silent
  omission is not an acceptable status.

## 9. Frozen evidence decisions

- The same product must attempt an application-launched recursive decision run
  for the assessor-created dataset. The outcome may be honestly classified as
  feasible, time-limited, failed or infeasible; success or global optimality is
  not required.
- At least two candidate-justified supplied stress examples require solved
  comparison evidence. They may use controlled stored results under §4.
- `dataset_comparison.csv` and `configuration_comparison.csv` replace the
  closed scenario comparison, and `scenario_results.csv` is retired.
- BASE benchmark evidence, dataset comparisons and configuration comparisons
  are generated once per declared comparison set; core and recursive evidence
  remains attributable to each run.
- Every controlled application journey must be runnable. The assessor may
  sample it live and may rely on repeatable automated or recorded evidence for
  additional coverage when identities, inputs, actions and outcomes remain
  visible.
- Solver execution may be synchronous, asynchronous or retrieved from a
  strictly compatible stored result. At least one user-authored published
  dataset must be solved through an application-launched route.

Assessment governance may refine assessment-environment budgets and evaluation
mechanics. It may not convert supplied example identifiers into
a closed runtime, require a commercial solver, or relax the lineage and stale-
result protections fixed here.
