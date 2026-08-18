# CAP-001 Cost Policy

## Purpose

This document defines the accounting treatment candidates must apply to the
CAP-001 data. It is authoritative for capitalisation, markup eligibility and
the separation of material value from period expense. The machine-readable
rules are in `data/raw/cost_allocation_rules.csv`.

The policy does not prescribe a software library, solver or decomposition
strategy. Any implementation must still satisfy the task's algebraic
formulation, reconciliation and evidence requirements.

## Leg-local commercial data

Each raw row describes its own business concern:

- an approval identifies an allowed seller, buyer and material relationship;
- a contract supplies currency, Incoterm, handling, lot, fixed-cost, payment
  and effective-date terms;
- a lane supplies transport time, capacity, freight, insurance and reliability;
- a recipe supplies one local input-to-output transformation; and
- an external price supplies a quoted price where material enters the modeled
  network.

There is no contract-level label declaring the end-to-end valuation structure.
Candidates must resolve it from the relationships. An active contract whose
seller has `external_boundary_flag=true` has one external price for its
material in every active period. No other contract may use an external price.

## Cost-component dictionary

| Component | Capitalised | Stage | Allocation basis | Markup-eligible | Meaning |
|---|---|---|---|---|---|
| `EXTERNAL_PURCHASE` | Yes | `SOURCE` | `QUANTITY` | No | Quoted material value entering at an external boundary |
| `FREIGHT` | Yes | `RECEIPT` | `QUANTITY` | No | Buyer-borne variable main-carriage charge |
| `DUTY` | Yes | `RECEIPT` | `GOODS_VALUE` | No | Buyer-borne import duty on the configured customs basis |
| `INSURANCE` | Yes | `RECEIPT` | `GOODS_VALUE` | No | Buyer-borne insurance on goods value |
| `FIXED_ORDER` | Yes | `RECEIPT` | `ACTIVATION` | No | Contract order cost attributable to one receiving pool |
| `FIXED_SHIPMENT` | Yes | `RECEIPT` | `ACTIVATION` | No | Lane shipment cost attributable to one receiving pool |
| `CONVERSION` | Yes | `TRANSFORMATION` | `QUANTITY` | Yes | Variable processing cost per unit of recipe output |
| `SETUP` | Yes | `TRANSFORMATION` | `ACTIVATION` | Yes | Fixed recipe setup cost when the recipe is activated |
| `OVERHEAD` | Yes | `TRANSFORMATION` | `DIRECT` | Yes | Eligible fixed and variable recipe overhead |
| `SURGE` | Yes | `TRANSFORMATION`, or `SOURCE` under a boundary-contract override | `QUANTITY` | No | Incremental premium for capacity above the regular band |
| `MARKUP` | Yes | `TRANSFORMATION` | `GOODS_VALUE` | No | Supplier markup applied once to the eligible transformation base |
| `HOLDING` | No | `NONE` | `QUANTITY` | No | Period inventory-holding expense |
| `ACTIVATION` | No | `NONE` | `ACTIVATION` | No | Horizon relationship-use expense |
| `SHORTAGE` | No | `NONE` | `QUANTITY` | No | Stage-1 service measure, reported separately |

For a component and calculation context, retain every matching rule, select the
highest `precedence`, and fail if more than one rule remains at that precedence.
A scoped rule replaces the global treatment; it does not create another copy of
the component.

## Receipt value and Incoterm responsibility

The Incoterm table is a simplified modelling abstraction, not legal guidance.
For an internal processing-node seller, the release uses EXW or FCA. Modelled
post-handover carriage, insurance and import duty are buyer-borne receipt
additions. Under FCA, seller-side origin handling is already represented before
dispatch through conversion or overhead.

An external boundary quote is stated on the contract's Incoterm basis and
already includes costs borne by the seller up to the simplified handover point.
Buyer-borne components are then added from the lane and duty tables. A
seller-included component must not be added again.

Subject to the resolved component rules, receipt value is:

```text
dispatched goods value
+ buyer-borne variable freight
+ buyer-borne fixed shipment cost
+ buyer-borne insurance
+ buyer-borne import duty
+ attributable fixed order cost
```

`customs_value_basis` determines whether duty is calculated on goods alone or
goods plus applicable freight. All source-currency values are converted using
the dispatch period's `eur_per_currency_unit`.

## Transformation value and markup

Recipe input consumption uses the common unit value of the relevant
node/material/period pool. The eligible markup base is:

```text
input pool value
+ variable conversion
+ activated setup
+ eligible fixed and variable overhead
```

Apply the configured `markup_rate` once to that base. Do not mark up freight,
duty, insurance, surge, fixed order, fixed shipment or an earlier markup.
Alternative recipes remain separate transformations even when they produce the
same node/material output pool.

## Single-ledger rule

Every realised cost must appear exactly once:

- capitalised components enter material value at their declared stage and may
  propagate into later pools; or
- non-capitalised components enter the appropriate objective or reporting
  ledger without changing material value.

Do not sum intermediate material values again as independent expenditure after
they have propagated into downstream output. Fixed costs may be capitalised only
when their activation can be attributed to one receiving pool or recipe.
Shortage belongs to the lexicographic service stage and must not be duplicated
as Stage-2 material or period cost.

## Baseline comparator isolation

`baseline_standard_costs.csv` is permitted only for the diagnostic fixed-price
MILP. Every row is marked `baseline_only_flag=true` and
`prohibited_for_recursive_model_flag=true`. The assessed valuation route must
reject or exclude that file and derive intermediate value from the network
facts instead.

The baseline and assessed formulations must otherwise share the same physical,
commercial and timing controls. A difference in their decisions should arise
from valuation, not from silently removing MOQ, capacity, timing or eligibility
constraints from one formulation.

## Required reconciliation

The submitted evidence must allow independent recomputation of:

1. source value and every receipt addition;
2. pool quantity, pool value and common unit value;
3. recipe input, conversion, setup, overhead and markup value;
4. served and closing-inventory value;
5. every non-capitalised ledger item; and
6. the exactly-once classification of every cost-component entry.

Residuals must use the controlled tolerances. Missing components, duplicated
components, baseline leakage, invalid markup eligibility and unresolved rule
ties are validation failures.
