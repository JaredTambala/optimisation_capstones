# CAP-001 Network Structure Design Contract

## Document control

| Field | Value |
|---|---|
| Purpose | Define the structural dataset that WP4 must generate before commercial and planning facts are added |
| Status | Accepted on 18 August 2026; network-depth thresholds frozen |
| Date | 18 August 2026 |
| Governing sources | CAP-001 specification v0.3 §§6, 11.2, 12.1–12.2 and 13.1; decision configuration v0.3.0; CN-002 where fixture evidence is referenced |
| Scope | Organisations, nodes, plants, materials, recipes, recipe inputs and material-flow approvals |
| Explicit non-scope | Contracts, lanes, prices, capacities, inventory, demand, scenarios, optimisation results and application implementation |

## 1. Design outcome

WP4 must produce a deterministic multi-tier structure capable of sustaining a
meaningful supply-chain optimisation exercise. Success is not measured by row
count alone. The structure must contain credible alternatives, concentration,
shared dependency, material transformation and traceable terminal lineages.

WP4 proves structural possibility. WP5 must make the alternatives commercially
distinct, WP6 must make timing and disruption material, and WP7 must judge the
combined dataset. A structurally valid network can therefore pass WP4 and still
be rejected during whole-dataset calibration.

## 2. Fixed requirements

The following positions are already controlled and are not generator choices.

| Area | Fixed position |
|---|---|
| Topology | One directed acyclic Tier-N network instantiated as Tier 4 → Tier 3 → Tier 2 → Tier 1 → Asterion plants; declared edges may skip tiers but may not move upstream or within a tier |
| Tier meaning | Tier 1 is nearest Asterion; Tier 4 is the external boundary |
| Plants | Exactly Birmingham, Dortmund, Katowice and Zaragoza |
| Supplier nodes | Tier 1: 6–8; Tier 2: 8–10; Tier 3: 8–10; Tier 4: 10–12 |
| Organisations | 20–26, including selected multi-site, multi-tier and common-parent structures |
| Materials | 30–40 total; 6–8 demandable terminal materials |
| Recipes | 40–60 |
| Approvals | 120–180 material-flow approval records; only `APPROVED` records form usable structural paths |
| Pooling grain | Identical node, material and period only; one authoritative UOM per material |
| Boundary rule | Only Tier-4 boundary nodes may introduce externally priced material |
| Lineage | Every terminal material has a complete four-supplier-tier lineage and at least two broader sourcing combinations |
| Hidden dependency | The network includes discoverable common upstream, ownership and geographic dependency structures |
| Recipe policy | Alternatives are blendable unless their group is explicitly exclusive |
| Identifiers | Stable controlled IDs and fictional names; generation is deterministic from private namespaced seeds |

## 3. Structural conventions closed for implementation

These conventions remove ambiguity without changing the controlled contracts.

1. Tier-4 nodes are external boundary source sites and do not host
   transformations. Tier-1 through Tier-3 supplier nodes may host
   transformations. Plants do not host transformations in release 1.
2. Tier-1 suppliers produce the demandable `TERMINAL` materials shipped to
   plants. `PLANT_READY` remains a reserved material-stage value and is not
   instantiated unless a later controlled change introduces a distinct plant
   transformation step.
3. An approval carries a material unchanged between nodes. Material changes
   occur only through a recipe at a processing-capable supplier node.
4. Active approvals move strictly downstream according to
   `TIER_4 > TIER_3 > TIER_2 > TIER_1 > PLANT`. Tier skips are permitted only
   for explicitly recorded shorter alternatives.
5. Every active structural entity must participate in at least one complete or
   explicitly declared alternative terminal lineage. Extra disconnected or
   decorative entities are prohibited.
6. Structural alternatives are generated before commercial terms. WP4 must not
   assume that two structural paths will remain economically credible; WP5 is
   responsible for that calibration.
7. An approval is structurally usable only when `approval_status` is
   `APPROVED` and its validity range overlaps the release planning window.
   `CONDITIONAL` and `SUSPENDED` records may provide assessment context but do
   not count towards paths, participation or scorecard thresholds.

## 4. Graph definitions

The generator and validator use the following definitions consistently.

- **Node graph:** active physical nodes joined by active approved seller-to-
  buyer relationships, ignoring material labels.
- **State graph:** `(node_id, material_id)` vertices joined by transport edges
  for approvals and transformation edges for recipe input-to-output changes.
- **Complete lineage:** a state-graph derivation from at least one Tier-4
  external boundary source through Tier 3, Tier 2 and Tier 1 to a terminal
  material at an Asterion plant.
- **Broader sourcing combination:** a complete set of upstream choices capable
  of supplying every input of the selected recipes. Two combinations count as
  distinct only when they differ in a Tier-1 producing node and in at least one
  upstream operating supplier organisation.
- **Multi-sourced receiving pool:** one buyer-node/material pair with at least
  two active upstream seller nodes.
- **Hidden dependency motif:** apparently separate downstream choices that
  share an upstream node/material, operating supplier, parent group or region.
- **Participating entity:** an organisation, node, material, recipe or approval
  appearing in at least one terminal lineage witness retained by the profiler.

For multi-input recipes the validator need not enumerate every possible
combination. It may stop after retaining two valid witness combinations per
terminal material and the dependency witnesses required below.

## 5. Network-depth scorecard

The accepted structural candidate uses the following frozen acceptance
thresholds. They are deliberately structural; flow-weighted concentration and
economic dominance belong to WP5–WP7.

| Metric | Frozen acceptance threshold |
|---|---:|
| Weakly connected components in the active node graph | Exactly 1 |
| Active structural entities participating in a terminal lineage | 100% |
| Terminal materials with at least one full Tier-4-to-plant lineage | 100% |
| Broader sourcing combinations per terminal material | At least 2 |
| Tier-1 producer nodes per `HIGH` or `CRITICAL` terminal material | At least 2 |
| Plants structurally eligible to receive each terminal material | At least 2 |
| Terminal materials structurally eligible at each plant | At least 3 |
| Multi-sourced receiving pools | At least one at Tier 3, Tier 2, Tier 1 and plant level |
| Share of non-boundary receiving node/material pairs that are multi-sourced | At least 20% |
| Multi-input recipes | At least 20% of active recipes |
| Alternative recipe groups | At least 4 groups, including at least 2 blendable and 2 exclusive groups |
| Multi-site operating supplier organisations | At least 4 |
| Operating supplier organisations with nodes at more than one tier | At least 2 |
| Parent groups containing at least two operating suppliers | At least 2 |
| Common-upstream dependency motifs | At least 2 |
| Parent-group dependency motifs | At least 2 |
| Regional dependency motifs using distinct upstream sites | At least 2 |
| Terminal materials covered by hidden dependency motifs | At least 3 |
| Plants covered by hidden dependency motifs | At least 2 |
| Terminal materials with an organisation-diverse alternative | At least 2 |
| Terminal materials with two apparent downstream choices but one documented common upstream dependency | At least 2 |
| Terminal materials with a declared shorter alternative | No more than 25%; none may rely on it as their only lineage |
| Duplicate active seller/buyer/material approvals | 0 |
| Orphan nodes, materials, recipes or approvals | 0 |
| Node, material-state or recipe dependency cycles | 0 |

`Organisation-diverse alternative` means that two retained combinations do not
share an operating supplier or parent group at every upstream tier. This is a
structural resilience signal, not a claim that the alternatives have adequate
capacity or acceptable economics.

## 6. Minimal implementation shape

The code exists to generate and test the dataset, not to become a framework or
a reference application. Start with three plainly named files:

| File | Responsibility |
|---|---|
| `capstones/CAP-001/generator/generate_network.py` | Deterministically construct the seven tables and write an explicit target directory |
| `tooling/assess_network_structure.py` | Independently validate the tables and emit the scorecard, witnesses and concise report |
| `tests/test_network_generation.py` | Test reproducibility and the required positive and negative structural cases |

Split these files only if their responsibilities become genuinely difficult to
follow. Do not introduce model-building, solver or application code in WP4.
Namespaced sub-seeds can remain a small helper in `generate_network.py`: each is
derived from `(master_seed, namespace)` rather than consuming one shared random
stream. Adding a name in one phase must not silently reshuffle unrelated entity
families.

Generation proceeds constructively:

1. choose counts within the controlled ranges;
2. generate organisations, parent groups and sites;
3. generate terminal families and one full four-tier backbone for each;
4. overlay alternative paths and the required hidden-dependency motifs;
5. generate supporting materials and recipes, including multi-input and
   alternative groups;
6. materialise approvals and plant eligibility;
7. fill remaining scale only with entities attached to a retained lineage;
8. validate and profile; and
9. reject the candidate if any scorecard gate fails.

Draft generation writes to an explicit build directory and must never overwrite
`student_release/.../data/raw` directly. Promotion into the release tree is a
later controlled packaging action.

## 7. Validation layers

WP4 validation is intentionally independent of optimisation results.

1. **Contract checks:** headers, types, domains, keys and structural foreign
   keys for the seven WP4 files.
2. **Semantic checks:** tier/flag consistency, parent hierarchy, material-stage
   direction, recipe completeness, UOM consistency and effective ranges.
3. **Graph checks:** strict downstream approvals, topological order, reachability,
   full lineages, broader combinations, cycles and orphans.
4. **Depth checks:** every metric in §5 plus machine-readable witness paths for
   each required alternative and dependency motif.
5. **Reproducibility checks:** same seed/configuration produces byte-identical
   files and scorecard; a changed structural seed changes at least one intended
   structural artefact.

The scorecard must report numerator, denominator, threshold, pass/fail and the
IDs of witness or failing entities. A single aggregate “network complexity”
score is prohibited because it would hide weak dimensions.

## 8. Required WP4 evidence

- seven populated structural CSVs conforming to the controlled schemas;
- machine-readable `network_depth_scorecard.json`;
- concise `NETWORK_STRUCTURE_REPORT.md` explaining the graph and every
  intentional exception;
- network overview image or code-generated diagram suitable for author review;
- retained full-lineage, alternative-path and hidden-dependency witnesses;
- deterministic seed/configuration record and file checksums; and
- positive, cycle, orphan, shallow-lineage and superficial-multi-sourcing tests.

The visual is review evidence, not the acceptance mechanism. Machine checks and
witnesses remain authoritative.

## 9. WP4/WP5 boundary

WP4 approval means that a supply relationship is structurally possible. WP5
must add one valid commercial contract and at least one physical lane for every
active approval intended to carry flow. WP5 may reject and regenerate a WP4
candidate if commercialisation reveals universal dominance, implausible lane
requirements or alternatives that cannot be differentiated credibly.

Likewise, region and parent structures created here are scenario candidates;
WP6 decides which become controlled disruptions.

## 10. Completion gate

WP4 is complete when:

1. every fixed requirement and scorecard threshold above passes;
2. the generated structure is deterministic and contract-valid;
3. retained witnesses make every terminal lineage, alternative and hidden
   dependency reviewable;
4. no active structural entity is decorative;
5. the author review finds the network understandable enough to explain in an
   application while still requiring genuine Tier-N reasoning; and
6. the candidate is accepted as the structural input to WP5, with any
   provisional thresholds either frozen or explicitly amended.

All six conditions were met and owner acceptance was recorded on 18 August
2026. The thresholds in §5 are therefore frozen. Later changes require an
explicit controlled amendment and re-execution of the complete scorecard.

## 11. Governance finding

The authoritative v0.3 document still describes WP7/WP8 as producing full
reference models and results. The delivery plan and traceability matrix now
record the capstone owner's narrower authoring intent: private implementation
exists only to establish viability and calibrate the dataset. Before release,
that scope change should be captured in a normative change note or a reissued
specification. It does not block WP4 structural design or generation.
