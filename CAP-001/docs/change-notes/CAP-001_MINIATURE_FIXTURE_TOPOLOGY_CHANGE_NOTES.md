# CAP-001 Miniature Fixture Topology Change Notes

## Document control

| Field | Value |
|---|---|
| Change note | CN-002 — Four-layer, multi-sourced miniature fixture |
| Status | Approved by capstone owner; implementation authorised |
| Date | 6 August 2026 |
| Current specification | *CAP-001 Tier-N End-to-End Cost Model, Modelling Decisions and Dataset Generation Specification* v0.3, §12.8 and Appendix E |
| Current specification SHA-256 | `a47823ff636aa5f07242fa1980f123073fc731775cdf17d517f4cefb1d64bf89` (unchanged — this note amends the fixture section by reference; the frozen DOCX is not reissued) |
| Proposed target | v0.3 as amended by CN-002 (normative amendment via this note, exactly as CN-001 amended v0.2 before v0.3 existed) |
| Change class | Material change to the WP2 miniature fixture's topology and published control totals, plus one already-accepted WP1 schema constant (`supplier_tier_count`) |
| Explicitly unchanged | `network.release_instance_supplier_tiers = 4`; `network.plant_count = 4`; `network.target_scale`; all 26 raw-data contracts and their fields; `configuration_version` (stays `0.3.0`); every recursive-cost accounting equation in CN-001 §6–§8 |
| Approval required from | Capstone owner (given), data lead, optimisation lead, evaluation lead |

## 1. Executive change summary

The frozen v0.3 specification's own worked example (§12.8, restated as control totals in Appendix E) describes the miniature fixture as a single chain: one plant, two Tier-4 sources, and exactly one node at each of Tier 3, Tier 2 and Tier 1. This is sufficient to prove the recursive-cost *arithmetic* (pooling, markup, freight capitalisation), but it cannot demonstrate the fixture's most important accounting property — that a pool commingling several differently-costed inbound streams collapses to a single outflow cost, with no way to selectively attribute cheap or expensive material to a chosen outflow. A one-node-per-tier chain has no commingling anywhere except at a single, isolated fan-in.

The capstone owner reviewed the single-chain design and rejected it as pedagogically thin, and directed that the fixture be expanded to a richer topology with genuine multi-sourcing at more than one point in the network. Investigation confirmed the frozen spec offers no larger sanctioned alternative for the *fixture* specifically — all multi-sourcing and network-richness requirements in the spec (§11.2, §12.2, §12.3, §12.5) are explicitly scoped to the full release-1 generated instance (WP4+), not to the hand-worked fixture. Expanding the fixture is therefore a genuine amendment to §12.8/Appendix E, not an application of existing spec language.

The replacement topology is a **4-layer network**: Tier 4 (3 external boundary nodes) → Tier 3 (5 nodes) → Tier 2 (2 nodes) → Plants (3 nodes), with **Tier 1 removed** as a distinct layer (Tier 2's transformation output is shipped directly to plants). It introduces genuine fan-in/fan-out at three separate hops instead of one, and is fully hand-derived and independently verified, including a value-conservation identity (total capitalised cost injected plus opening book value equals total served value plus total closing inventory value, exactly) that did not exist as an explicit control in the single-chain design.

This is not a change to the assessed problem, the cost-accounting equations, or the full-release network. It changes only: the fixture's own topology, its published control totals, and the fixture-scoped `supplier_tier_count` constant that recorded the old topology's tier count.

## 2. Required change-control actions

1. Adopt this note (CN-002) as the normative amendment to v0.3 §12.8 and Appendix E. The frozen DOCX is not reissued; this note governs the fixture's topology and control totals going forward, exactly as CN-001 governed the v0.2→v0.3 transition before v0.3 existed as a document.
2. Amend `config/cap001_decision_config.json`: `miniature_fixture_contracts.fixture_manifest.json.fields[supplier_tier_count].const` changes from `4` to `3`. `period_count` (`const: 5`) is **not** touched.
3. Amend the second, independently hard-coded `"supplier_tier_count": 4` inside `tooling/build_contract_artifacts.py`'s `planned_artifacts` fixture-manifest generation to `3`.
4. Regenerate all derived contract artefacts via `python -m tooling.build_contract_artifacts` (cascades into `config/cap001_decision_config.sha256`, `generated/contracts/WP1_ARTIFACT_MANIFEST.json`, `schemas/miniature_fixture/fixture_manifest.schema.json`, and both student-release copies of the manifest and schema).
5. Re-run `python -m tooling.validate_wp1`, `python -m tooling.audit_source_documents`, and `pytest` — all must pass unchanged. No test in the existing suite asserts `supplier_tier_count`; only `network.release_instance_supplier_tiers == 4` is asserted (`tests/test_frozen_policies.py`), and that constant is untouched.
6. Amend `CAP-001_DELIVERY_AND_ASSESSMENT_PLAN.md` §WP2: replace the "five-period/four-tier" network description and the 14-row control-totals table with the new topology description and the 15-row headline control-totals table (§5 below).
7. Amend `CAP-001_REQUIREMENTS_TRACEABILITY_MATRIX.md`: FIX-001 and FIX-002 rows updated to describe the four-layer, three-supplier-tier, multi-sourced-at-three-hops fixture and its value-conservation identity.
8. Append a dated amendment note to `docs/WP1_ACCEPTANCE_REPORT.md` recording that `supplier_tier_count` was reopened, why, and that all validators/tests re-passed after the change (combined with the separate, unrelated fixture-path ownership handoff to `tooling/build_contract_artifacts.py` that fixture implementation also requires).
9. Do not begin authoring the fixture's raw-data CSVs until steps 2–5 are complete and green.

## 3. What is explicitly NOT changing

- `network.release_instance_supplier_tiers = 4` — the full release-1 generated instance still has four supplier tiers (Tier 1–Tier 4) plus plants. This constant lives in a different part of the configuration (`network`, not `miniature_fixture_contracts`) and is validated independently in `tooling/contract_runtime.py`.
- `network.plant_count = 4` and `network.target_scale` — the full release still targets four Asterion plants (Birmingham, Dortmund, Katowice, Zaragoza) and 6–12 nodes per tier.
- `configuration_version` — stays `0.3.0`. A version bump is unnecessary and would needlessly reopen the pinned assertions in `tooling/contract_runtime.py`'s `validate_config` and `tests/test_frozen_policies.py`.
- All 26 raw-data contracts and every field within them — the fixture uses the same schemas as the full release; only which rows populate them changes.
- Every recursive-cost accounting equation in CN-001 §6–§8 (pooling, weighted-average unit cost, transformation value, receipt value, Stage-2 objective) — unchanged. The reconciliation engine built for the fixture is topology-agnostic by design and required no equation changes to accommodate the richer network.

This is the same category of fixture-scoped deviation from full-release scale that already existed before this change (5 periods vs. 12 in the full release; 1 plant vs. 4 in the original single-chain design) — not a new category of exception.

## 4. Before / after comparison

| Dimension | Before (rejected single-chain design) | After (this note) |
|---|---|---|
| Supply-chain layers | 4 (Tier 4/3/2/1) + Plant | 3 (Tier 4/3/2) + Plant |
| Supply nodes | 6 (2 Tier-4, 1 each Tier-3/2/1) | 13 (3 Tier-4, 5 Tier-3, 2 Tier-2) |
| Plants | 1 (Dortmund) | 3 (Dortmund, Katowice, Zaragoza) |
| Materials | 4 | 5 |
| Recipes | 3 | 7 |
| Arcs | 5 | 15 |
| Genuine multi-sourcing fan-in points | 1 (Tier 3 only) | 3 (Tier 3, Tier 2, one plant) |
| Raw-data row count (26 files) | ~150 | 346 |
| Published control totals | 14 | 15 headline (105 total, including the full derivation) |
| Explicit value-conservation identity | Not published as a distinct control | Published as `CT-105`, checked first |
| `supplier_tier_count` | 4 (matches the old topology) | 3 (matches the new topology) |
| `period_count` | 5 | 5 (unchanged) |

## 5. Amendment to v0.3 §12.8 (fixture description)

Replace the current §12.8 opening statement —

> "Before the full dataset is generated, the implementation must reproduce a small five-period, four-tier fixture by hand and through the approved model adapter. The fixture contains one plant, one terminal material, two Tier 4 sources, one weighted-average pool at Tier 3 and one transformation at each downstream supplier tier."

— with:

> Before the full dataset is generated, the implementation must reproduce a small five-period, four-layer fixture by hand and through the approved model adapter. The fixture contains three Tier-4 external boundary sources, five Tier-3 nodes, two Tier-2 nodes and three Asterion plants, connected by fifteen approved arcs with genuine multi-sourcing at three separate points in the network (a three-way pool at Tier 3, a two-way pool at Tier 2, and a two-way pool at one plant). Tier 1 is not instantiated as a distinct layer in the fixture; Tier-2 transformation output ships directly to plants. Every arc's dispatch quantity is pinned by matched minimum-order-quantity, order-multiple and lane-capacity fields, and every fan-out origin pool has zero permitted storage, so the fixture resolves to exactly one feasible physical plan — it is an accounting oracle, not an optimisation exercise, though it is rich enough that a solver could also reproduce it.

Add a new closing sentence recording the consequential effect of removing Tier 1: the `PLANT_READY` material stage, previously reserved for Tier-1 output, is unused in the fixture.

## 6. Amendment to v0.3 Appendix E (control totals)

Withdraw the existing 14-row control-totals table. Replace with the 15-row headline table below (the full 105-row derivation lives in `miniature_fixture/control_total_definitions.json` and `.../fixture_control_totals.csv`, both private, and the student-visible subset in the release copy):

| Control total | Expected |
|---|---:|
| Tier-3 pool quantity (3-way fan-in) | 150.0000000 units |
| Tier-3 pool value | EUR 402.0000000 |
| Tier-3 weighted-average unit cost | EUR 2.6800000/unit |
| Tier-3 transformation output value (yield 0.80) | EUR 540.0000000 |
| Tier-3 closing inventory value (capacity-stranded) | EUR 33.8000000 |
| Tier-2 pool unit cost (2-way fan-in) | EUR 5.1714286/unit |
| Tier-2 transformation output value (node A) | EUR 1122.0000000 |
| Tier-2 transformation output value (node B) | EUR 731.5000000 |
| Tier-2 closing inventory value (BOM-stranded) | EUR 32.0000000 |
| Plant pool unit cost — opening stock + single receipt | EUR 20.1000000/unit |
| Plant pool unit cost — dual-sourced fan-in | EUR 20.6750000/unit |
| Plant pool unit cost — single-sourced | EUR 22.1000000/unit |
| Total served value, three plants, two demand periods | EUR 2073.0000000 |
| Total terminal-period closing inventory value | EUR 166.3000000 |
| **Stage-2 value before non-capitalised cost** | **EUR 2239.3000000** |

Add a new Appendix E note recording the value-conservation identity: total capitalised cost injected (EUR 1945.30) plus opening book value (EUR 294.00) equals total served value (EUR 2073.00) plus total terminal closing value (EUR 166.30) — both sides EUR 2239.30 exactly, with HOLDING, ACTIVATION and SHORTAGE all zero. This identity must be checked first, before any finer-grained total, by the fixture validator.

## 7. Amendment to the WP1 schema constant

`schemas/miniature_fixture/fixture_manifest.schema.json`'s `supplier_tier_count` changes from `const: 4` to `const: 3`, reflecting that the fixture now instantiates three supplier tiers (Tier 4, Tier 3, Tier 2) plus a separate plant layer — plants have never been counted as a "tier" anywhere in the governing specification (*"four supplier tiers plus Asterion plants"* appears throughout v0.3; §6.2's tier table lists "Plant" as a row separate from the four numbered tiers). `period_count` (`const: 5`) is unaffected and stays at 5: with three arc-hops instead of four, the fifth period changes role from "final arrival and service" to "serve a second demand tranche from carried closing stock," but every period continues to do load-bearing work.

This is a fixture-scoped constant, distinct from `network.release_instance_supplier_tiers` (the full-release tier count, unaffected). No test in the existing suite asserts `supplier_tier_count`, so this change carries no test-breakage risk beyond the regeneration chain in §2.

## 8. Consequential documentation amendments

1. `planning_calendar`'s cross-field rule "only P12 has `is_terminal_period=true`" describes the 12-period full-release calendar. The fixture's own 5-period calendar has no P12; its rule must be re-scoped, in the generated data dictionary and this note, to "only the last period of the instance calendar." This is a prose/dictionary amendment, not a schema-enforced constraint (`is_terminal_period` is typed as a plain boolean with no `const` tied to a specific `period_id`), so it carries no validator risk.
2. `disruption_scenarios.csv` SCN-03's frozen description ("Tier 1 node disruption") names a layer that no longer exists in the fixture. SCN-03 remains present in the fixture's `disruption_scenarios.csv` (all six enum values must exist) but stays `active_flag=false` regardless (only BASE is active in the fixture); its fixture-local description is retargeted to a Tier-2 node disruption so the row remains internally coherent even though inactive.

## 9. Impact on downstream work packages

- **WP3 (solver proof of concept)**: the richer fixture is large enough that a solver-based reproduction is a meaningfully harder (and more informative) proof than the single-chain design would have been, but the fixture remains solvable by hand first — WP3 is not blocked or expanded in scope by this change.
- **WP7 (full reference models)**: no equation changes; the reconciliation engine built for the fixture is topology-agnostic and directly reusable at full release scale.
- **WP8 (calibration and adversarial validation)**: the fixture's 9 negative variants (one more than the originally planned 8, adding a deliberate-shortage case since BASE is now designed for zero shortage with an explicit surplus) give WP8 a richer set of proven detection mechanisms to draw on when designing full-scale adversarial tests.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Reopening already-accepted WP1 evidence | Full regeneration and re-test sequence in §2, steps 4–5; dated amendment note in `docs/WP1_ACCEPTANCE_REPORT.md` |
| Larger hand-check surface (105 totals vs. 14) invites arithmetic error | The value-conservation identity (§6) is checked first and is strictly more informative than any single total — if it holds, the network cannot be leaking or double-counting value anywhere, which bounds the risk from any individual total being mistyped |
| A richer fixture could be mistaken for an optimisation exercise, with students questioning why a "solve" always produces the same answer | The fixture's determinism (every arc pinned by matched MOQ/multiple/capacity, every fan-out origin storage-capped at zero) is stated explicitly in the amended §12.8 text: "it is an accounting oracle, not an optimisation exercise" |

## 11. Decisions closed by this note

The design report's open decisions (documented in the WP2 implementation plan) are resolved as follows, consistent with the topology fixed above: third plant identity is Dortmund/Katowice/Zaragoza; the fixture retains exactly one dutiable lane (GB→NL, 2%) as an isolated negative-control case; period-keyed reference files (`source_capacity`, `transformation_capacity`, `conversion_costs`, `external_source_prices`, `terminal_demand`, `fx_rates`) are populated densely (one row per period) rather than sparsely, to remove missing-row ambiguity; `disruption_scenarios.csv` carries all six enum rows with only BASE active; `configuration_version` stays `0.3.0`.
