# CAP-001 Network Structure Report

Assessment status: **PASS**

This report describes structural possibility only. Contracts, lanes, costs,
capacity, demand and scenarios are deliberately outside this assessment.

## Entity counts

| Entity | Count |
|---|---:|
| Supplier Organisations | 22 |
| Supplier Nodes | 34 |
| Plants | 4 |
| Materials | 36 |
| Terminal Materials | 8 |
| Recipes | 52 |
| Recipe Inputs | 67 |
| Approvals | 138 |
| Usable Approvals | 138 |

## Depth scorecard

| Metric | Result | Threshold | Status |
|---|---:|---:|:---:|
| Weakly connected components in the active node graph | 1 | exactly 1 | PASS |
| Active structural entities participating in a terminal lineage | 100.0% | 100% | PASS |
| Terminal materials with a full Tier-4-to-plant lineage | 100.0% | 100% | PASS |
| Minimum broader sourcing combinations per terminal material | 2 | at least 2 | PASS |
| Minimum Tier-1 producer nodes for HIGH or CRITICAL terminal materials | 2 | at least 2 | PASS |
| Minimum plants eligible to receive each terminal material | 3 | at least 2 | PASS |
| Minimum terminal materials eligible at each plant | 6 | at least 3 | PASS |
| Receiving levels with at least one multi-sourced pool | 4 | all 4 levels | PASS |
| Share of non-boundary receiving node/material pairs that are multi-sourced | 55.1% | at least 20% | PASS |
| Share of active recipes with multiple inputs | 28.8% | at least 20% | PASS |
| Alternative recipe groups | 4 | at least 4, including 2 blendable and 2 exclusive | PASS |
| Multi-site operating supplier organisations | 12 | at least 4 | PASS |
| Operating suppliers represented at more than one tier | 12 | at least 2 | PASS |
| Parent groups containing at least two operating suppliers | 2 | at least 2 | PASS |
| Common-upstream dependency motifs | 2 | at least 2 | PASS |
| Parent-group dependency motifs | 3 | at least 2 | PASS |
| Regional dependency motifs using distinct upstream sites | 2 | at least 2 | PASS |
| Terminal materials covered by hidden dependencies | 5 | at least 3 | PASS |
| Plants covered by hidden dependencies | 4 | at least 2 | PASS |
| Terminal materials with an organisation-diverse alternative | 8 | at least 2 | PASS |
| Terminal materials with downstream choice and a common upstream dependency | 2 | at least 2 | PASS |
| Share of terminal materials using a declared shorter alternative | 0.0% | no more than 25%; never the sole lineage | PASS |
| Duplicate usable seller/buyer/material approvals | 0 | 0 | PASS |
| Orphan active structural entities | 0 | 0 | PASS |
| Node, material-state or recipe dependency cycles | 0 | 0 | PASS |

## Terminal lineage summary

| Terminal material | Tier-1 combinations | Eligible plants |
|---|---:|---:|
| MAT-0029 — Compact Motor Controller | 2 | 3 |
| MAT-0030 — High-Capacity Drive Controller | 2 | 3 |
| MAT-0031 — Remote Monitoring Controller | 2 | 3 |
| MAT-0032 — Precision Motion Controller | 2 | 3 |
| MAT-0033 — Ruggedised Control Cabinet Module | 2 | 3 |
| MAT-0034 — Energy Recovery Controller | 2 | 3 |
| MAT-0035 — Process Sensor Controller | 2 | 3 |
| MAT-0036 — Safety Control Module | 2 | 3 |

## Deliberate dependency structure

- Common-upstream motifs: 2 terminal materials.
- Parent-group motifs: 3 terminal materials.
- Region-only motifs using distinct sites: 2 terminal materials.
- Machine-readable witnesses identify the affected choices, upstream nodes,
  parent groups and plants.

## Interpretation boundary

A passing result proves that the structural data has lineage, alternatives and
discoverable dependency. It does not prove that an alternative has adequate
capacity, attractive economics or useful scenario behaviour; those properties
must be established when the remaining dataset is generated and calibrated.
