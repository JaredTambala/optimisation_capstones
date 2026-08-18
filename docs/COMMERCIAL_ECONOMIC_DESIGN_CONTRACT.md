# CAP-001 Commercial and Economic Dataset Design Contract

## Document control

| Field | Value |
|---|---|
| Purpose | Define how the accepted network is commercialised and how its economic depth is assessed |
| Status | Completed and accepted; candidate, seed and thresholds frozen on 18 August 2026 |
| Date | 18 August 2026 |
| Governing sources | CAP-001 specification v0.3 §§7, 8, 11.2, 12.3–12.5 and 13.1 as amended by CN-003; decision configuration v0.3.1; accepted network candidate |
| Input | The frozen WP4 candidate in `capstones/CAP-001/generated/network/data/` |
| Scope | Contracts, simplified Incoterm rules, duties, lanes, external prices, conversion costs, cost-allocation rules, FX and baseline standard costs |
| Explicit non-scope | Demand, source and transformation capacity, inventory, scenarios, an optimised allocation, model-solution code and application implementation |

## 1. Design outcome

WP5 must turn the accepted physical network into a credible commercial decision
space. It succeeds when the data contains understandable economic tensions: for
example, low variable cost against high fixed cost, low price against long lead
time, or a cheap downstream quote against expensive recursively propagated
inputs. It does not succeed merely because every commercial table is populated.

The authoring objective is evidence about dataset depth and fidelity. WP5 is
not intended to produce a preferred sourcing plan or a model solution. A
candidate must still formulate an explicit MILP baseline and recursive-cost
MINLP, or a faithful declared approximation around those algebraic
formulations, in the assessed engagement.

WP5 can establish commercial coverage, coherent accounting and the presence of
potential trade-offs. It cannot establish BASE feasibility, scenario
materiality, binding capacity behaviour or final formulation bounds until the
WP6 planning data exists. Those combined claims belong to WP7.

## 2. Frozen input profile and expected output shape

The commercial generator consumes the accepted WP4 candidate without changing
its entities or relationships.

| Dataset | Candidate expectation | Basis |
|---|---:|---|
| `supply_contracts.csv` | 138 rows | One active contract for each approved material flow |
| `incoterm_rules.csv` | 6 rows | The complete controlled subset: EXW, FCA, CPT, CIP, DAP and DDP |
| `import_duty_rates.csv` | 138 rows | One full-horizon rule for each required origin/destination/material-family tuple in the accepted network |
| `shipping_lanes.csv` | 112–120 rows | One standard lane for each of 104 active node pairs, plus 8–16 deliberate expedited alternatives |
| `external_source_prices.csv` | 396 rows | 33 boundary contracts across 12 periods |
| `conversion_costs.csv` | 624 rows | 52 recipes across 12 periods |
| `cost_allocation_rules.csv` | 47 rows | Fourteen global component rules plus a source-stage surge override for each of 33 boundary contracts |
| `fx_rates.csv` | 216 rows | 18 currencies across 12 periods; EUR fixed at 1 |
| `baseline_standard_costs.csv` | 576 rows | 48 intermediate seller/material states across 12 periods |

These are consequences of the accepted candidate, not new scale targets. A
controlled change to the network must recalculate the expectations rather than
padding or dropping commercial rows to preserve these numbers.

## 3. Commercial conventions to close before generation

### 3.1 Leg-local data and the pricing boundary

The raw data must not label an internal leg as `RECURSIVE_COST_PLUS`. Recursion
is not a property of one contract row: it is the result of applying the common
pool and transformation accounting rules across the connected network. Such a
label would disclose the structure the candidate is expected to discover and
is redundant with the actual data relationships.

Before WP5 generation, remove `pricing_method` from the
`supply_contracts.csv` contract through a controlled WP1 schema amendment and
regenerate the schema and data dictionary. The column is currently unused by
the fixture reconciler and private data loader.

Each commercial and physical row then remains scoped to its own concerns:

- an approval states that a seller may supply a material to a buyer;
- a contract states currency, responsibility, handling, lot, fixed-cost,
  payment and effective-date terms for that approval;
- a lane states the available transport service between its two nodes;
- a recipe states how inputs become output at one processing node; and
- an external price row states a quoted price only where material enters the
  modeled network from an external Tier-4 boundary.

Boundary pricing is inferred from those relationships, not declared by a
contract label. A contract whose seller has `external_boundary_flag=true` must
have one positive external price row in every active period. Every other
contract must have no external price row. Its dispatched goods value is formed
from the seller's node/material/period pool under the accounting policy.

An external price attached to a non-boundary contract, or a missing price for
an active boundary contract, is a release-blocking error.

### 3.2 Incoterm accounting convention

The six Incoterm codes remain a deliberately simplified responsibility model,
not a legal or comprehensive logistics model. The following convention prevents
seller-borne cost from silently disappearing:

1. Contracts whose sellers are internal processing nodes use EXW or FCA only.
   Modelled post-handover carriage, insurance and import duty are therefore
   buyer-borne receipt additions. Under FCA, seller-side origin handling is
   represented in conversion or overhead before dispatch; it is not a separate
   lane charge.
2. Contracts whose sellers are external boundary nodes may use all six
   controlled codes. The external unit price is a quote on the named Incoterm
   basis and includes costs borne by the seller up to the simplified handover
   point.
3. Buyer-borne freight, fixed shipment, insurance and duty are added at receipt
   only when both the Incoterm responsibility flag and the applicable cost rule
   require the addition. Seller-included amounts are not added again.
4. The author generator retains a private quote build-up so that seller-included
   components can be checked for plausibility and exactly-once treatment. The
   released price remains the authoritative commercial quote; the build-up is
   calibration evidence, not another candidate input.
5. Contracts sharing an origin/destination pair use the same main-carriage,
   insurance and duty responsibility profile. A boundary pair with seller-paid
   main carriage has one active lane only. Expedited lane choice is offered only
   where carriage is buyer-controlled.
6. `buyer_pays_origin_transport` is responsibility metadata. The quantitative
   lane charge is the modelled post-handover transport charge; WP5 does not
   invent a separate origin-haul cost that the schema cannot express.

This convention should be recorded in ADR-005 before the candidate is promoted.
If owner review instead requires seller-paid main carriage on recursive internal
contracts, the raw contract must first be amended to represent that value
explicitly; generation must not work around the gap with an undocumented
assumption.

### 3.3 Currency and units

- Contract fixed costs and external prices use the contract currency.
- Conversion costs use the processing node's local currency.
- Freight uses a controlled carrier currency, normally the origin or a major
  corridor currency.
- Every populated currency has exactly one positive EUR conversion factor per
  period. EUR is exactly 1.
- Economic comparisons convert values to EUR and compare only like materials
  in their authoritative UOM. No implicit KG/EA conversion is permitted.
- Period movement is deterministic and deliberately modest in BASE; disruption
  multipliers are not embedded in the WP5 facts.

### 3.4 Single-ledger policy

The global rules use the following default treatment. More-specific rules may
override a global rule only through explicit precedence and may not create a
tie.

| Component | Capitalised | Stage | Basis | In transformation markup base |
|---|---|---|---|---|
| External purchase | Yes | Source | Quantity | No |
| Freight | Yes | Receipt | Quantity | No |
| Duty | Yes | Receipt | Goods value | No |
| Insurance | Yes | Receipt | Goods value | No |
| Fixed order | Yes | Receipt | Activation | No |
| Fixed shipment | Yes | Receipt | Activation | No |
| Conversion | Yes | Transformation | Quantity | Yes |
| Setup | Yes | Transformation | Activation | Yes |
| Overhead | Yes | Transformation | Direct | Yes |
| Surge | Yes | Transformation by default; source for a boundary-contract override | Quantity | No |
| Markup | Yes | Transformation | Goods value | No |
| Holding | No | None | Quantity | No |
| Activation | No | None | Activation | No |
| Shortage | No | None | Quantity | No |

Input pool value is independently included in the markup base. Markup is then
applied once to input value plus conversion, setup and eligible overhead. It is
not applied to freight, duty, insurance, surge, fixed commercial costs or a
previous markup.

Holding and relationship activation are Stage-2 period expenses. Shortage is
the separately reported Stage-1 service measure and is not added to material
value or duplicated in Stage 2. Every capitalised fixed amount must identify a
single receiving pool or transformation activation to which it is attributable.

### 3.5 Comparator isolation

`baseline_standard_costs.csv` is a deliberately imperfect diagnostic view of
intermediate cost, not an alternative source of truth. It is derived from a
controlled central point in the commercial cost envelope and then biased by
material, region and supplier profile. Both isolation flags must be true on
every row. The recursive data view must reject or exclude this table.

WP5 should deliberately create several cases in which a baseline standard-cost
ranking conflicts with the recursively propagated commercial ranking. This is
a precondition for a useful formulation comparison, not proof that two solved
models will choose differently; that proof is deferred to WP7.

## 4. Deterministic generation sequence

Generation is constructive and uses independent namespaced sub-seeds so a
change in one commercial family does not silently reshuffle unrelated facts.

1. **Resolve controlled policy.** Freeze the Incoterm convention, component
   classification, scope precedence, synthetic business ranges and private
   generation seed.
2. **Create relationship terms.** Generate one contract per approval. Assign
   currency, Incoterm, handling time, MOQ, order multiple, fixed order cost,
   horizon activation cost and payment terms as a coherent profile rather than
   independent random fields.
3. **Create logistics.** Derive route distance from node coordinates; choose a
   credible standard mode from geography and distance; then generate transit,
   variability, capacity, freight, fixed shipment, insurance and reliability.
   Add expedited alternatives only on selected decision-relevant corridors.
4. **Create border treatment.** Generate one deterministic duty rule for every
   required origin/destination/material-family tuple, including explicit zero
   rates for domestic or configured trade-bloc movements.
5. **Create boundary economics.** Generate base source economics by material
   family, supplier and region; form Incoterm-basis external quotes; generate
   the 12-period FX and price paths; retain the private seller-included quote
   build-up.
6. **Create transformation economics.** Generate conversion, setup, fixed and
   variable eligible overhead, and markup from process complexity, scale,
   supplier and region. Alternative recipes are calibrated together.
7. **Propagate conditional envelopes.** Traverse the acyclic material-state
   graph from Tier 4 to plants at representative feasible order quantities.
   Compute ranges for recursively formed goods value and landed additions
   without selecting an allocation.
8. **Create comparator costs.** Generate isolated baseline standard costs from
   the envelopes and introduce controlled, documented ranking differences.
9. **Assess and regenerate.** Run contract, accounting, plausibility,
   dominance and crossover checks. Reject the candidate if any release gate
   fails; do not hand-edit individual CSV rows into acceptance.

## 5. Economic depth scorecard

The accepted commercial candidate is assessed against the following frozen
thresholds. They were reviewed together with the generated profile and retained
witnesses on 18 August 2026.

| Metric | Frozen threshold |
|---|---:|
| Approved flows with exactly one active contract | 138 of 138 |
| Active node pairs with at least one standard lane | 104 of 104 |
| Boundary contracts with complete period prices | 33 of 33 |
| Intermediate contracts with an external price | 0 |
| Recipe-period combinations with conversion economics | 624 of 624 |
| Required currencies with complete period FX | 18 of 18 |
| Intermediate state-periods with isolated baseline standard cost | 576 of 576 |
| Terminal materials with at least two commercialised full-lineage envelopes | 8 of 8 |
| Distinct retained commercial trade-off witnesses | At least 16, with at least 2 supporting each terminal material |
| Fixed/variable or fixed/lot-size ranking crossovers | At least 4 receiving pools |
| Faster or more reliable options carrying a visible cost disadvantage | At least 4 corridors |
| Local/import, tariff or FX-exposure contrasts | At least 4 receiving pools |
| Multi-source pools whose representative blend changes weighted-average input cost materially | At least 4 intermediate pools |
| Baseline-versus-recursive ranking conflicts | At least 4 pools covering at least 2 terminal materials |
| Expedited lane alternatives | 8–16 corridors, including enough Asia–Europe coverage to support later SCN-02 calibration |
| Unexplained cost disappearance or duplicate ledger treatment | 0 |
| Undocumented strictly dominated active commercial options | 0 |

A retained witness identifies the contracts, lanes, recipes, periods, order
quantities, normalized EUR values and structural lineage involved. One witness
may satisfy more than one trade-off category, but there must still be at least
16 distinct witnesses.

For the accepted profile, a ranking reversal or cost-mix effect is considered
material when the normalized unit-cost difference is at least 3%. A service
premium is considered visible when the faster or more reliable option costs at
least 5% more at one representative order quantity. These are frozen dataset
calibration thresholds, not claims about universal industry economics.

## 6. Dominance and plausibility review

Dominance is tested over the common feasible order quantities supported by the
contracts and lanes, not at one arbitrary quantity. The audit uses the smallest
common feasible lot, a central common lot and the largest common audit lot no
greater than lane capacity. It compares normalized landed cost, transit,
reliability, MOQ/lot burden and recorded dependency exposure.

An option is not rejected merely because it is more expensive in BASE. A
higher-cost option may be commercially credible because it is faster, more
reliable, less concentrated or exposed to a different region or parent group.
If another option is no worse on every recorded dimension at every audit
quantity, the dominated option must be regenerated or retained with an explicit
later-scenario rationale.

Plausibility checks should emphasize relationships rather than one global price
range:

- expedited lanes are faster and more expensive than their standard pair;
- distance and mode explain freight and transit differences;
- worse payment, MOQ or fixed-cost terms can accompany a lower unit quote;
- duty is resolved from origin, destination and material family exactly once;
- conversion cost and setup burden reflect recipe complexity and scale;
- markup is non-negative, stable enough to be explainable and applied once;
- all price and cost movement is smooth unless an explicit later scenario
  changes it; and
- outliers are named in the report with their business rationale.

The generator configuration should hold reviewable ranges by material family,
region, mode and process class. Those private ranges are calibration controls,
not externally sourced market benchmarks and should not be described as such.

## 7. Conditional envelopes and the WP7 bound hand-off

WP5 produces finite *commercial* envelopes, conditional on explicitly listed
order quantities. For each reachable node/material/period it records:

- lower and upper recursively propagated unit-value estimates;
- lower and upper receipt additions by cost component;
- fixed-cost amortisation at each audit quantity;
- the alternatives that attain each edge of the envelope; and
- any baseline standard-cost ranking conflict.

This topological calculation is an assessor, not an optimiser. It must not
select a supply allocation or present its path minima as a reference solution.

Final safe bounds for shipment, production, inventory, pool value and common
unit cost require source capacity, transformation capacity, storage, demand and
opening inventory from WP6. WP7 must combine those facts with the WP5 cost
envelopes, document the resulting formulation bounds and test that retained
feasible plans do not touch an invalid artificial bound. WP5 therefore closes
the cost side of ADR-009 but does not claim to close the complete bound proof.

## 8. Minimal implementation shape

The implementation exists to produce and challenge the data. It should begin
with three plainly named files and reuse the existing schema runtime:

| File | Responsibility |
|---|---|
| `capstones/CAP-001/generator/generate_commercial_data.py` | Read the frozen network and deterministically write the nine commercial tables to an explicit target directory |
| `tooling/assess_commercial_data.py` | Independently validate coverage, accounting, plausibility, envelopes, dominance and retained witnesses |
| `tests/test_commercial_generation.py` | Test reproducibility and the required positive and adversarial commercial cases |

No Pyomo, PuLP, solver invocation, reference allocation or application code is
required in WP5. This does not relax the assessed formulation requirement; it
keeps the authoring implementation proportionate to its purpose.

Draft generation writes under `capstones/CAP-001/generated/commercial/` and
must not overwrite the student release. WP7 later composes the frozen network,
commercial and planning candidates into one release candidate.

## 9. Validation and evidence

The independent assessor must cover:

1. **Contract validation:** schemas, types, keys, domains, periods and foreign
   keys for all nine tables.
2. **Coverage:** every approval, pair, boundary price, recipe-period, currency,
   duty tuple and comparator state is complete and effective.
3. **Semantic controls:** pricing boundary, compatible Incoterm/lane use,
   currency availability, UOM consistency, mode/distance coherence and
   baseline isolation.
4. **Accounting controls:** unique rule resolution, no precedence ties,
   exactly-once capitalisation, valid markup base, attributable fixed costs and
   reconciliation of buyer-added versus seller-included boundary costs.
5. **Economic depth:** every scorecard metric in §5, with machine-readable
   witnesses rather than aggregate assertions.
6. **Reproducibility:** byte-identical data and evidence for the same seed and
   isolated changes when one namespaced seed changes.

Required retained evidence is:

- the nine generated CSVs;
- `commercial_depth_scorecard.json`;
- `tradeoff_witnesses.json`;
- `conditional_cost_envelopes.json`;
- private `external_price_build_up.json`;
- `COMMERCIAL_ECONOMIC_REPORT.md`;
- generation manifest, row counts and checksums; and
- the populated public `COST_POLICY.md` and cost-ledger dictionary.

Negative tests must include at least: a missing contract or lane, an internal
external price, missing FX or duty resolution, incompatible shared-pair
Incoterms, disappearing or duplicated seller-included cost, a cost-rule
precedence tie, markup on an ineligible component, baseline leakage, a removed
crossover and byte-level non-determinism.

## 10. Progress gates

WP5 should be delivered through four evidence-based gates.

1. **Policy ready:** the redundant `pricing_method` column has been removed
   through a controlled schema amendment; the owner agrees the Incoterm and
   ledger convention; ADR-005 records it; provisional economic bands and
   scorecard thresholds are visible.
2. **Candidate complete:** all nine datasets generate deterministically from
   the frozen network and pass contract and coverage checks.
3. **Depth demonstrated:** the independent report contains enough distinct,
   inspectable trade-off witnesses and no unexplained dominance or accounting
   failures.
4. **Owner accepted:** the owner reviews the ranges and witnesses, accepts or
   regenerates the candidate, and freezes the thresholds and exact data as the
   input to WP6.

Completion of these gates means the dataset has credible commercial depth. It
does not mean CAP-001 has an accepted solution. WP6 must add planning pressure,
and WP7 must demonstrate that the combined dataset remains feasible,
non-trivial and suitable for the intended consultant engagement.

## 11. Current candidate result

The first generated candidate passes all twenty-one technical gates. Its principal
results are:

| Measure | Result |
|---|---:|
| Contract coverage | 138 of 138 approvals |
| Lane coverage | 104 of 104 node pairs |
| Full boundary price series | 33 of 33 contracts |
| Intermediate external prices | 0 |
| Fixed/variable crossovers | 4 |
| Speed/reliability premiums | 12 |
| Tariff, FX or origin contrasts | 49 |
| Material intermediate-pool mix effects | 36 |
| Baseline-versus-derived ranking conflicts | 9 |
| Unexplained strictly dominated options | 0 |
| Documented diversification exceptions | 5 |
| Terminal materials with at least two trade-off witnesses | 8 of 8 |
| Synthetic plausibility-range failures | 0 |
| Accounting issues | 0 |

The deterministic candidate and independent evidence are under
`capstones/CAP-001/generated/commercial/`. All four WP5 progress gates pass:
the owner accepted the generated profile, its five documented diversification
exceptions, seed and scorecard thresholds on 18 August 2026. ADR-005 remains
subject to its separate formal reviewer approval before release.
