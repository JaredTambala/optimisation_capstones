# CAP-001 BASE Reference Benchmark

This directory contains a solved, independently validated BASE reference
incumbent. It is calibration evidence, not business input data, a prescribed
implementation, a unique allocation or a globally optimal answer.

## Pinned identity

- Dataset: `BASE` / `a298c1b63350cc2213c9bf06d437bba4b60919cb90fad3bd4a864570790339a0`
- Configuration: `0.3.6` / `42499253f0465faec5ecfba87f3d0620aece877fe9d9c8ddda28f4191b47387e`
- Model version: `0.3.1`
- Formulation: `MINLP`
- Method: `HEURISTIC`
- Status: `locally_optimal`

## Reference controls

- Stage 1 weighted shortage: `0`
- Stage 1 reproduction ceiling: `1e-05`
- Stage 2 recursive value and non-capitalised cost: `4466380.63`
- Stage 2 reproduction ceiling: `4511044.884`
- Served quantity: `9301.8` of `9301.8`
- Service rate: `100.00000000%`
- Independent physical checks: `21908`
- Maximum physical residual: `8.350729956e-06`
- Independent recursive-accounting checks: `10645`
- Maximum recursive-accounting residual: `0.001197530022`

## Required interpretation

`reference_solution.json` retains the complete incumbent decisions and value
state for replay. A candidate must reproduce the published service, accounting
and objective-quality controls under the pinned BASE data and configuration.
The candidate does not have to copy the retained allocation. A different plan
passes when it is independently valid, meets the published objective-quality
rules and explains material aggregate differences.

The reference method is deliberately disclosed as a heuristic: a private
local-fact physical-seed MILP produces an integer plan, then the exact recursive
value equations are solved for that plan. No synthetic intermediate-cost table
is used and no global-optimality claim is made. The `locally_optimal` status
describes the fixed-plan nonlinear value-equation solve; it is not an
optimality claim for the retained allocation.
