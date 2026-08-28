# CAP-001 BASE Reference Benchmark Change Notes

## Document control

| Field | Value |
|---|---|
| Change note | CN-005 — Replace the synthetic fixed-price diagnostic with a solved BASE reference benchmark |
| Status | Approved and implemented during WP8 |
| Date | 26 August 2026 |
| Configuration/data/model/schema versions | `0.3.3` / `0.3.2` / `0.3.1` / `0.3.3` |
| Supersedes | The fixed-price diagnostic requirement, `baseline_standard_costs.csv`, `baseline_comparison.csv` and former candidate `solve_baseline` obligation |

## 1. Decision

CAP-001 uses one solved and independently validated BASE reference incumbent as
the full-scale diagnostic. It no longer supplies synthetic intermediate
standard costs or requires a second fixed-price economic formulation.

The benchmark is result evidence, not business data and not a model input. It
is pinned to the exact BASE dataset hash, policy/configuration hash, formulation
semantics and declared solution method. A candidate must be able to reproduce
its material service, recursive accounting and objective-quality controls
before relying on their own recommendations.

## 2. Why the former diagnostic is retired

`baseline_standard_costs.csv` contained precomputed state-period unit values
derived by propagating upstream costs and then deliberately biasing selected
rankings. Although isolated from the assessed recursive model, it was not a
leg-local business fact and duplicated part of the reasoning the candidate is
expected to formulate.

The fixed-price comparison consequently tested divergence from an artificial
comparator rather than whether the candidate's implementation could reproduce a
credible, known full-horizon recursive result.

## 3. Benchmark boundary

The published benchmark must include:

- immutable BASE dataset and configuration identities;
- formulation and method classification;
- solver status, limitations and any available bound or gap;
- the complete retained incumbent decisions and recursive value state needed
  for independent replay;
- service, objective-stage and material aggregate controls;
- independent physical, integrality, bound and recursive-accounting results;
- explicit numeric tolerances; and
- an explanation that the incumbent is not asserted to be the unique or
  globally optimal allocation unless separately certified.

The private authoring process may use an algebraic physical-feasibility seed or
other declared heuristic around the explicit recursive MINLP. Any such method
must be classified honestly. No synthetic intermediate-cost table may be
reintroduced as a benchmark dependency.

## 4. Faithful reproduction

Faithful reproduction means that a candidate run against the pinned BASE
dataset and reference configuration:

1. passes independent schema, physical, integrality, bound and recursive-value
   validation;
2. reproduces the benchmark service result within the controlled quantity
   tolerance;
3. reproduces the benchmark recursive accounting controls within the
   controlled value and unit-cost tolerances;
4. reaches the published objective value or accepted quality interval; and
5. explains material aggregate decision differences.

Row-for-row equality with the retained allocation is not required. CAP-001
permits another feasible allocation when it satisfies the formulation and the
published equivalence/quality controls. This prevents degeneracy or a stronger
valid solution from being treated as failure.

## 5. Controlled consequences

The implementation:

- removes `baseline_standard_costs.csv` from raw configuration, schemas,
  fixtures, commercial generation and all six dataset packages;
- removes `baseline_comparison.csv` from the required outputs;
- replaces the former candidate `solve_baseline` command with
  `reproduce_reference` in the submission
  contract;
- replaces fixed-price application and assessment requirements with BASE
  reference-reproduction outcomes;
- retains private physical-feasibility tooling only as authoring support, not
  as a candidate model or economic comparator; and
- publishes the benchmark outside the versioned business-data package.

## 6. Acceptance

CN-005 is complete when:

- all supplied datasets contain only the 25 approved leg-local and inherited-
  state masters;
- no active schema, manifest, fixture or requirement references the retired
  standard-cost or comparison files;
- the BASE reference bundle reproduces deterministically from the pinned
  inputs and passes independent validation;
- benchmark results cannot be consumed as optimisation inputs;
- student and evaluator contracts apply the same reproduction tolerances and
  equivalence rules; and
- generated-artifact, dataset, benchmark and full repository tests pass.
