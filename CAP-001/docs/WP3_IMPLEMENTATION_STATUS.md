# CAP-001 Model-viability Proof — Frozen Evidence Record

## Status

WP3 was frozen on 18 August 2026. The implemented evidence is sufficient for
its authoring purpose: proving that the controlled fixture and modelling
semantics can support a credible optimisation capstone.

This is not acceptance of a model solution, a reference application or the
student release. It does not supersede formal WP1/WP2 controls.

## What has been demonstrated

- All 25 raw contracts can be loaded into explicit optimisation formulations
  without importing solved quantities or values from the fixture reconciler.
- The private local-fact physical-seed MILP and recursive-cost MINLP share the
  same tier-neutral physical constraints.
- The miniature network is physically feasible and its recursive accounting
  reproduces the EUR 2,239.30 conservation identity and all 105 published
  control totals.
- Small private probes demonstrate a real sourcing choice, lexicographic
  shortage behaviour, controlled infeasibility and finite/zero-pool bounds.
- HiGHS solves the MILP and the HiGHS/IPOPT route provides an honestly
  classified local/heuristic recursive result in the authoring environment.
- Extracted decisions can be checked independently of live model expressions.

Together these results establish fixture-scale semantic viability. They do not
establish the depth or calibration of the future full generated dataset.

## Why `cap001_model` is retained

The package is private authoring infrastructure. Its useful role is to act as a
smoke-test oracle while WP4–WP6 generate and calibrate the full dataset.

| Part | Continuing value |
|---|---|
| `data.py`, `physical.py` | Detect contract, reference, topology and physical-feasibility defects in generated data. |
| `physical_seed.py` | Provide a cheap private MILP physical-feasibility seed; its proxy objective is not candidate economics. |
| `recursive.py`, `bounds.py` | Detect recursive-cost, zero-pool and bound defects. |
| `validation.py`, `recursive_validation.py` | Reconcile quantities and values independently of solver expressions. |
| `contracts.py`, `solvers.py` | Supply the minimum execution plumbing needed by those checks. |
| `proof_cases.py`, `solution_bundle.py` | Optional diagnostic conveniences; retained because they are already tested, not because WP3 requires them. |

The package is not normative, is not student starter code, and must not dictate
which algebraic modelling library a student uses. It should not receive new
features unless a reopen criterion is met.

## Frozen evidence

- `tests/test_physical_seed_model.py`
- `tests/test_recursive_model.py`
- `tests/test_solution_bundle.py`
- `solver_proof_cases/`

Focused verification:

```bash
pytest -q tests/test_physical_seed_model.py tests/test_recursive_model.py tests/test_solution_bundle.py
```

## Explicitly closed scope

WP3 will not add a complete required-output export pipeline, more proof-case
coverage, production solver orchestration, exhaustive status/fallback tests or
a reference application. CN-005 subsequently used the retained harness to
produce one public, independently replayable BASE calibration incumbent. That
narrow contract-maintenance action is not a model solution deliverable and
does not reopen WP3.

The required-output contracts remain standards for the consultant submission,
not a build list for the capstone author.

## Reopen criteria

Reopen this work only when:

- a controlled input or accounting contract changes materially;
- the full generator produces infeasible or unreconcilable data;
- scenario calibration fails to create meaningful decisions and trade-offs; or
- the retained authoring smoke test stops running in the supported environment.

Absent one of these triggers, effort moves to dataset generation, calibration,
the consultant brief, assessment standards and hidden evaluation controls.
