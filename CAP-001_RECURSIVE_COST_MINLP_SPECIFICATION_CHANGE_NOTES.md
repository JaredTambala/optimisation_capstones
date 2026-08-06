# CAP-001 Recursive-Cost MINLP Specification Change Notes

## Document control

| Field | Value |
|---|---|
| Change note | CN-001 — Four-tier recursive-cost sourcing with weighted-average pooling |
| Status | Proposed material change |
| Date | 30 July 2026 |
| Current specification | *CAP-001 Supplier Allocation Under Disruption Risk: Business Narrative, Modelling Decisions and Dataset Generation Specification* v0.2 |
| Proposed target | CAP-001 specification v0.3 |
| Change class | Material change to decision problem, mathematical class, datasets, outputs, reference implementation and assessment |
| Confirmed costing policy | Weighted-average pooling by node, material and planning period |
| Approval required from | Capstone owner, domain lead, optimisation lead, data lead and evaluation lead |

## 1. Executive change summary

CAP-001 v0.2 models a two-tier supply network with exogenous contract prices and a mixed-integer linear formulation. The proposed v0.3 changes the assessed problem to a four-tier sourcing and transformation network in which intermediate material costs are calculated recursively from the optimised mix of upstream inputs.

At each intermediate node, receipts and opening inventory are pooled. A weighted-average unit cost is calculated for the pool. Every consumption, shipment and closing-inventory movement from that pool carries the same calculated unit cost. Intermediate output cost is then calculated from:

- pooled input-material value;
- BOM quantities and yields;
- conversion cost;
- capitalised freight, duty and insurance;
- fixed order or shipment cost where applicable;
- configured supplier overhead or markup.

The resulting intermediate unit cost becomes an input to the next downstream tier. Because both unit cost and allocated quantity are decision-dependent, the model contains bilinear equalities and becomes a non-convex mixed-integer nonlinear programme.

This is not a minor extension to the current MILP. It changes:

- the network from two tier-specific stages to a generic four-tier directed acyclic graph;
- the core optimisation class from MILP to non-convex MINLP;
- the meaning of supplier prices and landed cost;
- the baseline and reference-solution strategy;
- raw-data contracts;
- standard output tables;
- deterministic validation;
- acceptable solver statuses and optimality claims;
- the application and presentation evidence expected from students.

## 2. Required change-control action

The change must be implemented through a new specification version, not only through ADR-003.

1. Increment the CAP-001 design specification from v0.2 to v0.3.
2. Mark the v0.2 two-tier MILP design as superseded for implementation.
3. Create an approved architecture decision covering the four-tier network and weighted-average pooling policy.
4. Replace the current model, data and output ADR sequence with the revised sequence in section 18 of this note.
5. Regenerate the delivery plan and requirements traceability matrix after v0.3 is approved.
6. Do not begin full dataset generation until the miniature recursive-cost fixture and reference-solver experiment pass.

## 3. Proposed revised decision statement

Replace the current decision question with:

> How should Asterion allocate sourcing, production and material flows across a four-tier supplier network so that fixed terminal-product demand is fulfilled, all intermediate material requirements are available at the correct nodes and times, and the recursively calculated weighted-average cost of terminal supply is minimised subject to commercial, capacity, inventory, lead-time and disruption constraints?

The intended learning challenge is not only to choose low-cost suppliers. Students must ensure that each downstream allocation is supported by feasible upstream volumes across every transformation tier and must reconcile how the selected upstream mix propagates into the final unit cost.

## 4. Revised business and network scope

### 4.1 Network structure

Release 1 should use four supplier tiers plus Asterion receiving plants:

```text
Tier 4 external raw-material sources
  -> Tier 3 processed materials and specialist subcomponents
    -> Tier 2 intermediate assemblies
      -> Tier 1 plant-ready components
        -> Asterion plants with fixed terminal-material demand
```

Tier numbering follows proximity to Asterion:

- Tier 1 supplies Asterion directly.
- Tier 4 is the most upstream external-price tier.
- A node may source different input materials from multiple approved nodes.
- A supplier organisation may own multiple nodes at one or more tiers.
- A material may have more than one approved transformation recipe where explicitly configured.
- Weighted-average pooling occurs only within an identical node-material-period pool using one authoritative unit of measure.
- The released production network must be acyclic for a given material-transformation lineage.

### 4.2 Preserved scope controls

The following v0.2 controls remain:

- fixed 12-week Monday-to-Sunday horizon;
- fixed terminal demand rather than demand forecasting;
- explicit approvals, contracts, capacities, lanes, inventory and lead times;
- MOQ, order multiples, fixed costs and activation decisions;
- BASE and controlled disruption scenarios;
- interactive decision-support application;
- private generation logic, reference results and hidden checks;
- same-period conversion within the weekly bucket; work-in-progress inventory and processing-lag valuation remain out of release 1;
- no ERP write-back, live tracking or rolling-horizon replanning in the initial release.

### 4.3 Revised release boundary

The v0.3 release must include the physical and cost basis required to calculate recursive prices. It must not rely on unexplained intermediate supplier prices.

- Exogenous unit prices are permitted only for configured external Tier 4 sources or explicitly declared external services.
- Tier 1–Tier 3 material prices are calculated by the model.
- Opening inventory must include both quantity and cost basis.
- Transformation cost, overhead and markup must be explicit.
- Freight, duty, insurance and fixed commercial costs must declare whether they are capitalised into material value or treated as non-capitalised period expense.
- Every cost must appear exactly once in either the recursive material-value ledger or the non-capitalised objective ledger.

### 4.4 Business authority and terminology

The revised narrative must explain why Asterion can optimise upstream allocations that are normally controlled by independent suppliers.

Recommended position:

- Asterion operates a nominated-source and open-cost programme for selected critical components.
- Participating Tier 1–Tier 3 suppliers provide approved BOM, source, conversion-cost and markup information.
- Asterion may nominate or constrain upstream sources and indicative volumes through its commercial agreements.
- The application produces a coordinated sourcing recommendation; supplier confirmation and purchase-order execution remain outside the capstone.

The variable \(u_{n,m,t}\) represents the calculated pooled landed or embedded unit cost at a node. It becomes a supplier price only after the configured conversion, overhead and markup rules have been applied. It must not be described as a legal invoice price where the commercial contract does not support that interpretation.

## 5. Core modelling decision

### 5.1 Model class

Replace:

> Mixed-integer linear programming is the core formulation.

With:

> A bounded, non-convex mixed-integer nonlinear programme is the core formulation. Nonlinearity arises from exact weighted-average pooling and recursive propagation of decision-dependent unit costs through multiple tiers. A fixed-price MILP is retained as a required baseline and diagnostic comparator.

### 5.2 Tier-neutral principal sets

| Set | Meaning |
|---|---|
| \(N\) | Supplier sites and Asterion plant nodes |
| \(M\) | Raw, intermediate and terminal materials |
| \(T\) | Weekly planning periods |
| \(A\) | Approved material-flow arcs |
| \(R\) | Transformation recipes |
| \(K\) | Commercial contracts |
| \(L\) | Shipping lanes or modes |
| \(\Omega\) | BASE and disruption scenarios |

Each node has a `node_tier` in `{TIER_1, TIER_2, TIER_3, TIER_4, PLANT}`. The equations should use node and arc relationships rather than hard-coded `s2`, `s1` and plant variable families.

### 5.3 Required quantity variables

| Variable | Type | Meaning |
|---|---|---|
| \(x_{a,m,t}\) | Continuous | Quantity dispatched on approved arc \(a\) |
| \(arr_{a,m,t}\) | Continuous or derived | Quantity arriving after the configured lag |
| \(p_{n,r,t}\) | Continuous | Output quantity produced using recipe \(r\) at node \(n\) |
| \(cons_{n,r,m,t}\) | Continuous or derived | Input material consumed by the recipe |
| \(I_{n,m,t}\) | Continuous | End-of-period inventory quantity |
| \(serve_{n,m,t}\) | Continuous | Terminal demand fulfilled |
| \(short_{n,m,t}\) | Continuous | Terminal demand shortage |
| \(order\_on_{k,t}\) | Binary | Contract-order activation |
| \(lots_{k,t}\) | Non-negative integer | Number of order multiples |
| \(recipe\_on_{n,r,t}\) | Binary where required | Transformation activation |
| \(pool\_on_{n,m,t}\) | Binary | Indicates a positive material pool |

### 5.4 Required cost and value variables

| Variable | Type | Meaning |
|---|---|---|
| \(u_{n,m,t}\) | Continuous, bounded | Weighted-average unit cost of the available pool |
| \(Q^{pool}_{n,m,t}\) | Continuous | Quantity available in the period pool before outflows |
| \(V^{pool}_{n,m,t}\) | Continuous | Value available in the period pool before outflows |
| \(V^{inv}_{n,m,t}\) | Continuous | End-of-period inventory value |
| \(V^{ship}_{a,m,t}\) | Continuous | Material value dispatched on an arc before receipt additions |
| \(V^{receipt}_{a,m,t}\) | Continuous | Receipt value after capitalised lane/commercial additions |
| \(V^{cons}_{n,r,m,t}\) | Continuous | Pooled value consumed by a transformation |
| \(V^{prod}_{n,r,t}\) | Continuous | Value of recipe output before pooling with existing stock |
| \(V^{serve}_{n,m,t}\) | Continuous | Value assigned to fulfilled terminal demand |

All unit-cost variables require finite, defensible lower and upper bounds. Quantity pools also require finite upper bounds. Bound construction is part of the assessed model design and the private reference implementation.

## 6. Weighted-average pooling equations

### 6.1 Quantity pool

For each node, material and period:

\[
Q^{pool}_{n,m,t}
=
I_{n,m,t-1}
+\sum_{a\in\delta^-(n,m)} arr_{a,m,t}
+\sum_{r:\,out(r)=m} p_{n,r,t}
\]

Opening inventory replaces \(I_{n,m,0}\) in P01.

Release 1 preserves the v0.2 convention that receipts and completed production are available within their recorded weekly period. Conversion consumes its inputs and produces its output within the same weekly bucket. A later version may introduce explicit production starts, completion lags and work-in-progress value.

### 6.2 Value pool

\[
V^{pool}_{n,m,t}
=
V^{inv}_{n,m,t-1}
+\sum_{a\in\delta^-(n,m)} V^{receipt}_{a,m,t}
+\sum_{r:\,out(r)=m} V^{prod}_{n,r,t}
\]

### 6.3 Weighted-average unit cost

\[
V^{pool}_{n,m,t}
=
u_{n,m,t}Q^{pool}_{n,m,t}
\]

This bilinear equality is the core weighted-average pooling rule.

When \(Q^{pool}_{n,m,t}=0\), the unit cost must be fixed to zero rather than left indeterminate. The implementation must link pool activation, quantity and unit cost using approved bounds and a documented minimum meaningful quantity or equivalent indicator formulation.

### 6.4 Quantity outflow balance

\[
Q^{pool}_{n,m,t}
=
I_{n,m,t}
+\sum_{a\in\delta^+(n,m)}x_{a,m,t}
+\sum_r cons_{n,r,m,t}
+serve_{n,m,t}
\]

Only the applicable outflow terms are active for each node and material.

### 6.5 Common pool valuation of outflows

All outflows from the same node-material-period pool carry the same unit cost:

\[
V^{inv}_{n,m,t}=u_{n,m,t}I_{n,m,t}
\]

\[
V^{ship}_{a,m,t}=u_{n,m,t}x_{a,m,t}
\]

\[
V^{cons}_{n,r,m,t}=u_{n,m,t}cons_{n,r,m,t}
\]

\[
V^{serve}_{n,m,t}=u_{n,m,t}serve_{n,m,t}
\]

These equalities prevent the optimiser from assigning low value to demand and high value to residual inventory selectively.

### 6.6 Pool value conservation

The following reconciliation must hold within numerical tolerance:

\[
V^{pool}_{n,m,t}
=
V^{inv}_{n,m,t}
+\sum_{a\in\delta^+(n,m)}V^{ship}_{a,m,t}
+\sum_r V^{cons}_{n,r,m,t}
+V^{serve}_{n,m,t}
\]

This equality is both a model control and a deterministic post-solve acceptance check.

The reference formulation may omit algebraically redundant value equalities where retaining them would damage numerical conditioning. It must still emit enough detailed evidence for every pooling and value-conservation identity above to be recomputed independently.

## 7. Recursive transformation cost

### 7.1 BOM consumption

For recipe \(r\), input material \(m\) and output quantity \(p_{n,r,t}\):

\[
cons_{n,r,m,t}
=
\frac{a_{r,m}}{\eta_{n,r}}p_{n,r,t}
\]

where \(a_{r,m}\) is the BOM coefficient and \(\eta_{n,r}\) is the fixed yield.

### 7.2 Production value

The output value of a transformation must reconcile:

\[
V^{prod}_{n,r,t}
=
\sum_m V^{cons}_{n,r,m,t}
+c^{variable}_{n,r,t}p_{n,r,t}
+F^{setup}_{n,r}recipe\_on_{n,r,t}
+C^{other}_{n,r,t}
\]

If the supplier applies a fixed cost-plus markup:

\[
V^{prod}_{n,r,t}
=
(1+\mu_{n,r})
\left(
\sum_m V^{cons}_{n,r,m,t}
+c^{variable}_{n,r,t}p_{n,r,t}
+F^{setup}_{n,r}recipe\_on_{n,r,t}
\right)
\]

The specification must choose one markup convention and apply it consistently. Release 1 should use configured, exogenous markup rates; markup optimisation or negotiation remains out of scope.

### 7.3 Shipment and receipt value

The goods value dispatched from an intermediate node is:

\[
V^{ship}_{a,m,t}=u_{origin(a),m,t}x_{a,m,t}
\]

The receipt value at the destination is:

\[
V^{receipt}_{a,m,t'}
=
V^{ship}_{a,m,t}
+C^{freight}_{a,m,t}
+C^{duty}_{a,m,t}
+C^{insurance}_{a,m,t}
+C^{capitalised\ fixed}_{a,m,t}
\]

where \(t'\) is the derived arrival period. Fixed FX rates, duty percentages and insurance percentages may multiply value variables because their rates are fixed coefficients.

### 7.4 External Tier 4 prices

For a configured external-price source:

\[
V^{ship}_{a,m,t}
=
c^{external}_{a,m,t}x_{a,m,t}
\]

Only these boundary prices are exogenous. Intermediate Tier 1–Tier 3 unit costs must not be supplied as authoritative raw inputs.

## 8. Objective and anti-gaming controls

### 8.1 Lexicographic service protection

Stage 1 remains:

\[
\min \sum_{n,m,t}w_{n,m,t}short_{n,m,t}
\]

The generated BASE case must permit zero weighted shortage.

### 8.2 Recursive-cost objective

At the zero-shortage level, Stage 2 should minimise the value of terminal demand together with closing inventory value across the controlled network and non-capitalised costs:

\[
\min
\sum_{n\in PLANT,m,t}V^{serve}_{n,m,t}
+\sum_{n,m}V^{inv}_{n,m,T}
+C^{noncapitalised}
\]

The final objective definition must ensure that buying surplus low-cost material cannot reduce the weighted-average cost assigned to demand while leaving the acquisition cost unpenalised.

The reference design must therefore use at least one of these controls:

1. include closing-inventory value at every controlled network node in the objective;
2. apply fixed or tightly bounded terminal-inventory targets;
3. minimise non-duplicated external spend and value-add costs alongside terminal unit cost;
4. use a lexicographic tertiary objective that minimises surplus and trapped value.

The chosen treatment must be fixed in an ADR and demonstrated with an explicit dilution-gaming negative test.

Release 1 should prohibit dispatches that arrive after P12. A later version may allow them only if the corresponding in-transit quantity and value are represented explicitly in the objective and balance sheets.

### 8.3 No double counting

The specification must distinguish:

- **capitalised costs**, which enter the recursive material-value ledger and propagate into terminal unit cost; and
- **non-capitalised costs**, which enter the objective separately.

A cost may not appear in both categories. The objective must not sum intermediate material values and terminal material values as if they were independent expenditures.

### 8.4 Opening inventory treatment

Each opening inventory record must include a quantity and cost basis. The ADR must state whether opening value is:

- an accounting cost participating fully in weighted-average cost of demand; or
- a sunk cost reported separately from incremental procurement spend.

Recommended release-1 treatment: use opening book value in the weighted-average pool, report both accounting cost of terminal demand and incremental new spend, and make the primary objective treatment explicit.

## 9. Revised baseline and student task

### 9.1 Required fixed-price MILP baseline

Retain a linear diagnostic baseline:

- use fixed, explicitly baseline-only standard intermediate costs;
- enforce the same physical network, BOM, yield, capacity, lane, MOQ, order-multiple, activation, inventory and lead-time constraints;
- minimise weighted shortage first and fixed-price operational cost second;
- solve BASE and all supplied scenarios;
- do not claim that it reproduces recursive supplier price formation.

### 9.2 Required recursive-cost MINLP

Every student must:

1. implement or reproduce the physical four-tier network;
2. implement exact weighted-average pooling;
3. calculate intermediate output values recursively;
4. reconcile every pool and transformation;
5. compare the recursive-cost result with the fixed-price MILP baseline;
6. report solution status, bounds, optimality gap and runtime honestly;
7. test every required disruption scenario;
8. explain how upstream allocation changes terminal unit cost;
9. identify limitations of the non-convex solve;
10. disclose any relaxation, discretisation or approximation and quantify its recursive-cost reconciliation error.

Students may use a direct MINLP, spatial relaxation, piecewise approximation, decomposition or an exact algebraically equivalent reformulation. Method choice does not remove the obligation to reproduce the weighted-average costing policy, emit the standard evidence and describe whether the result is exact, relaxed or approximate.

### 9.3 Resilience requirement

The resilience challenge remains, but it must not obscure the core recursive-cost requirement. The student must first demonstrate a valid BASE recursive-cost model. A resilience intervention then extends or constrains that model.

## 10. Raw-data contract changes

The data model must become tier-neutral. The following table records the minimum changes to the v0.2 contracts.

| v0.2 file | v0.3 action | Required change |
|---|---|---|
| `planning_calendar.csv` | Retain | No conceptual change |
| `supplier_organisations.csv` | Retain and extend | Support organisations operating at multiple tiers |
| `supplier_sites.csv` | Replace with `network_nodes.csv` | Include supplier sites and plant nodes; add `node_type`, `node_tier`, processing capability and pooling policy |
| `plants.csv` | Retain as a plant extension | One-to-one plant metadata keyed to its `network_nodes.csv` record |
| `materials.csv` | Extend | Add generic material stage, poolability, external-price flag and terminal-material flag |
| `bill_of_materials.csv` | Replace | Split into `transformation_recipes.csv` and `transformation_inputs.csv` |
| `supplier_material_approvals.csv` | Generalise | Permit supplier-site buyers at every downstream tier and plants |
| `supply_contracts.csv` | Modify | Add pricing method; exogenous unit price permitted only for external sources; retain MOQ, lots, fixed costs and dates |
| `incoterm_rules.csv` | Extend | Add explicit capitalisation flags for freight, duty and insurance |
| `import_duty_rates.csv` | Retain | Apply to configured customs value using fixed rules |
| `supplier_capacity.csv` | Generalise | Capacity by node, material or recipe and period |
| `shipping_lanes.csv` | Retain and generalise | Permit arcs between every adjacent approved tier |
| `opening_inventory.csv` | Extend | Add opening unit cost, opening value and cost-basis source |
| `plant_demand.csv` | Rename to `terminal_demand.csv` | Demand only terminal plant-required materials |
| `supplier_performance_history.csv` | Retain | Support all supplier tiers |
| `incident_history.csv` | Retain | Support node, organisation, region, lane and material targets |
| `disruption_scenarios.csv` | Retain | Revise narratives/targets for four tiers |
| `disruption_impacts.csv` | Generalise | Tier-neutral node, arc, recipe, region, material and demand targets |
| `fx_rates.csv` | Retain | Fixed conversion into EUR |

### 10.1 New required files

| File | Purpose |
|---|---|
| `transformation_recipes.csv` | Defines node-capable outputs, yield, activation and effective periods |
| `transformation_inputs.csv` | Defines input materials and coefficients for each recipe |
| `external_source_prices.csv` | Provides exogenous price only at approved external Tier 4 boundaries |
| `conversion_costs.csv` | Provides variable conversion, fixed setup, overhead and configured markup |
| `cost_allocation_rules.csv` | Declares which freight, duty, insurance, fixed and holding costs are capitalised |
| `baseline_standard_costs.csv` | Provides explicitly non-authoritative fixed intermediate costs for the diagnostic MILP only |
| `opening_inventory.csv` additions | Provide opening quantity, unit cost and total value with reconciliation |

### 10.2 Prohibited raw inputs

The student release must not contain:

- intermediate unit prices used as authoritative inputs to the recursive MINLP;
- precomputed weighted-average pool costs;
- precomputed terminal-product costs;
- reference sourcing paths or source-contribution shares;
- reference MINLP solutions, bounds or objective ranges.

`baseline_standard_costs.csv` is permitted only when it is clearly labelled as a comparator input and the recursive MINLP is prevented from reading it.

## 11. Revised standard output contract

Replace tier-specific output filenames with generic four-tier evidence.

| Output | Minimum grain | Required evidence |
|---|---|---|
| `orders.csv` | Contract-material-dispatch period | Activation, lots, quantity, external price where applicable and fixed cost |
| `shipments.csv` | Arc-material-dispatch/arrival period | Quantity, source pool unit cost, dispatched value, capitalised additions and receipt value |
| `production.csv` | Node-recipe-period | Output quantity, input quantities/values, yield, conversion cost, markup and output value |
| `inventory_cost_rollforward.csv` | Node-material-period | Opening quantity/value, receipts, production, pool quantity/value/unit cost, outflows and closing quantity/value |
| `demand_service.csv` | Plant-terminal material-period | Demand, fulfilment, shortage, unit cost and fulfilled value |
| `cost_component_ledger.csv` | Cost category-entity-period | Capitalised and non-capitalised cost with a unique ledger classification |
| `recursive_cost_reconciliation.csv` | Node-material-period or recipe-period | Quantity and value residuals for every pooling and transformation equality |
| `constraint_report.csv` | Constraint family-entity-period | LHS, RHS, residual/violation and applicable bound information |
| `scenario_comparison.csv` | Plan-scenario | Service, terminal unit cost, terminal value, inventory value, runtime, bound/gap and resilience measures |

Common `run_metadata.json`, `metrics.json` and baseline-comparison evidence remain required. Run metadata must add formulation type, exact/relaxed/approximate classification, solver termination, primal objective, global or relaxation bound where available, absolute gap, relative gap and number of starts.

## 12. Dataset-generation changes

The generator must:

1. create a four-tier acyclic transformation graph;
2. ensure each important downstream material has multiple feasible upstream sourcing combinations;
3. create shared upstream dependencies across apparently diverse Tier 1 suppliers;
4. generate coherent external prices, conversion costs, markups, freight and FX;
5. derive plausible lower and upper unit-cost bounds for every node-material-period;
6. generate opening inventory quantity and book value consistently;
7. create sufficient physical capacity for a zero-shortage BASE solution;
8. make the fixed-price MILP and recursive-cost MINLP choose materially different sourcing in at least one controlled case;
9. ensure weighted-average pooling affects terminal cost rather than serving only as a reporting calculation;
10. include a case where a locally attractive downstream supplier is expensive after upstream cost recursion;
11. include a case where multi-sourcing changes an intermediate weighted-average cost;
12. prevent unbounded inventory acquisition or weighted-average dilution;
13. keep the reference instance small enough for controlled non-convex optimisation;
14. generate a larger extension instance for heuristic or decomposition work only after the reference case is stable.

## 13. Deterministic validation changes

### 13.1 Physical checks

Retain and generalise:

- approval, contract and lane validity;
- MOQ, lot and activation reconciliation;
- node/recipe and lane capacity;
- BOM and yield consumption;
- dispatch/arrival timing;
- inventory non-negativity;
- demand and shortage reconciliation;
- scenario targeting and recovery.

### 13.2 Weighted-average cost checks

Add:

- `pool_quantity = opening_inventory + receipts + production`;
- `pool_value = opening_inventory_value + receipt_value + production_value`;
- `pool_value = pool_unit_cost × pool_quantity`;
- every outflow uses the same node-material-period pool unit cost;
- closing inventory value equals pool unit cost × closing quantity;
- dispatched material value equals pool unit cost × dispatched quantity;
- consumed input value equals pool unit cost × consumed quantity;
- terminal served value equals pool unit cost × served quantity;
- pool value equals the value of all outflows plus closing inventory;
- production output value equals input values plus declared conversion, fixed and markup additions;
- receipt value equals dispatched value plus declared capitalised additions;
- no cost appears in both capitalised and non-capitalised ledgers;
- zero-quantity pools have zero unit cost and value;
- all cost and quantity residuals fall within declared absolute and relative tolerances.

### 13.3 Anti-gaming checks

Add targeted tests for:

- surplus low-cost purchasing used to dilute terminal unit cost;
- arbitrary cost assignment between demand and closing inventory;
- unbounded or weakly bounded unit-cost variables;
- zero-quantity pools with arbitrary unit cost;
- cost disappearing between tiers;
- cost counted more than once;
- expensive opening inventory being ignored contrary to the configured policy;
- fixed costs being excluded from recursive value;
- markups being applied repeatedly or to the wrong cost base.

## 14. Reference-solver and reproducibility changes

The existing Pyomo/HiGHS-only reference position is insufficient for the recursive MINLP. Revise the reference strategy as follows:

- retain HiGHS or another MILP solver for the fixed-price baseline and linear relaxations;
- select an approved non-convex MINLP-capable reference solver through ADR and benchmark evidence;
- record whether the solver provides a global bound, only a local solution, or a heuristic feasible solution;
- use finite variable bounds and deterministic solver settings;
- run multiple starts where the chosen solver is local;
- retain full solver logs, termination reason, primal objective, bound, absolute gap and relative gap;
- use a miniature instance to verify equations independently of solver performance;
- maintain exact or best-known reference results rather than asserting global optimality without proof;
- define time limits separately for baseline, miniature reference and full student case;
- document any licensed solver requirement and provide an accessible fallback route for students.

The final solver choice remains an ADR decision. The specification must not name `optimal` as an expected status unless the selected method supplies a defensible global certificate.

The output contract should distinguish at least:

- `globally_optimal`, supported by an accepted global certificate and gap;
- `locally_optimal`, supported only by local termination conditions;
- `feasible_time_limited` or `best_found`;
- `infeasible`, supported by appropriate evidence;
- `solver_failed`.

An approximation or relaxation must additionally report its formulation type and any known approximation or relaxation gap.

## 15. AI-assisted evaluation changes

The AI evaluator must receive deterministic physical and recursive-cost reconciliation before qualitative scoring.

Add mandatory flags for:

- intermediate prices treated as unexplained exogenous inputs;
- omitted opening inventory cost basis;
- failure to use weighted-average pooling;
- different unit costs assigned to simultaneous outflows from one pool;
- missing bilinear cost/quantity links;
- incorrect propagation of freight, duty, insurance, conversion cost or markup;
- double-counted intermediate and terminal values;
- terminal-cost claims that do not reconcile to upstream inputs;
- weighted-average dilution through surplus inventory;
- claims of global optimality unsupported by a global bound;
- comparison of solutions that use different physical constraints;
- resilience conclusions based on physically or financially unreconciled results.

Qualitative scoring should reward:

- transparent explanation of recursive cost;
- defensible bounds and scaling;
- appropriate solver strategy for non-convexity;
- honest interpretation of local versus global results;
- clear visual explanation of how upstream source mix changes terminal cost;
- production reasoning about data lineage, cost ownership and audit.

## 16. Application and presentation changes

The application should add:

- a four-tier network explorer;
- node/material pool quantity and weighted-average unit-cost views;
- a recursive cost waterfall from external source to terminal demand;
- comparison of fixed-price MILP and recursive-cost MINLP allocations;
- source-mix contribution to each intermediate and terminal cost;
- scenario impacts on both physical availability and propagated unit cost;
- solver status, primal bound, global/lower bound where available, gap and runtime;
- clear warnings for locally optimal, feasible time-limited or unreconciled results.

The presentation should explicitly answer:

1. Why does fixed-price tier-by-tier optimisation fail to capture the customer problem?
2. How does weighted-average pooling work?
3. Where does non-convexity enter?
4. How were variable bounds and solver strategy chosen?
5. How does the recursive solution differ from the fixed-price baseline?
6. Which upstream sources drive terminal cost?
7. What confidence can be placed in the reported solution?
8. What additional controls are needed for production cost accounting and audit?

## 17. Production-readiness additions

The production extension must address:

- authoritative ownership of external prices, conversion costs, markups and opening book values;
- reconciliation with ERP inventory valuation and supplier cost-breakdown data;
- treatment of retroactive price changes and FX corrections;
- versioning of recipes, cost-allocation rules and cost bases;
- audit trail from terminal unit cost to source quantities and value additions;
- solver warm starts and preservation of incumbent solutions;
- operational fallback to the fixed-price MILP if the MINLP service is unavailable;
- detection of unstable unit costs caused by small pool quantities;
- privacy and commercial sensitivity of supplier cost build-ups;
- governance of supplier-provided cost and markup assumptions.

## 18. Revised ADR sequence

Replace the current ADR sequence with:

1. **ADR-001 — Business narrative and four-tier release scope.**
2. **ADR-002 — Tier-neutral network, transformation graph and time semantics.**
3. **ADR-003 — Weighted-average pooling and opening inventory cost basis.**
4. **ADR-004 — Recursive production, shipment and receipt value equations.**
5. **ADR-005 — Capitalised versus non-capitalised cost and no-double-count policy.**
6. **ADR-006 — Objective hierarchy, terminal inventory and anti-dilution treatment.**
7. **ADR-007 — MOQ, lot, activation, fixed-cost and capacity formulation.**
8. **ADR-008 — Scenario transformation across four tiers.**
9. **ADR-009 — Synthetic graph, cost distributions and unit-cost bounds.**
10. **ADR-010 — Reference MINLP solver, starts, tolerances, bounds and time limits.**
11. **ADR-011 — Output schemas, reconciliation tolerances and rounding.**
12. **ADR-012 — Student solver-access and fallback policy.**

## 19. Section-by-section amendments to v0.2

| v0.2 section | Required v0.3 amendment |
|---|---|
| Document control | Increment version; record material MINLP redesign and precedence |
| §1 Purpose | Replace two-tier MILP implementation-ready claim with four-tier recursive-cost MINLP purpose |
| §2 Executive summary | Add weighted-average pooling, endogenous intermediate cost and fixed-price baseline |
| §3 Decision register | Replace optimisation class, network, cost, reference and output decisions |
| §4 Business workflow | Add recursive-cost reconciliation and baseline/MINLP comparison |
| §5 Scope | Add four tiers and cost-basis inputs; prohibit unexplained intermediate prices |
| §6 Network design | Replace Tier 2/Tier 1 spine with generic four-tier DAG and transformations |
| §7 Formulation | Replace tier-specific MILP variables/equations with quantity/value/unit-cost MINLP |
| §8 Baseline | Convert current baseline to fixed-price diagnostic MILP; add required recursive MINLP |
| §9 Scenarios | Retarget scenario impacts across four tiers and cost propagation |
| §10 Dataset structure | Replace tier-specific files with generic network/transformation/cost contracts |
| §11 Data contracts | Add recipes, recipe inputs, external prices, conversion costs, cost-allocation rules and opening values |
| §12 Generation | Generate cost-recursive trade-offs, bounds and anti-dilution cases |
| §13 Validation | Add pool, value, transformation, receipt and no-double-count reconciliation |
| §14 Student requirements | Require recursive model, baseline comparison, bounds/gap and cost-lineage application views |
| §15 Reference/evaluation | Replace MILP-only reference with baseline MILP plus non-convex MINLP strategy |
| §16 Work packages | Add miniature model, solver benchmark and recursive-cost calibration before release |
| §17 Parameters/ADRs | Replace with the 12-ADR sequence in this note |
| Appendix A | Replace release checklist with MINLP-specific acceptance conditions |
| Appendix B | Add exact recursive-cost student instruction |
| Appendix C | Retain ADR template |
| Appendix D | Replace tier-specific tables with the generic output contract in section 11 |

## 20. Proposed implementation work-package changes

| WP | Revised purpose | Acceptance condition |
|---|---|---|
| WP1 | Decision configuration and tier-neutral schemas | Configuration generates network, transformation, cost and output schemas |
| WP2 | Miniature hand-worked recursive-cost fixture | Quantity and value reconcile manually across all four tiers |
| WP3 | Reference-solver proof of concept | At least one feasible bounded MINLP solve reproduces the fixture |
| WP4 | Four-tier dimension and graph generation | Graph is acyclic, connected and contains controlled multi-sourcing |
| WP5 | Commercial, recipe and cost generation | External prices and all cost additions reconcile without intermediate exogenous prices |
| WP6 | Planning facts, inventory cost basis and scenarios | BASE is physically feasible and cost pools are well bounded |
| WP7 | Fixed-price MILP and recursive-cost MINLP references | Both models solve and their differences are explainable |
| WP8 | Calibration, bounds and anti-gaming tests | Reference results are stable and dilution/double-count tests fail correctly |
| WP9 | Student release and application contract | Release provides all inputs without leaking calculated costs or references |
| WP10 | Deterministic and AI-assisted evaluation harness | Sample submissions are checked and scored reproducibly |

## 21. Release-1 acceptance additions

Do not approve v0.3 release until:

- the four-tier graph is acyclic and internally consistent;
- every terminal material has a feasible upstream supply tree;
- important nodes have multiple input sources;
- BASE has a zero-shortage physical solution;
- opening quantity and value reconcile;
- every pool quantity, pool value and unit cost reconcile;
- every transformation reconciles input value, conversion additions and output value;
- every shipment reconciles source value and receipt additions;
- every terminal unit cost can be traced to upstream sources;
- no cost is lost or double counted;
- weighted-average dilution tests are controlled;
- unit-cost and quantity bounds are defensible;
- the fixed-price MILP and recursive MINLP differ meaningfully in at least one decision;
- solver status, bound and gap reporting are validated;
- the miniature reference result is independently hand checked;
- the full case solves to an approved feasible quality within the runtime budget;
- student release data contain no authoritative intermediate prices or reference costs;
- the evaluation harness detects all specified physical and financial defects.

## 22. Remaining decisions required before v0.3 approval

The following decisions remain open and must be resolved explicitly:

1. Whether opening inventory book value is part of the primary objective or reported separately from incremental spend.
2. Which costs are capitalised at each transformation and receipt stage.
3. Exact supplier markup convention and cost base.
4. Treatment of holding cost in recursive value.
5. Treatment of terminal and intermediate closing inventory in the objective.
6. Whether alternative recipes may be blended or require exclusive activation.
7. Approved lower and upper bound construction for unit costs.
8. Reference MINLP solver and student-access policy.
9. Required global/local optimality evidence and accepted gap thresholds.
10. Full-case runtime budget and fallback evaluation behaviour.
11. Which disruption scenarios should change price, capacity, lead time, recipes or external cost simultaneously.
12. Whether the initial release should include all four tiers in every terminal material lineage or allow selected shorter chains.

These are implementation decisions within the confirmed weighted-average recursive-cost direction. They must not be left implicit in the dataset generator or reference model.
