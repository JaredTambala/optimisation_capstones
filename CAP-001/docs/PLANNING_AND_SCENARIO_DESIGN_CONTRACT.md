# CAP-001 Planning and Scenario Dataset Design Contract

## Document control

| Field | Value |
|---|---|
| Purpose | Define the planning facts and six complete, interchangeable dataset packages needed to complete CAP-001 |
| Status | Completed and accepted after controlled recalibration; 24 technical gates pass; packages frozen |
| Date | 25 August 2026 |
| Governing sources | CAP-001 specification v0.3 §§7, 10, 11.18–11.27, 12.5–12.7 and 13; decision configuration v0.3.1; accepted network and commercial candidates |
| Inputs | Frozen network data in `generated/network/data/` and frozen commercial data in `generated/commercial/data/` |
| Scope | BASE planning facts; five scenario datasets; dataset manifests; package validation; author-side scenario generation; candidate configuration and explanation hand-off |
| Explicit non-scope | A preferred allocation, a published feasibility witness, a reference application, student resilience-policy design and a full recursive optimisation result |

## 1. Design outcome

The planning layer must turn the accepted structural and commercial choices
into a multi-period decision. Lead time, advance commitment, storage, opening
stock, regular and surge capacity, setup, shared resources and service priority
must affect what a reasonable plan can do. Adding twelve copies of otherwise
static facts would not meet this objective.

Every supplied scenario is a complete dataset, not a delta that a student
combines with a separately loaded BASE directory. The release unit is six
self-contained packages: BASE and SCN-01 through SCN-05. Each contains the
complete 25-file raw-data contract and its own manifest and checksums. A student
explores another business reality by replacing the dataset root and rebuilding
the same generic formulation.

Each package is a deterministic 12-week planning case. At P01 the candidate's
system is assumed to know the complete P01–P12 dataset, including all dated
disruption and recovery assumptions. It therefore produces one horizon-wide
plan and may make advance commitments or position inventory for a later impact.
P01 is the first decision period, not the date on which only P01 facts are
revealed. Unexpected mid-horizon revelation, frozen prior decisions and
stochastic non-anticipativity are outside this dataset contract.

The resulting system boundary is:

```text
one complete dataset package
        -> schema and business validation
        -> effective facts from that package alone
        -> declared policy and authorised override configuration
        -> one generic MILP or MINLP formulation
        -> versioned decision, comparison and explanation
```

Scenario impacts remain data inside the selected package. This is necessary
because some authoritative facts are not period-grained and because one common
impact contract keeps treatment consistent across capacity, logistics, cost and
demand changes. The student's preparation layer resolves only that package's
own `disruption_impacts.csv`; it must never reach into another package, fetch
BASE rows or choose a different scenario from a central overlay.

WP6 proves that the six datasets are complete, coherent, constructively
feasible where intended, interchangeable through one loader and capable of
creating temporal and scenario pressure. WP7 has accepted their combined
decision depth. Neither work package is an author model-solution exercise.

## 2. Dataset-package contract

The private candidate layout is:

```text
generated/datasets/
  BASE/
    dataset_manifest.json
    data/                       # all 25 CSVs
  SCN-01/
    dataset_manifest.json
    data/                       # all 25 CSVs
  SCN-02/
    dataset_manifest.json
    data/                       # all 25 CSVs
  SCN-03/
    dataset_manifest.json
    data/                       # all 25 CSVs
  SCN-04/
    dataset_manifest.json
    data/                       # all 25 CSVs
  SCN-05/
    dataset_manifest.json
    data/                       # all 25 CSVs
```

The student release mirrors these six roots under `data/datasets/`. The current
single `data/raw/` scaffold is transitional and must not remain the authoritative
main-case input location once the packages are promoted.

Each manifest records at least the capstone and data versions, dataset ID,
scenario ID, compatibility group, required file count, every file checksum and
one aggregate dataset hash. A package is invalid if any of the 25 files is
missing, even where the omitted file would be identical to BASE or contain only
a header. Symlinks, parent-directory fallbacks and implicit shared files are
prohibited in the release.

The controlled packages use stable entity identifiers so results can be
compared directly. Candidate code must nevertheless derive all sets and
relationships from the selected package rather than relying on frozen counts or
names. A future valid replacement package may change any input file, not only
the rows described by the five supplied scenario narratives.

Within each package, `disruption_scenarios.csv` contains the one scenario record
that identifies that package. `disruption_impacts.csv` contains only the
applicable period-specific impact and recovery rows; it is header-only for
BASE. The public `SCENARIO_CATALOGUE.md` lists all six supplied packages.

## 3. BASE planning facts and expected shape

The accepted candidates contain 22 boundary source/material states, 52 active
recipes, 159 usable node/material pool states, 24 approved plant/terminal
material pairs and 70 distinct seller/material states. Those relationships
determine the BASE planning facts below. Each scenario package contains the
complete facts needed to interpret its own package-local impact rows. The first
controlled set does not pre-apply an impact to another fact table and then ask
the candidate to apply it again.

| Dataset | BASE expectation | Basis |
|---|---:|---|
| `planning_calendar.csv` | 12 rows | P01–P12, 4 January–28 March 2027 |
| `source_capacity.csv` | 264 rows | 22 boundary source/material states × 12 periods |
| `transformation_capacity.csv` | 624 rows | 52 recipes × 12 periods |
| `inventory_policies.csv` | 159 rows | One explicit policy for every usable pool state |
| `opening_inventory.csv` | 32–56 rows | Positive opening stock only; absence explicitly means zero |
| `terminal_demand.csv` | 288 rows | 24 plant/terminal-material pairs × 12 periods |
| `supplier_performance_history.csv` | 2,100 rows | 70 seller/material states × 30 historical months |
| `incident_history.csv` | 24–40 rows | Sparse historical events supporting the supplied exposure families |
| `disruption_scenarios.csv` | 1 row | The package's scenario identity and recommended view |
| `disruption_impacts.csv` | 0 for BASE; scenario-specific thereafter | Only the selected package's period impacts and explicit recovery |

The ranges are proposed design controls, not reasons to pad the data. A later
controlled change to the frozen network must recompute all relationship-derived
expectations.

## 4. Authoritative inputs and candidate configuration

### 4.1 Business facts

Every CSV under the selected `data/` root is authoritative for that run. A
candidate solution loads it read-only, validates the whole package and creates
a fresh model instance. It must not retain dimensions, parameters or caches
from the previously selected dataset unless they are keyed by the complete
dataset hash and proven compatible.

Historical performance and incidents are exploratory evidence. They may inform
a candidate's resilience measure, parameter choice or recommendation, but they
do not silently alter capacity, lead time, eligibility, objective coefficients
or scenario magnitude. A candidate that derives a model parameter from history
records that transformation in its configuration and explanation.

### 4.2 Package-local effective facts

The first controlled stress set expresses its forward changes through the
selected package's `disruption_impacts.csv`. This avoids double application and
uses one rule for weekly capacity, logistics, cost and demand changes, including
effects on non-periodic tables such as `shipping_lanes.csv`.

This does not make a scenario a partial dataset. Each package contains the
normal facts to which its own impacts apply, the applicable impact and recovery
rows, and every other required file. No external BASE data is needed.
Author-side validation independently resolves the effective view and proves
that the package is internally complete. A future replacement dataset may
change any fact directly, but the loader must never assume that a scenario ID
alone implies a change.

### 4.3 Candidate policy configuration

A candidate solution owns a separate, machine-readable run-policy
configuration. The assessment default remains pinned, but a high-quality
application should be able to declare and compare at least:

- the selected dataset root and run mode;
- approval and eligibility enforcement, including any explicitly authorised
  exception rather than silent use of an unapproved flow;
- quantitative resilience rules such as source, parent-group or regional
  concentration, minimum diversity or protected inventory;
- intervention choices such as expedited-lane use or a declared fixed
  inventory buffer;
- service priorities and parameters within the controlled objective hierarchy;
- soft-constraint penalties or within-stage objective weights where used; and
- field-level overrides with target, original value, effective value, reason
  and authority.

The default lexicographic service/economic/tie-break hierarchy and recursive
accounting policy remain assessment controls. Sensitivity runs may modify
declared parameters but may not be presented as the pinned default result.
Every run records both the dataset hash and effective configuration hash in
`run_metadata.json`.

## 5. BASE planning construction

### 5.1 Calendar and timing

The calendar contains twelve contiguous Monday-to-Sunday weeks. Transit is
calculated from the selected package as:

```text
lead_time_weeks = ceil((contract_handling_days + adjusted_transit_days) / 7)
```

A P*t* dispatch arrives in P*t + lead_time_weeks*. Post-P12 arrivals are
prohibited. Receipts and completed same-period transformation are usable in the
same weekly bucket following the acyclic material order. There is no opening
in-transit stock or WIP.

### 5.2 Demand

Demand is dense for all 24 approved plant/terminal-material streams. A private
finished-product mix creates plant-specific proportions, mild week-to-week
variation and selected planned peaks; only component demand is released.
Demand is fixed input, not a forecasting exercise.

The profile should create several genuine volume and timing decisions without
making every week exceptional. Planned peaks should activate some combination
of advance production, inventory drawdown, surge, alternative sourcing or
expedited transport. Priority class and service weight govern Stage 1;
`shortage_penalty_eur_per_unit` is reporting and sensitivity data only.

### 5.3 Capacity

Source capacity covers only the 22 externally priced boundary source/material
states. Transformation capacity covers every active recipe. Regular, surge and
planned-downtime fields are generated as coherent profiles, not independent
random values. Surge premiums must agree with the corresponding frozen WP5
commercial records.

Shared resource groups link multiple recipes at the same processing site where
there is a credible competition for equipment or labour. Capacity is calibrated
around a private constructive flow witness so that BASE has recourse and zero
shortage, while selected regular, shared-resource, lane or setup limits remain
decision-relevant. The witness is a feasibility certificate, not an optimum or
a released allocation.

For a non-null `shared_capacity_group_id`, every recipe row in the same
group/period repeats the same regular capacity, surge capacity and downtime.
Those repeated values are the group budgets, not separate budgets that may be
summed. `shared_capacity_coefficient` converts one output unit to group-capacity
units. A formulation therefore limits the coefficient-weighted sum of regular
output to the repeated regular budget and applies the equivalent constraint to
surge output. For a null group, the capacity values are recipe-specific. The
package assessor rejects incomplete group/coefficient pairs, one-recipe groups
and inconsistent repeated limits.

### 5.4 Inventory and opening value

Every usable pool state has one inventory-policy row, including explicit
`allow_inventory_flag=false` rows. Storage is allowed selectively across all
supplier tiers and plants; some no-storage states are retained so the network
cannot be reduced to independent weekly choices.

Positive opening-inventory rows are generated only where stock is physically
permitted. Missing rows mean zero opening stock. Usable quantity equals on-hand
less reserved, and opening total value equals usable quantity times opening unit
cost. Unit cost is calibrated within the accepted WP5 conditional envelope for
that state but is identified as synthetic book value.

Opening stock must cover otherwise unavoidable early lead-time gaps. It must
not be so generous that the first half of the horizon can ignore sourcing and
transformation. Safety-stock treatment is mixed deliberately: report-only
targets support analysis, selected soft targets create a policy trade-off and a
small number of hard targets represent fixed business rules. Terminal targets
are used sparingly.

### 5.5 Historical evidence

Thirty monthly observations per seller/material state provide enough history
for exploratory reliability, quality, completeness and lead-time analysis.
Profiles contain persistent cross-supplier differences, bounded noise,
occasional incidents and controlled `PARTIAL` flags. Quantity identities must
hold: accepted ≤ received ≤ ordered and on-time ≤ received.

Historical incidents are sparse and customer-readable. They support, but do
not mechanically generate, the forward scenario hypotheses. At least one
relevant historical pattern exists for each source, logistics, node and regional
exposure family. The histories remain useful only because the engagement asks
the candidate to justify resilience configuration and recommendations from the
data; they must not become decorative objective inputs.

## 6. Supplied dataset catalogue

The frozen package set uses the following concrete changes. Each row describes
a complete package, not instructions for finding data in BASE. WP7 tests their
combined decision materiality without changing these facts unless it identifies
a demonstrable dataset defect that passes controlled regeneration and renewed
acceptance.

| Dataset | Authoritative package reality | Distinct business question | System capability exercised | Recommended view |
|---|---|---|---|---|
| BASE | Normal planning and commercial facts; no impact rows | What is the common planning and economic reference? | Package validation, pinned defaults, approvals and reproducibility | `REOPTIMISE` |
| SCN-01 | `NODE-0005` polymer-resin boundary capacity is 7% in P01–P03, 50% in P04–P05 and normal from P06 | How dependent are terminal lineages on one upstream source? | Dataset replacement, surge sourcing, advance inventory and recursive propagation | `REOPTIMISE` |
| SCN-02 | Selected Asia–Europe standard lanes have transit ×1.75, freight ×1.40 and capacity ×0.75 in P02–P07; paired air lanes remain available | Is expedited transport worth its cost and capacity limitation? | Package-local time effects, arrival re-indexing, mode choice and cost/service sensitivity | `REOPTIMISE` |
| SCN-03 | `NODE-0030` is unavailable in P04, at 50% in P05 and normal from P06 | Can downstream production and service recover through approved alternate Tier-1 sites? | Model reconstruction, node availability, recipe/site eligibility and approval gates | `REOPTIMISE` |
| SCN-04 | Four `EUROPE_CENTRAL` Tier-2–Tier-4 nodes operate at 35–50% in P03–P06, while anchor `NODE-0027` operates at 10% through P10 before explicit recovery | Does nominal supplier diversity survive correlated regional exposure? | Region/parent concentration rules and resilience interventions | `BOTH` |
| SCN-05 | SCN-01 and SCN-02 conditions overlap with a 10–15% uplift in selected critical terminal demand | Where does a tightly coupled plan cease to provide adequate recourse? | Package validation, effect composition, service priority and explainable shortage | `REOPTIMISE` |

All five stress datasets remain because they test different generic system
behaviours as well as different business exposures. Only SCN-04 requires both
stress of the stored BASE plan and reoptimisation in the standard evidence set.
The application may support both modes for every package, but the assessment
does not require repetitive duplicate narratives.

## 7. Package-local impact semantics

The preparation layer uses only impact rows contained in the selected package:

1. Load and validate all 25 files from one dataset root.
2. Confirm that the manifest scenario and the package's one scenario row agree.
3. Resolve applicable node, organisation, parent-group, region, lane, recipe,
   material, price, conversion-cost and terminal-demand selectors from that
   package's relationships.
4. Apply `availability_flag=false` before capacity or lane multipliers.
5. Compose applicable multipliers multiplicatively within the affected field.
6. Permit replacement only for a declared field. Highest priority wins and a
   tie at the winning priority is invalid.
7. Apply transit multipliers before weekly ceiling and arrival indexing.
8. Represent recovery with explicit later-period rows rather than inference
   from a scenario name, a missing row or another dataset.
9. Reject negative, non-finite, structurally invalid or commercially
   implausible effective values.
10. Revalidate approvals, capacity coverage, period boundaries and post-horizon
    arrivals before constructing the model.

No code path may open `../BASE`, combine two dataset roots or substitute a
cached BASE table. Scenario identifiers select packages for the user; they do
not select bespoke equations.

An upstream cost change enters at the targeted boundary or conversion stage and
propagates through the recursive calculation. It does not create an exogenous
intermediate price.

`STRESS_ONLY` evaluates a stored plan produced from another complete package,
normally BASE, against the selected replacement dataset. Compatibility is
checked by identifiers before the plan is evaluated. `REOPTIMISE` creates a
fresh model from the selected package and finds recourse under the declared
configuration.

## 8. Two-level explanation contract

For every supplied dataset, the application must make two kinds of explanation
possible.

**Business/data explanation** identifies the material differences between the
selected package and BASE, affected periods, lineages and dependencies; compares
cost, service, inventory and concentration; and states the operational
implication.

**System explanation** identifies the dataset and configuration hashes,
validation outcome, approvals and resilience rules; records overrides; names
the constraints or gates that became active; explains objective-stage or
within-stage parameter effects; and states why the decision changed.

The standard evidence may use concise comparisons for all packages and deeper
analysis for selected cases. A high-quality solution is distinguished by the
generality and auditability of dataset replacement, not by five repeated
essays.

## 9. Constructive generation and packaging sequence

1. Generate and validate the fixed calendar.
2. Create the hidden plant/product profile and dense terminal-component demand.
3. Build a deterministic feasible quantity-flow witness backwards through the
   approved DAG, respecting yield, lead time, lot and effective-period rules.
4. Seed opening inventory only where early demand cannot otherwise be covered.
5. Calibrate source, transformation, shared-resource and storage limits around
   the witness, retaining selected pressure points and credible recourse.
6. Generate inventory policies and validate stock/value identities.
7. Generate thirty months of performance history and a sparse incident record
   tied to real candidate relationships.
8. Assemble the complete BASE package from the frozen structural and commercial
   data and the new planning facts.
9. Generate each stress package independently: copy every required fact file,
   add only that package's impact and recovery rows, and write a complete
   manifest. Do not also pre-apply those rows to another fact table.
10. Rebuild every package twice and prove byte-identical data and hashes.
11. Run each package through the same independent loader and validation path.
12. Run the retained private physical MILP only as a feasibility smoke check;
    retain no preferred allocation and expose no reference solution.
13. Assess the planning and dataset-interchangeability scorecard. Regenerate a
    complete package where materiality is weak; do not hand-edit CSV rows.

Namespaced deterministic sub-seeds isolate demand, capacity, inventory,
history and package generation so a deliberate adjustment to one family does
not silently reshuffle the others.

## 10. Proposed planning and dataset scorecard

The owner reviewed the recalibrated profile and its witnesses on 25 August
2026. These thresholds, planning seed `9042027` and the six package hashes
recorded in the implementation report are frozen.

| Metric | Proposed threshold |
|---|---:|
| Complete dataset packages | 6 of 6 |
| Required raw CSVs present and schema-valid | 150 of 150 |
| Packages requiring a lookup or fallback outside their own root | 0 |
| Package manifests with complete checksums and matching scenario identity | 6 of 6 |
| Packages ingested through the same loader and model-construction entry point | 6 of 6 |
| Calendar periods, contiguous and correctly dated | 12 of 12 per package |
| Boundary source/material/period capacity coverage | 264 of 264 per package |
| Recipe/period transformation-capacity coverage | 624 of 624 per package |
| Usable pool states with an explicit inventory policy | 159 of 159 per package |
| Plant/terminal-material/period demand coverage | 288 of 288 per package |
| Seller/material/month performance coverage | 2,100 of 2,100 per package |
| BASE physical feasibility | At least one independently validated zero-shortage witness |
| BASE boundary-source dependency | Zero shortage is infeasible when all boundary sourcing is disabled |
| Terminal demand streams with planned variation | 24 of 24; no flat copied series |
| Demand peaks materially above the stream median | At least 8 streams |
| Terminal service events requiring a supporting standard dispatch at least two periods earlier | At least 8 |
| Positive opening-stock states | 32–56, spanning at least three supplier tiers and plants |
| Capacity, shared-resource, lane or setup pressure witnesses | At least 16 across at least three constraint families |
| Shared-capacity groups containing multiple recipes | At least 6 |
| Multi-source pools with persistent historical service or quality contrast | At least 8 |
| Historical source-completeness flags marked `PARTIAL` | 3–10% of rows, clustered rather than random noise |
| Stress packages affecting at least one active terminal lineage | 5 of 5 |
| SCN-01 affected terminal materials | At least 2 |
| SCN-02 affected Asia–Europe corridors with a retained expedited alternative | At least 4 |
| SCN-03 affected plant/terminal demand streams with an approved alternate Tier-1 source | At least 3 |
| SCN-04 affected nodes and tiers | At least 5 nodes across Tier 2, Tier 3 and Tier 4 |
| SCN-05 selected critical-demand uplift | 10–15%, combined with SCN-01 and SCN-02 conditions |
| Cross-package cache leakage, target ambiguity or replacement-priority ties | 0 |

A pressure witness identifies the affected rows, periods, lineage and physical
mechanism. It demonstrates credible potential materiality, not a preferred
allocation. Solved cost, service, inventory and concentration differences are
WP7 acceptance evidence.

## 11. Minimal implementation shape

The implementation exists to generate and challenge datasets, not to become an
exemplar submission.

| File | Responsibility |
|---|---|
| `generator/generate_planning_data.py` | Generate the BASE calendar, capacity, inventory, demand and historical facts from the frozen inputs |
| `generator/generate_dataset_packages.py` | Assemble BASE and the five complete stress packages, including manifests and package-local impacts |
| `tooling/assess_dataset_packages.py` | Independently validate all six packages, effective facts, feasibility-witness consistency, temporal depth and scenario materiality |
| `tests/test_dataset_generation.py` | Test deterministic generation, package independence, common-loader compatibility and adversarial cases |

No new reference application, full recursive allocation, solver abstraction or
scenario-specific model family is required. The existing private harness may be
reused for the bounded physical-feasibility smoke check.

Private generation writes under `generated/datasets/` and
must not overwrite the student release. WP7 treats the frozen packages as its
viability-audit input. Promotion into the student release remains a later
controlled activity.

## 12. Validation and adversarial evidence

The independent assessment must cover:

1. complete package manifests, file counts, hashes and scenario identity;
2. schemas, keys, domains, periods, dates, UOMs and cross-file references within
   each package root;
3. dense capacity and demand coverage at the derived relationship grains;
4. capacity, storage, opening-stock and historical quantity identities;
5. lead-time indexing, same-period conversion and the P12 arrival boundary;
6. constructive BASE feasibility and absence of excessive artificial slack;
7. package-local target resolution, composition, precedence and recovery;
8. identical loader and model-construction behaviour across all six packages;
9. scenario lineage participation and available recourse; and
10. history relevance without treating exploratory evidence as an undeclared
    mathematical input.

Negative tests must include: a missing unchanged file, manifest/hash mismatch,
lookup outside the package root, stale dimensions retained after dataset
replacement, calendar gap, missing capacity row, invalid opening value, safety
stock above storage, impossible early demand, post-P12 arrival, unknown or
ambiguous impact target, multiplicative composition error, replacement-priority
tie, missing recovery, invalid availability precedence and a hard-coded
scenario-name dependency.

Required retained evidence is a manifest for every package, package-completeness
matrix, planning-depth scorecard, private feasibility-witness summary, temporal-
pressure witnesses, dataset-difference and materiality witnesses, reproducible
dataset hashes and a concise human-readable report.

## 13. Progress gates

1. **Design implemented — passed:** the complete-package contract, five
   scenario/system purposes, run-mode burden and history role are implemented.
   ADR-008 is accepted.
2. **BASE complete — passed:** all BASE planning facts generate deterministically
   and the bounded physical MILP check confirms zero shortage.
3. **Packages complete — passed:** all six self-contained datasets contain 25
   valid raw files, a matching manifest and no external fallback.
4. **Interchangeability demonstrated — passed:** the same loader, preparation
   and model-construction entry point accepts all six packages after complete
   state reset.
5. **Depth demonstrated — passed:** all 24 technical gates, including temporal,
   history and scenario-participation gates, pass with inspectable witnesses.
6. **Owner accepted — passed:** on 25 August 2026 the owner accepted the
   recalibrated data profile and froze all six datasets, seed, thresholds and
   package hashes after the whole-dataset audit passed 10/10 gates.

Passing WP6 means the data offers credible temporal and scenario depth through
interchangeable input packages. It does not establish an accepted optimiser, a
preferred resilience intervention or a complete consultant solution.
