# CAP-001 Network Structure Implementation Status

## Outcome

The first full-scale structural candidate has been generated and passes every
contract, semantic, graph and network-depth check. Technical implementation is
complete. The capstone owner accepted the report and candidate on 18 August
2026, freezing the scorecard thresholds in the design contract. This exact
structural candidate is now the controlled input to commercial and economic
generation.

This implementation proves structural dataset depth. It does not contain an
optimisation formulation, reference allocation, commercial calibration or
application code.

## Candidate profile

| Dimension | Result |
|---|---:|
| Supplier organisations | 22 |
| Supplier sites | 34 |
| Plants | 4 |
| Materials | 36 |
| Terminal materials | 8 |
| Transformation recipes | 52 |
| Recipe inputs | 67 |
| Material-flow approvals | 138 |
| Receiving pools that are multi-sourced | 55.1% |
| Recipes with multiple inputs | 28.8% |
| Alternative recipe groups | 4: two blendable and two exclusive |
| Common-upstream dependency motifs | 2 terminal materials |
| Parent-group dependency motifs | 3 terminal materials |
| Region-only dependency motifs using distinct sites | 2 terminal materials |

Every terminal material has:

- a complete Tier 4 → Tier 3 → Tier 2 → Tier 1 → plant derivation;
- at least two retained sourcing combinations that differ at Tier 1 and in at
  least one upstream operating supplier;
- two Tier-1 producer sites; and
- structural eligibility at three of the four plants.

Every plant is eligible for six terminal materials. All active organisations,
nodes, materials, recipes and usable approvals participate in at least one
terminal lineage, with an explicit terminal-coverage entry retained for every
entity. Single-source receiving pools have no restrictive share cap, and
multi-source share caps collectively cover the full pool. The active node graph
is weakly connected and the node, material-state and recipe graphs are acyclic.

## Implementation and evidence

| Purpose | Evidence |
|---|---|
| Deterministic construction | `capstones/CAP-001/generator/generate_network.py` |
| Independent validation and profiling | `tooling/assess_network_structure.py` |
| Positive and adversarial tests | `tests/test_network_generation.py` |
| Seven generated structural tables | `capstones/CAP-001/generated/network/data/` |
| Seed, row-count and checksum record | `capstones/CAP-001/generated/network/generation_manifest.json` |
| Machine-readable depth gates | `capstones/CAP-001/generated/network/evidence/network_depth_scorecard.json` |
| Complete derivation witnesses | `capstones/CAP-001/generated/network/evidence/lineage_witnesses.json` |
| Hidden-dependency witnesses | `capstones/CAP-001/generated/network/evidence/dependency_witnesses.json` |
| Human-readable review | `capstones/CAP-001/generated/network/evidence/NETWORK_STRUCTURE_REPORT.md` |
| Code-generated network diagram | `capstones/CAP-001/generated/network/evidence/network_overview.mmd` |

The tests cover successful generation, all seven CSV contracts,
byte-identical regeneration, seed sensitivity, graph cycles, orphan entities,
missing terminal lineages and duplicate approvals presented as superficial
multi-sourcing. They also reject approval-share caps that make a structurally
necessary receiving pool impossible to cover.

## Reproduction

```bash
python capstones/CAP-001/generator/generate_network.py --check
python -m tooling.assess_network_structure --check
pytest -q tests/test_network_generation.py
```

## Acceptance decision

The candidate deliberately contains both diversified and exposed structures:
not every pool is multi-sourced, apparently distinct terminal choices can
share upstream nodes or parent ownership, and no shorter tier-skipping path is
included merely to inflate complexity. The evidence exposes these properties
rather than compressing them into one opaque score.

The capstone owner confirmed that the report was acceptable on 18 August 2026.
The candidate and thresholds are frozen. Any later structural change must be
controlled, regenerate the evidence and pass the complete assessment again.

The next stage must still establish whether its structural alternatives have
credible contracts, lanes and different economic behaviour. It must also close
the Incoterm accounting rule so seller-borne freight, insurance and duty remain
represented exactly once rather than disappearing from recursive cost.
