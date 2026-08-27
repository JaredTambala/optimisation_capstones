# CAP-001 Derived Value Reconciliation Change Notes

## Document control

| Field | Value |
|---|---|
| Change note | CN-004 — Retire the dedicated recursive-value reconciliation file |
| Status | Approved and implemented during WP8 |
| Date | 26 August 2026 |
| Change class | Remove one required output without replacement and make the in-model calculation boundary explicit |
| Configuration/data/schema version | `0.3.2` / `0.3.1` / `0.3.2` |
| Explicitly unchanged | The 26 raw-file inventory, physical network, commercial rules, recursive quantity/value equations, formulation requirement and miniature-fixture arithmetic |
| Subsequent amendment | CN-005 later retires the synthetic 26th raw table and replaces its diagnostic with a solved BASE benchmark; the CN-004 calculation boundary remains unchanged |

## 1. Problem

`recursive_cost_reconciliation.csv` was previously described as a required
candidate output. Although it contained equation residuals rather than supplied
costs, its existence wrongly suggests that recursive value is a separate data
product or a calculation to perform outside the mathematical model.

That is not the intended problem. The recursive structure is part of the
formulation itself. It is discovered and solved through the relationships among
local flows, transformations, value-add, inventory pools and demand service.

## 2. Input and calculation boundary

The supplied business data describes local facts:

- an external quote where material enters the modelled network;
- one approval and contract relationship between a seller and buyer;
- the commercial terms applying to that relationship;
- one transport lane and its local charges;
- one transformation recipe and its inputs, yield and local value-add;
- applicable FX, duty, Incoterm and allocation rules; and
- opening inventory quantity and inherited book value.

No assessed-model input may provide an authoritative intermediate pool cost,
downstream landed cost, cumulative path cost, terminal unit cost or end-to-end
recursive cost. Those values are consequences of selected flows,
transformations, pooling and accounting treatment.

The candidate's MILP or MINLP must therefore represent recursive calculation in
the mathematical model, using variables, expressions and constraints for the
relevant quantities and values. It must not read a precomputed recursive-cost
table or rely on a post-solve spreadsheet to establish the model economics.

CN-005 subsequently retired the synthetic standard-cost diagnostic input. The
published BASE reference is solution evidence and must never enter the
candidate calculation as a model input. This strengthens, rather than alters,
the assessed formulation boundary above.

## 3. Decision

Retire `recursive_cost_reconciliation.csv` without a replacement file.

During a solve, the modelling implementation must calculate the relevant pool,
dispatch, receipt, transformation, closing and served values in working memory.
The submitted application may persist ordinary run results needed for user
interpretation, comparison and reproducibility, but it must not create a
dedicated recursive-cost or recursive-value reconciliation dataset.

The evaluator must independently reconstruct the applicable quantity and value
equalities from the immutable inputs and submitted decision/result evidence. It
may report aggregate counts, maximum residuals, tolerances and pass/fail states
in `reconciliation_summary.json`. The detailed evaluator calculation remains
working state or private diagnostic evidence, not a candidate-supplied file.

The miniature fixture retains its disclosed accounting walkthrough and control
totals. Its reconciler calculates the detailed equalities in memory. It must not
publish an `expected_reconciliation` CSV containing recursive-value rows.

Terms such as recursive value or recursive formulation may remain in the
mathematical specification where they describe the problem to be solved. They
must not appear as raw-data classifications or as a separate required data
product.

## 4. Controlled implementation consequences

The controlled regeneration removed the file from:

- `config/cap001_decision_config.json` and its schema;
- required-output schemas, generated data dictionaries and manifests;
- private and student miniature-fixture manifests and expected files;
- empty output contracts and release-manifest templates;
- validators, builders and generated-artifact tests;
- WP8 task, evidence and traceability documents; and
- the student release and evaluator submission paths.

The fixture builder now retains in-memory calculation and summary assertions
without serialising the equation rows. The evaluator must follow the same
boundary. Historical reports and this change note may mention the retired
filename when explaining the migration.

## 5. Acceptance

CN-004 is complete because:

1. every assessed-model input schema and dataset is proven free of intermediate,
   cumulative and terminal derived-cost fields;
2. no replacement recursive-cost or equation-grain value-reconciliation file
   is added to the candidate contract;
3. the retired filename is absent from active configuration, schemas, manifests,
   fixture paths, empty contracts and generated documentation;
4. the mathematical model derives recursive quantities and values through its
   own variables, expressions and constraints;
5. the fixture and evaluator independently reproduce all controlled
   quantity/value equalities in memory and detect negative variants;
6. `reconciliation_summary.json` contains sufficient aggregate validation
   evidence without becoming a hidden detailed cost table;
7. the assessed route rejects any attempt to source an internal pool value from
   any raw field or from the published reference solution; and
8. the full generated-artifact and validation test suite passes.
