# CAP-001 Miniature Fixture — Accounting Walkthrough

Generated from the authored fixture by `python -m tooling.build_fixture_reconciliation`. Do not edit directly — every number here is the reconciler's own recomputed output.

## 1. Purpose and how to use it

This fixture is the miniature, fully hand-checkable proof that weighted-average pooling, transformation valuation and receipt capitalisation work before you attempt the full recursive model. Run `python -m tooling.validate_fixture` against the supplied raw fixture-input directory before moving on to the full dataset. This command validates and revalues the input fixture; it is not a validator for submitted model-output files.

## 2. What the fixture is

Five periods (P01–P05), three supplier tiers (Tier 4, Tier 3, Tier 2) plus three Asterion plants, connected by fifteen approved arcs. Sourcing, transformation output and dispatch quantities are all pinned by data (matched minimum-order-quantity, order-multiple and lane-capacity fields, and zero-storage fan-out origins), so the fixture has exactly one feasible physical realisation — it is an accounting oracle, not an optimisation exercise.

## 3. Which inputs carry signal

`network_nodes`, `materials`, `transformation_recipes`, `transformation_inputs`, `material_flow_approvals`, `supply_contracts`, `shipping_lanes`, `external_source_prices`, `source_capacity`, `transformation_capacity`, `conversion_costs`, `cost_allocation_rules`, `inventory_policies`, `opening_inventory`, `terminal_demand`, `incoterm_rules`, `import_duty_rates` and `fx_rates` all directly determine a control total. `supplier_organisations`, `supplier_performance_history`, `incident_history`, `disruption_scenarios`, `disruption_impacts`, and `plants` are present because every raw contract must exist for the fixture to validate, but none of their fields feed the BASE reconciliation — `disruption_impacts` in particular describes an inactive stress scenario, not BASE.

## 4. The accounting rules, in dependency order

4.1 Pool grain is `(node_id, material_id, period_id)`.
4.2 Opening inventory enters the pool at its book value, exactly as configured.
4.3 Quantity roll-forward: `pool_quantity = opening + receipts + production`.
4.4 Value roll-forward: `pool_value = opening_value + receipt_value + production_value`.
4.5 Weighted-average unit cost: `pool_value = unit_cost * pool_quantity`; when `pool_quantity = 0`, `unit_cost` is fixed to exactly `0`, never left undefined.
4.6 Common-outflow-cost rule: every outflow from a pool in a period — closing inventory, dispatch, consumption, service — uses that pool's one unit cost. No outflow may be priced differently from another leaving the same pool.
4.7 Receipt valuation: `receipt_value = dispatched_value + freight + duty + insurance + fixed_shipment + fixed_order`, where each addition is included only if its cost-allocation rule is capitalised AND (for freight/fixed-shipment/duty/insurance) the arc's Incoterm makes the buyer responsible for it.
4.8 Transformation valuation: markup is applied once, to the eligible base (input value plus conversion, setup and overhead where each is marked markup-eligible) — never to freight, duty, insurance or fixed costs, which already entered the pool upstream and re-enter only via input value.
4.9 Closing inventory retains value at every node, not only at plants.
4.10 Stage-2 assembly: `stage_2_value = total served value across every plant and demand period + total closing inventory value at every node in the terminal period + non-capitalised cost (zero here)`.

## 5. The worked walk-through

| Control total | Value |
|---|---:|
| NODE-0001 boundary origination quantity | units 100.0000000 |
| NODE-0001 boundary origination value | EUR 400.0000000 |
| NODE-0001 boundary origination unit cost | EUR/unit 4.0000000 |
| NODE-0002 boundary origination quantity | units 110.0000000 |
| NODE-0002 boundary origination value | EUR 220.0000000 |
| NODE-0002 boundary origination unit cost | EUR/unit 2.0000000 |
| NODE-0003 boundary origination quantity | units 100.0000000 |
| NODE-0003 boundary origination value | EUR 300.0000000 |
| NODE-0003 boundary origination unit cost | EUR/unit 3.0000000 |
| LANE-00001 boundary receipt value (NODE-0001->NODE-0004) | EUR 258.0000000 |
| LANE-00002 boundary receipt value (NODE-0001->NODE-0005) | EUR 174.0000000 |
| LANE-00003 boundary receipt value (NODE-0002->NODE-0006) | EUR 182.0000000 |
| LANE-00004 boundary receipt value (NODE-0002->NODE-0008) | EUR 72.0000000 |
| LANE-00005 boundary receipt value (NODE-0003->NODE-0006) | EUR 172.0000000 |
| LANE-00006 boundary receipt value (NODE-0003->NODE-0007) | EUR 169.0000000 |
| NODE-0004 Tier-3 input pool quantity (MAT-0001) | units 60.0000000 |
| NODE-0004 Tier-3 input pool value (MAT-0001) | EUR 258.0000000 |
| NODE-0004 Tier-3 input pool unit cost (MAT-0001) | EUR/unit 4.3000000 |
| NODE-0005 Tier-3 input pool quantity (MAT-0001) | units 40.0000000 |
| NODE-0005 Tier-3 input pool value (MAT-0001) | EUR 174.0000000 |
| NODE-0005 Tier-3 input pool unit cost (MAT-0001) | EUR/unit 4.3500000 |
| NODE-0006 Tier-3 input pool quantity (MAT-0002) | units 150.0000000 |
| NODE-0006 Tier-3 input pool value (MAT-0002) | EUR 402.0000000 |
| NODE-0006 Tier-3 input pool unit cost (MAT-0002) | EUR/unit 2.6800000 |
| NODE-0007 Tier-3 input pool quantity (MAT-0002) | units 50.0000000 |
| NODE-0007 Tier-3 input pool value (MAT-0002) | EUR 169.0000000 |
| NODE-0007 Tier-3 input pool unit cost (MAT-0002) | EUR/unit 3.3800000 |
| NODE-0008 Tier-3 input pool quantity (MAT-0002) | units 30.0000000 |
| NODE-0008 Tier-3 input pool value (MAT-0002) | EUR 72.0000000 |
| NODE-0008 Tier-3 input pool unit cost (MAT-0002) | EUR/unit 2.4000000 |
| NODE-0004 Tier-3 transformation output value (RCP-00001) | EUR 330.0000000 |
| NODE-0004 Tier-3 transformation output unit cost (RCP-00001) | EUR/unit 5.5000000 |
| NODE-0005 Tier-3 transformation output value (RCP-00002) | EUR 242.0000000 |
| NODE-0005 Tier-3 transformation output unit cost (RCP-00002) | EUR/unit 6.0500000 |
| NODE-0006 Tier-3 transformation output value (RCP-00003) | EUR 540.0000000 |
| NODE-0006 Tier-3 transformation output unit cost (RCP-00003) | EUR/unit 4.5000000 |
| NODE-0007 Tier-3 transformation output value (RCP-00004) | EUR 198.0000000 |
| NODE-0007 Tier-3 transformation output unit cost (RCP-00004) | EUR/unit 4.9500000 |
| NODE-0008 Tier-3 transformation output value (RCP-00005) | EUR 132.0000000 |
| NODE-0008 Tier-3 transformation output unit cost (RCP-00005) | EUR/unit 4.4000000 |
| LANE-00007 Tier-3-to-Tier-2 receipt value (NODE-0004->NODE-0009) | EUR 342.0000000 |
| LANE-00008 Tier-3-to-Tier-2 receipt value (NODE-0005->NODE-0010) | EUR 256.0000000 |
| LANE-00009 Tier-3-to-Tier-2 receipt value (NODE-0006->NODE-0009) | EUR 564.0000000 |
| LANE-00010 Tier-3-to-Tier-2 receipt value (NODE-0007->NODE-0010) | EUR 214.0000000 |
| LANE-00011 Tier-3-to-Tier-2 receipt value (NODE-0008->NODE-0010) | EUR 148.0000000 |
| NODE-0009 Tier-2 input pool quantity (MAT-0003) | units 60.0000000 |
| NODE-0009 Tier-2 input pool value (MAT-0003) | EUR 342.0000000 |
| NODE-0009 Tier-2 input pool unit cost (MAT-0003) | EUR/unit 5.7000000 |
| NODE-0009 Tier-2 input pool quantity (MAT-0004) | units 120.0000000 |
| NODE-0009 Tier-2 input pool value (MAT-0004) | EUR 564.0000000 |
| NODE-0009 Tier-2 input pool unit cost (MAT-0004) | EUR/unit 4.7000000 |
| NODE-0010 Tier-2 input pool quantity (MAT-0003) | units 40.0000000 |
| NODE-0010 Tier-2 input pool value (MAT-0003) | EUR 256.0000000 |
| NODE-0010 Tier-2 input pool unit cost (MAT-0003) | EUR/unit 6.4000000 |
| NODE-0010 Tier-2 input pool quantity (MAT-0004) | units 70.0000000 |
| NODE-0010 Tier-2 input pool value (MAT-0004) | EUR 362.0000000 |
| NODE-0010 Tier-2 input pool unit cost (MAT-0004) | EUR/unit 5.1714286 |
| NODE-0009 Tier-2 transformation output value (RCP-00006) | EUR 1122.0000000 |
| NODE-0009 Tier-2 transformation output unit cost (RCP-00006) | EUR/unit 18.7000000 |
| NODE-0010 Tier-2 transformation output value (RCP-00007) | EUR 731.5000000 |
| NODE-0010 Tier-2 transformation output unit cost (RCP-00007) | EUR/unit 20.9000000 |
| LANE-00012 Tier-2-to-plant receipt value (NODE-0009->NODE-0011) | EUR 658.5000000 |
| LANE-00013 Tier-2-to-plant receipt value (NODE-0009->NODE-0012) | EUR 491.5000000 |
| LANE-00014 Tier-2-to-plant receipt value (NODE-0010->NODE-0012) | EUR 335.5000000 |
| LANE-00015 Tier-2-to-plant receipt value (NODE-0010->NODE-0013) | EUR 442.0000000 |
| NODE-0011 plant pool quantity | units 45.0000000 |
| NODE-0011 plant pool value | EUR 904.5000000 |
| NODE-0011 plant pool unit cost | EUR/unit 20.1000000 |
| NODE-0012 plant pool quantity | units 40.0000000 |
| NODE-0012 plant pool value | EUR 827.0000000 |
| NODE-0012 plant pool unit cost | EUR/unit 20.6750000 |
| NODE-0013 plant pool quantity | units 20.0000000 |
| NODE-0013 plant pool value | EUR 442.0000000 |
| NODE-0013 plant pool unit cost | EUR/unit 22.1000000 |
| NODE-0011 served value at P04 | EUR 603.0000000 |
| NODE-0011 served value at P05 | EUR 201.0000000 |
| NODE-0011 total served value across all demand periods | EUR 804.0000000 |
| NODE-0012 served value at P04 | EUR 620.2500000 |
| NODE-0012 served value at P05 | EUR 206.7500000 |
| NODE-0012 total served value across all demand periods | EUR 827.0000000 |
| NODE-0013 served value at P04 | EUR 265.2000000 |
| NODE-0013 served value at P05 | EUR 176.8000000 |
| NODE-0013 total served value across all demand periods | EUR 442.0000000 |
| NODE-0007 terminal-period closing inventory value (MAT-0002) | EUR 33.8000000 |
| NODE-0010 terminal-period closing inventory value (MAT-0003) | EUR 32.0000000 |
| NODE-0011 terminal-period closing inventory value (MAT-0005) | EUR 100.5000000 |
| Ledger total for EXTERNAL_PURCHASE | EUR 920.0000000 |
| Ledger total for FREIGHT | EUR 62.0000000 |
| Ledger total for DUTY | EUR 6.0000000 |
| Ledger total for INSURANCE | EUR 3.0000000 |
| Ledger total for FIXED_ORDER | EUR 72.0000000 |
| Ledger total for FIXED_SHIPMENT | EUR 120.0000000 |
| Ledger total for CONVERSION | EUR 263.8000000 |
| Ledger total for SETUP | EUR 170.0000000 |
| Ledger total for OVERHEAD | EUR 18.0000000 |
| Ledger total for SURGE | EUR 0.0000000 |
| Ledger total for MARKUP | EUR 310.5000000 |
| Ledger total for HOLDING | EUR 0.0000000 |
| Ledger total for ACTIVATION | EUR 0.0000000 |
| Ledger total for SHORTAGE | EUR 0.0000000 |
| Total served value across all plants and demand periods | EUR 2073.0000000 |
| Total terminal-period closing inventory value across all nodes | EUR 166.3000000 |
| Total non-capitalised cost (HOLDING + ACTIVATION + SHORTAGE) | EUR 0.0000000 |
| Stage-2 value before non-capitalised cost | EUR 2239.3000000 |
| Value-conservation identity: total capitalised cost plus opening book value | EUR 2239.3000000 |

## 6. The reconciliation identities and tolerance convention

Every identity in §4 is checked with `tolerance = max(absolute, relative * max(|lhs|, |rhs|))`, using the absolute/relative pairs in the configuration's `tolerances` block (quantity 1e-5 / 1e-7, value 1e-3 / 1e-7, unit cost 1e-5 / 1e-7). The strongest single check is value conservation: total capitalised cost injected across the whole network plus opening book value must equal total served value plus total terminal closing value, exactly.

## 7. Nine ways this goes wrong

- **Omitted cost** — a capitalised addition (freight, duty, fixed order, fixed shipment) is dropped from a receipt. Caught by the receipt-value identity, and propagates into every downstream pool.
- **Double count** — a cost already capitalised upstream is capitalised again downstream. Caught by pool value conservation.
- **Wrong markup base** — a receipt-stage cost is wrongly marked markup-eligible, or a transformation cost wrongly excluded. Caught by the transformation-value identity.
- **Inconsistent outflow cost** — two outflows from the same pool in the same period are priced differently. Caught by the common-outflow-cost identity.
- **Value loss** — a closing value is understated with no matching outflow to explain the gap. Caught by pool value conservation.
- **Artificial dilution** — a pool's quantity is inflated without matching value, to depress its unit cost. Caught by the bilinear unit-cost identity together with quantity roll-forward.
- **Zero-pool error** — a pool with zero quantity is left with nonzero value. Caught by the zero-pool-value identity.
- **Infeasible flow** — an approval is suspended, breaking a required physical path. The engine raises an error rather than silently reporting a wrong number.
- **Deliberate shortage** — terminal demand exceeds the quantity available at a plant. Caught by the published plant-service control total because served quantity and value fall below BASE.

## 8. Validate the fixture inputs

Run `python -m tooling.validate_fixture --data-dir <fixture-input-directory>`. The directory must contain all 25 raw fixture CSVs. The command reconstructs the reference valuation and compares it with the published reconciliation artefacts. Claimed model-output validation is a separate control and is not implemented by this command.

## 9. What is deliberately not here

No main-case reference results, private bounds, objective ranges, generator seeds or solver settings appear anywhere in this document or in the fixture's student-visible files. Absence here is by design, not oversight.

## 10. Provenance

Generated from configuration version `0.3.3`. Do not edit directly.
