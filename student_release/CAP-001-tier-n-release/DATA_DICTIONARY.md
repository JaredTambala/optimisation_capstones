# CAP-001 Data Dictionary

> Generated from `config/cap001_decision_config.json`. Do not edit directly.

Configuration version: `0.3.1`
Schema version: `0.3.1`

## Conventions

- UTF-8 CSV with one header row.
- Stable string identifiers; no business meaning is encoded in numeric suffixes.
- ISO-8601 dates and timezone-aware timestamps.
- Explicit currency and unit fields; probabilities and rates use 0–1 unless stated otherwise.
- Empty cells represent declared nullable values only. Literal placeholder strings such as `N/A` are invalid.
- Foreign keys and relationship rules are authoritative as listed below.

## Raw-data contracts

### `planning_calendar.csv`

Controlled 12-week planning calendar.

Primary key: `period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$`; P01-P12 | Stable period identifier. |
| `period_number` | integer | required | >= 1; <= 12 | Sequential period number. |
| `week_start_date` | string | required | date | Monday start date; P01 is 2027-01-04. |
| `week_end_date` | string | required | date | Sunday end date; P12 is 2027-03-28. |
| `order_cutoff_timestamp` | string | required | date-time | Timezone-aware planning cutoff. |
| `is_terminal_period` | boolean | required | — | True only for P12. |

Cross-field rules:

- Dates are contiguous Monday-Sunday weeks.
- Only P12 has is_terminal_period=true.

### `supplier_organisations.csv`

Fictional supplier organisations and parent relationships.

Primary key: `supplier_id`

Foreign keys:

- `parent_group_id` → `supplier_organisations.csv.supplier_id` (nullable)

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `supplier_id` | string | required | pattern `^SUP-[0-9]{4}$` | Stable fictional organisation identifier. |
| `supplier_name` | string | required | — | Fictional human-readable name. |
| `parent_group_id` | string | nullable | pattern `^SUP-[0-9]{4}$` | Ultimate fictional parent organisation. |
| `hq_country_code` | string | required | pattern `^[A-Z]{2}$`; ISO-3166 alpha-2 | Headquarters country. |
| `region_code` | string | required | pattern `^[A-Z][A-Z0-9_]*$`; Configured region | Risk-reporting region. |
| `financial_risk_band` | string | required | `LOW`, `MEDIUM`, `HIGH` | Synthetic continuity and credit signal. |
| `recovery_time_weeks` | integer | required | unit: weeks; >= 0 | Indicative severe-event recovery time. |
| `open_cost_participant_flag` | boolean | required | — | Participation in the nominated-source/open-cost programme. |
| `active_flag` | boolean | required | — | Current release status. |

### `network_nodes.csv`

Generic supplier-site and plant nodes.

Primary key: `node_id`

Foreign keys:

- `supplier_id` → `supplier_organisations.csv.supplier_id` (nullable)

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Stable physical-node identifier. |
| `supplier_id` | string | nullable | pattern `^SUP-[0-9]{4}$` | Owning supplier; null for Asterion plants. |
| `node_name` | string | required | — | Fictional site or plant name. |
| `node_type` | string | required | `SUPPLIER_SITE`, `PLANT` | Physical node class. |
| `node_tier` | string | required | `TIER_1`, `TIER_2`, `TIER_3`, `TIER_4`, `PLANT` | Tier following proximity to Asterion. |
| `external_boundary_flag` | boolean | required | — | Whether exogenous material prices may enter. |
| `processing_capability_flag` | boolean | required | — | Whether transformations may be configured. |
| `pooling_policy` | string | required | constant `WEIGHTED_AVERAGE` | Authoritative release-1 pooling policy. |
| `country_code` | string | required | pattern `^[A-Z]{2}$`; ISO-3166 alpha-2 | Physical country. |
| `region_code` | string | required | pattern `^[A-Z][A-Z0-9_]*$` | Scenario and analysis region. |
| `latitude` | number | required | unit: degrees; >= -90; <= 90 | Synthetic valid latitude. |
| `longitude` | number | required | unit: degrees; >= -180; <= 180 | Synthetic valid longitude. |
| `timezone` | string | required | IANA timezone | Local planning timezone. |
| `local_currency` | string | required | pattern `^[A-Z]{3}$`; ISO-4217 | Default local cost currency. |
| `site_risk_score` | number | required | >= 0; <= 100 | Exploratory risk signal. |
| `active_flag` | boolean | required | — | Current release status. |

### `plants.csv`

The four fixed Asterion plant nodes.

Primary key: `plant_id`

Foreign keys:

- `plant_id` → `network_nodes.csv.node_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `plant_id` | string | required | pattern `^NODE-[0-9]{4}$` | Asterion plant node. |
| `plant_name` | string | required | `Birmingham`, `Dortmund`, `Katowice`, `Zaragoza` | Fixed plant name. |
| `primary_role` | string | required | — | Narrative production role. |
| `base_currency` | string | required | constant `EUR` | Common optimisation currency. |
| `plant_priority_weight` | number | required | > 0 | Controlled service-priority weight. |
| `customer_region` | string | required | pattern `^[A-Z][A-Z0-9_]*$` | Customer-facing reporting region. |

### `materials.csv`

Poolable boundary, intermediate and terminal materials.

Primary key: `material_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Stable material identifier. |
| `material_name` | string | required | — | Fictional human-readable name. |
| `material_stage` | string | required | `BOUNDARY_RAW`, `PROCESSED`, `SUBASSEMBLY`, `PLANT_READY`, `TERMINAL` | Functional material stage. |
| `material_family` | string | required | pattern `^[A-Z][A-Z0-9_]*$` | Reporting, duty and scenario family. |
| `uom` | string | required | pattern `^[A-Z][A-Z0-9_]*$`; EA, KG, M or approved configured unit | One authoritative unit per poolable material. |
| `criticality_class` | string | required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Business service criticality. |
| `terminal_material_flag` | boolean | required | — | Whether plant terminal demand may reference the material. |
| `external_price_eligible_flag` | boolean | required | — | True only for declared boundary-sourced materials. |
| `poolable_flag` | boolean | required | — | Whether the material participates in inventory pools. |
| `shelf_life_weeks` | integer | nullable | unit: weeks; >= 0 | Narrative shelf life; no age buckets in release 1. |
| `active_flag` | boolean | required | — | Current release status. |

### `transformation_recipes.csv`

Transformation recipes at processing nodes.

Primary key: `recipe_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `output_material_id` → `materials.csv.material_id`
- `effective_from_period` → `planning_calendar.csv.period_id`
- `effective_to_period` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `recipe_id` | string | required | pattern `^RCP-[0-9]{5}$` | Stable transformation identifier. |
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Processing node. |
| `output_material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Produced material. |
| `recipe_group_id` | string | nullable | — | Alternative recipe group. |
| `activation_mode` | string | required | `BLENDABLE`, `EXCLUSIVE` | Alternative-use rule. |
| `yield_rate` | number | required | > 0; <= 1 | Fixed output yield. |
| `minimum_run_quantity` | number | required | >= 0 | Minimum positive output. |
| `setup_required_flag` | boolean | required | — | Whether positive production requires recipe activation. |
| `effective_from_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | First active period. |
| `effective_to_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Last active period. |
| `active_flag` | boolean | required | — | Current release status. |

### `transformation_inputs.csv`

Material inputs consumed by transformation recipes.

Primary key: `recipe_id, input_material_id`

Foreign keys:

- `recipe_id` → `transformation_recipes.csv.recipe_id`
- `input_material_id` → `materials.csv.material_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `recipe_id` | string | required | pattern `^RCP-[0-9]{5}$` | Owning recipe. |
| `input_material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Consumed material. |
| `quantity_per_output` | number | required | > 0 | Nominal coefficient before yield adjustment. |
| `scrap_recovery_flag` | boolean | required | — | Explicit recoverable-output flag; normally false. |
| `input_sequence` | integer | required | >= 1 | Stable display and validation order. |

### `material_flow_approvals.csv`

Approved material flows between nodes.

Primary key: `approval_id`

Foreign keys:

- `seller_node_id` → `network_nodes.csv.node_id`
- `buyer_node_id` → `network_nodes.csv.node_id`
- `material_id` → `materials.csv.material_id`
- `valid_from_period` → `planning_calendar.csv.period_id`
- `valid_to_period` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `approval_id` | string | required | pattern `^APR-[0-9]{5}$` | Stable approval identifier. |
| `seller_node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Approved origin. |
| `buyer_node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Approved destination. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Approved material. |
| `approval_status` | string | required | `APPROVED`, `CONDITIONAL`, `SUSPENDED` | Controlled approval status. |
| `valid_from_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | First valid period. |
| `valid_to_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Last valid period. |
| `maximum_approved_share` | number | nullable | >= 0; <= 1 | Optional approval-derived share cap. |
| `qualification_score` | number | required | >= 0; <= 100 | Supporting quality signal. |
| `notes` | string | nullable | — | Controlled qualification context. |

### `supply_contracts.csv`

Commercial contracts linked to approved flows.

Primary key: `contract_id`

Foreign keys:

- `approval_id` → `material_flow_approvals.csv.approval_id`
- `incoterm_code` → `incoterm_rules.csv.incoterm_code`
- `effective_from_period` → `planning_calendar.csv.period_id`
- `effective_to_period` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `contract_id` | string | required | pattern `^CTR-[0-9]{5}$` | Stable contract identifier. |
| `approval_id` | string | required | pattern `^APR-[0-9]{5}$` | Underlying approved flow. |
| `currency` | string | required | pattern `^[A-Z]{3}$` | Contract and fixed-cost currency. |
| `incoterm_code` | string | required | — | Simplified responsibility rule. |
| `contract_handling_days` | integer | required | unit: days; >= 0 | Preparation time before transit. |
| `minimum_order_quantity` | number | required | > 0 | Minimum positive order. |
| `order_multiple` | number | required | > 0 | Integer lot size. |
| `fixed_order_cost` | number | required | >= 0 | Direct fixed cost on order activation. |
| `horizon_activation_cost` | number | required | >= 0 | Non-capitalised relationship-use cost. |
| `payment_terms_days` | integer | required | >= 0 | Narrative payment terms. |
| `effective_from_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | First active period. |
| `effective_to_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Last active period. |
| `active_flag` | boolean | required | — | Current release status. |

### `incoterm_rules.csv`

Simplified capstone Incoterm responsibility rules.

Primary key: `incoterm_code`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `incoterm_code` | string | required | `EXW`, `FCA`, `CPT`, `CIP`, `DAP`, `DDP` | Controlled Incoterm subset. |
| `description` | string | required | — | Plain-English modelling description. |
| `buyer_pays_origin_transport` | boolean | required | — | Origin transport responsibility. |
| `buyer_pays_main_carriage` | boolean | required | — | Main carriage responsibility. |
| `buyer_pays_insurance` | boolean | required | — | Insurance responsibility. |
| `buyer_pays_import_duty` | boolean | required | — | Import duty responsibility. |
| `risk_transfer_stage` | string | required | — | Narrative risk-transfer stage. |
| `legal_disclaimer` | string | required | constant `This capstone Incoterm abstraction is not legal guidance.` | Fixed statement that this is not legal guidance. |

### `import_duty_rates.csv`

Simplified import-duty rules.

Primary key: `duty_rule_id`

Foreign keys:

- `effective_from_period` → `planning_calendar.csv.period_id`
- `effective_to_period` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `duty_rule_id` | string | required | pattern `^DUTY-[0-9]{5}$` | Stable duty rule identifier. |
| `origin_country_code` | string | required | pattern `^[A-Z]{2}$` | Dispatch country. |
| `destination_country_code` | string | required | pattern `^[A-Z]{2}$` | Receiving country. |
| `material_family` | string | required | pattern `^[A-Z][A-Z0-9_]*$` | Material family. |
| `duty_rate` | number | required | >= 0; <= 1 | Percentage of customs value. |
| `customs_value_basis` | string | required | pattern `^[A-Z][A-Z0-9_]*$`; GOODS, GOODS_PLUS_FREIGHT or approved configured basis | Authoritative calculation basis. |
| `effective_from_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | First active period. |
| `effective_to_period` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Last active period. |

### `source_capacity.csv`

Boundary-source material capacity by week.

Primary key: `node_id, material_id, period_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `material_id` → `materials.csv.material_id`
- `period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Boundary source node. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Externally priced material. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Capacity period. |
| `regular_capacity` | number | required | >= 0 | Normal source capacity. |
| `surge_capacity` | number | required | >= 0 | Additional available capacity. |
| `surge_unit_premium` | number | required | >= 0 | Capitalised surge premium. |
| `planned_downtime_fraction` | number | required | >= 0; <= 1 | Base planned reduction. |
| `minimum_supply_quantity` | number | required | >= 0 | Optional positive supply minimum. |

### `transformation_capacity.csv`

Recipe output capacity by node and week.

Primary key: `node_id, recipe_id, period_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `recipe_id` → `transformation_recipes.csv.recipe_id`
- `period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Processing node. |
| `recipe_id` | string | required | pattern `^RCP-[0-9]{5}$` | Capacity-controlled recipe. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Capacity period. |
| `regular_output_capacity` | number | required | >= 0 | Recipe limit when no shared group is present; otherwise the repeated regular group budget. |
| `surge_output_capacity` | number | required | >= 0 | Recipe limit when no shared group is present; otherwise the repeated surge group budget. |
| `surge_conversion_premium` | number | required | >= 0 | Capitalised incremental conversion cost. |
| `planned_downtime_fraction` | number | required | >= 0; <= 1 | Base planned capacity reduction. |
| `shared_capacity_group_id` | string | nullable | — | Shared production-resource identifier; all rows in a group-period repeat one common capacity budget. |
| `shared_capacity_coefficient` | number | nullable | > 0 | Shared group-capacity units consumed per unit of recipe output. |

### `shipping_lanes.csv`

Transport alternatives between nodes.

Primary key: `lane_id`

Foreign keys:

- `origin_node_id` → `network_nodes.csv.node_id`
- `destination_node_id` → `network_nodes.csv.node_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `lane_id` | string | required | pattern `^LANE-[0-9]{5}$` | Stable lane identifier. |
| `origin_node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Origin node. |
| `destination_node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Destination node. |
| `transport_mode` | string | required | `ROAD`, `SEA`, `RAIL`, `AIR` | Transport mode. |
| `distance_km` | number | required | unit: km; >= 0 | Synthetic route distance. |
| `base_transit_days` | number | required | unit: days; > 0 | Normal lane transit. |
| `transit_std_days` | number | required | unit: days; >= 0 | Historical variability signal. |
| `weekly_capacity` | number | required | >= 0 | Shared lane capacity. |
| `freight_currency` | string | required | pattern `^[A-Z]{3}$` | Freight charge currency. |
| `variable_freight_cost_per_unit` | number | required | >= 0 | Buyer-borne variable freight. |
| `fixed_shipment_cost` | number | required | >= 0 | Direct fixed lane cost. |
| `insurance_rate_pct_of_goods` | number | required | >= 0; <= 1 | Insurance rate on configured value. |
| `reliability_score` | number | required | >= 0; <= 100 | Exploratory reliability signal. |
| `expedited_flag` | boolean | required | — | Premium transport alternative. |
| `active_flag` | boolean | required | — | Current release status. |

### `external_source_prices.csv`

External unit prices for eligible boundary contracts only.

Primary key: `contract_id, material_id, period_id`

Foreign keys:

- `contract_id` → `supply_contracts.csv.contract_id`
- `material_id` → `materials.csv.material_id`
- `period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `contract_id` | string | required | pattern `^CTR-[0-9]{5}$` | Boundary-source external-price contract. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | External-price-eligible material. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Dispatch period. |
| `unit_price` | number | required | > 0 | Authoritative boundary price. |
| `currency` | string | required | pattern `^[A-Z]{3}$` | Price currency. |
| `price_source` | string | required | constant `SYNTHETIC_FIXED` | Synthetic source marker. |
| `scenario_sensitive_flag` | boolean | required | — | Whether configured price impacts may apply. |

### `conversion_costs.csv`

Transformation conversion, setup, overhead and markup inputs.

Primary key: `node_id, recipe_id, period_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `recipe_id` → `transformation_recipes.csv.recipe_id`
- `period_id` → `planning_calendar.csv.period_id`
- `markup_base_rule_id` → `cost_allocation_rules.csv.cost_rule_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Processing node. |
| `recipe_id` | string | required | pattern `^RCP-[0-9]{5}$` | Transformation. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Applicable period. |
| `currency` | string | required | pattern `^[A-Z]{3}$` | Cost currency. |
| `variable_conversion_cost_per_output` | number | required | >= 0 | Capitalised variable conversion cost. |
| `fixed_setup_cost` | number | required | >= 0 | Capitalised setup cost. |
| `eligible_overhead_fixed` | number | required | >= 0 | Capitalised fixed overhead. |
| `eligible_overhead_variable` | number | required | >= 0 | Capitalised variable overhead. |
| `markup_rate` | number | required | >= 0 | Exogenous supplier markup applied once. |
| `markup_base_rule_id` | string | required | pattern `^COST-[0-9]{4}$` | Rule defining eligible markup base. |
| `scenario_sensitive_flag` | boolean | required | — | Whether conversion-cost impacts may apply. |

### `cost_allocation_rules.csv`

Single-ledger cost classification and allocation policy.

Primary key: `cost_rule_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `cost_rule_id` | string | required | pattern `^COST-[0-9]{4}$` | Stable policy identifier. |
| `cost_component` | string | required | `EXTERNAL_PURCHASE`, `FREIGHT`, `DUTY`, `INSURANCE`, `FIXED_ORDER`, `FIXED_SHIPMENT`, `CONVERSION`, `SETUP`, `OVERHEAD`, `SURGE`, `MARKUP`, `HOLDING`, `ACTIVATION`, `SHORTAGE` | Controlled cost component. |
| `scope_type` | string | required | `GLOBAL`, `CONTRACT`, `LANE`, `RECIPE`, `MATERIAL_FAMILY` | Rule scope. |
| `scope_id` | string | nullable | — | Target for non-global rules. |
| `capitalised_flag` | boolean | required | — | Whether cost enters recursive material value. |
| `capitalisation_stage` | string | required | `SOURCE`, `RECEIPT`, `TRANSFORMATION`, `NONE` | Where value is added. |
| `allocation_basis` | string | required | `QUANTITY`, `GOODS_VALUE`, `ACTIVATION`, `DIRECT` | Calculation and allocation basis. |
| `markup_eligible_flag` | boolean | required | — | Membership in transformation markup base. |
| `noncapitalised_ledger_category` | string | nullable | — | Stage-2 ledger category for non-capitalised cost. |
| `precedence` | integer | required | >= 0 | Rule precedence; ties invalid at same scope. |

### `inventory_policies.csv`

Inventory permission, storage, safety and holding policy.

Primary key: `node_id, material_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `material_id` → `materials.csv.material_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Inventory location. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Stored material. |
| `allow_inventory_flag` | boolean | required | — | Whether closing inventory is permitted. |
| `safety_stock_quantity` | number | required | >= 0 | Configured target or requirement. |
| `safety_stock_treatment` | string | required | `REPORT_ONLY`, `SOFT`, `HARD` | Authoritative model treatment. |
| `maximum_storage_quantity` | number | required | >= 0 | Inventory upper bound. |
| `holding_cost_eur_per_unit_week` | number | required | >= 0 | Non-capitalised holding expense. |
| `minimum_meaningful_pool_quantity` | number | required | > 0 | Pool activation epsilon. |
| `terminal_target_quantity` | number | nullable | >= 0 | Optional P12 target. |

### `opening_inventory.csv`

Opening physical stock and book value.

Primary key: `node_id, material_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `material_id` → `materials.csv.material_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Inventory location. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Stored material. |
| `on_hand_quantity` | number | required | >= 0 | Physical stock. |
| `reserved_quantity` | number | required | >= 0 | Unavailable reserved stock. |
| `usable_quantity` | number | required | >= 0 | On-hand less reserved. |
| `opening_unit_cost_eur` | number | required | >= 0 | Book-value unit cost entering P01. |
| `opening_total_value_eur` | number | required | >= 0 | Usable quantity times unit cost. |
| `cost_basis_source` | string | required | constant `SYNTHETIC_BOOK_VALUE` | Valuation basis marker. |
| `valuation_date` | string | required | date | Opening cost-basis date. |

Cross-field rules:

- usable_quantity = on_hand_quantity - reserved_quantity
- opening_total_value_eur = usable_quantity * opening_unit_cost_eur within tolerance

### `terminal_demand.csv`

Fixed plant terminal-material demand by period.

Primary key: `plant_id, material_id, period_id`

Foreign keys:

- `plant_id` → `plants.csv.plant_id`
- `material_id` → `materials.csv.material_id`
- `period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `plant_id` | string | required | pattern `^NODE-[0-9]{4}$` | Demanding Asterion plant. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Terminal material. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Demand period. |
| `demand_quantity` | number | required | >= 0 | BASE terminal demand. |
| `priority_class` | string | required | `STANDARD`, `HIGH`, `CRITICAL` | Customer service priority. |
| `service_weight` | number | required | > 0 | Stage-1 weighted-shortage coefficient. |
| `shortage_penalty_eur_per_unit` | number | nullable | >= 0 | Reporting and sensitivity value. |

### `supplier_performance_history.csv`

Monthly supplier-node/material performance history.

Primary key: `node_id, material_id, month`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `material_id` → `materials.csv.material_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Observed supplier node. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Observed material. |
| `month` | string | required | date | Historical month start. |
| `ordered_quantity` | number | required | >= 0 | Observed ordered quantity. |
| `received_quantity` | number | required | >= 0 | Observed received quantity. |
| `on_time_quantity` | number | required | >= 0 | Quantity received on or before due date. |
| `accepted_quantity` | number | required | >= 0 | Quality-accepted quantity. |
| `average_actual_lead_time_days` | number | required | >= 0 | Observed average lead time. |
| `lead_time_std_days` | number | required | >= 0 | Observed lead-time variability. |
| `quality_incident_count` | integer | required | >= 0 | Monthly incident count. |
| `source_completeness_flag` | string | required | `COMPLETE`, `PARTIAL` | Controlled data-quality signal. |

### `incident_history.csv`

Historical synthetic disruption incidents.

Primary key: `incident_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `incident_id` | string | required | pattern `^INC-[0-9]{5}$` | Stable incident identifier. |
| `target_entity_type` | string | required | `NODE`, `ORGANISATION`, `PARENT_GROUP`, `REGION`, `LANE`, `RECIPE`, `MATERIAL` | Affected entity class. |
| `target_entity_id` | string | required | — | Affected entity. |
| `event_type` | string | required | `OUTAGE`, `STRIKE`, `WEATHER`, `PORT`, `ENERGY`, `QUALITY`, `CYBER` | Incident category. |
| `start_date` | string | required | date | Historical start. |
| `end_date` | string | required | date | Historical end. |
| `severity` | string | required | `LOW`, `MEDIUM`, `HIGH`, `SEVERE` | Qualitative severity. |
| `capacity_multiplier` | number | nullable | >= 0 | Observed or synthetic capacity factor. |
| `transit_multiplier` | number | nullable | > 0 | Observed or synthetic transit factor. |
| `cost_multiplier` | number | nullable | > 0 | Observed or synthetic cost factor. |
| `description` | string | required | — | Fictional customer-readable context. |

### `disruption_scenarios.csv`

Controlled BASE and five disruption scenarios.

Primary key: `scenario_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `scenario_id` | string | required | `BASE`, `SCN-01`, `SCN-02`, `SCN-03`, `SCN-04`, `SCN-05` | Stable scenario identifier. |
| `scenario_name` | string | required | — | Human-readable scenario name. |
| `scenario_category` | string | required | `BASE`, `SOURCE`, `LOGISTICS`, `NODE`, `REGIONAL`, `COMBINED` | Scenario family. |
| `severity` | string | required | `NORMAL`, `MODERATE`, `HIGH`, `SEVERE` | Qualitative severity. |
| `description` | string | required | — | Customer-facing narrative. |
| `recommended_run_mode` | string | required | `STRESS_ONLY`, `REOPTIMISE`, `BOTH` | Required application view. |
| `active_flag` | boolean | required | — | Available in the release. |

### `disruption_impacts.csv`

Deterministic scenario impacts and recovery rows.

Primary key: `impact_id`

Foreign keys:

- `scenario_id` → `disruption_scenarios.csv.scenario_id`
- `target_material_id` → `materials.csv.material_id` (nullable)
- `start_period_id` → `planning_calendar.csv.period_id`
- `end_period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `impact_id` | string | required | pattern `^IMP-[0-9]{5}$` | Stable impact identifier. |
| `scenario_id` | string | required | `BASE`, `SCN-01`, `SCN-02`, `SCN-03`, `SCN-04`, `SCN-05` | Owning scenario. |
| `target_entity_type` | string | required | `NODE`, `ORGANISATION`, `PARENT_GROUP`, `REGION`, `LANE`, `RECIPE`, `MATERIAL`, `EXTERNAL_PRICE`, `CONVERSION_COST`, `TERMINAL_DEMAND` | Target class. |
| `target_entity_id` | string | required | — | Target identifier or controlled compound key. |
| `target_material_id` | string | nullable | pattern `^MAT-[0-9]{4}$` | Optional material refinement. |
| `target_cost_component` | string | nullable | `EXTERNAL_PURCHASE`, `FREIGHT`, `DUTY`, `INSURANCE`, `FIXED_ORDER`, `FIXED_SHIPMENT`, `CONVERSION`, `SETUP`, `OVERHEAD`, `SURGE`, `MARKUP`, `HOLDING`, `ACTIVATION`, `SHORTAGE` | Optional cost-category refinement. |
| `start_period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | First affected period. |
| `end_period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Last affected period. |
| `availability_flag` | boolean | required | — | False overrides applicable capacity or lane availability. |
| `capacity_multiplier` | number | required | >= 0 | Source or transformation capacity multiplier. |
| `lane_capacity_multiplier` | number | required | >= 0 | Lane capacity multiplier. |
| `transit_time_multiplier` | number | required | > 0 | Transit multiplier before week conversion. |
| `cost_multiplier` | number | required | > 0 | Configured target-cost multiplier. |
| `demand_multiplier` | number | required | >= 0 | Terminal-demand multiplier. |
| `replacement_field` | string | nullable | — | Field replaced under explicit semantics. |
| `replacement_value` | number | nullable | — | Replacement value. |
| `impact_priority` | integer | required | >= 0 | Replacement precedence; ties rejected. |
| `notes` | string | nullable | — | Recovery or targeting explanation. |

### `fx_rates.csv`

Synthetic currency conversion to EUR.

Primary key: `currency, period_id`

Foreign keys:

- `period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `currency` | string | required | pattern `^[A-Z]{3}$` | Source currency. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Applicable period. |
| `eur_per_currency_unit` | number | required | > 0 | EUR per source-currency unit. |
| `rate_source` | string | required | constant `SYNTHETIC_FIXED` | Synthetic source marker. |
| `scenario_sensitive_flag` | boolean | required | — | Whether an approved scenario may change the rate. |

### `baseline_standard_costs.csv`

Comparator-only standard costs for the diagnostic MILP.

Primary key: `node_id, material_id, period_id`

Foreign keys:

- `node_id` → `network_nodes.csv.node_id`
- `material_id` → `materials.csv.material_id`
- `period_id` → `planning_calendar.csv.period_id`

| Column | Type | Required/nullable | Domain or constraints | Definition |
|---|---|---|---|---|
| `node_id` | string | required | pattern `^NODE-[0-9]{4}$` | Comparator supply node. |
| `material_id` | string | required | pattern `^MAT-[0-9]{4}$` | Comparator intermediate material. |
| `period_id` | string | required | pattern `^P(0[1-9]|1[0-2])$` | Applicable period. |
| `standard_unit_cost_eur` | number | required | > 0 | Fixed comparator cost. |
| `derivation_method` | string | required | constant `SYNTHETIC_STANDARD_COST` | Non-authoritative derivation marker. |
| `baseline_only_flag` | boolean | required | constant `True` | Must be true and enforced by isolation. |
| `prohibited_for_recursive_model_flag` | boolean | required | constant `True` | Recursive route must reject the file. |

## Required-output contracts

### `run_metadata.json`

Path: `artifacts/evaluation/run_metadata.json`  
One standardized record per run.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `capstone_id` | string | required | constant `CAP-001` |
| `capstone_version` | string | required | — |
| `data_version` | string | required | — |
| `model_version` | string | required | — |
| `scenario_id` | string | required | `BASE`, `SCN-01`, `SCN-02`, `SCN-03`, `SCN-04`, `SCN-05` |
| `run_id` | string | required | — |
| `git_commit` | string | required | — |
| `run_mode` | string | required | `BASELINE_MILP`, `RECURSIVE_MINLP`, `STRESS_ONLY`, `REOPTIMISE` |
| `formulation_type` | string | required | — |
| `formulation_classification` | string | required | `EXACT`, `RELAXED`, `APPROXIMATE`, `HEURISTIC` |
| `method_description` | string | required | — |
| `approximation_identifier` | string | nullable/conditional | — |
| `solver_name` | string | required | — |
| `solver_version` | string | nullable/conditional | — |
| `solver_options_hash` | string | required | — |
| `licence_access_route` | string | required | — |
| `status` | string | required | `globally_optimal`, `locally_optimal`, `feasible_time_limited`, `best_found`, `infeasible`, `solver_failed` |
| `raw_termination_condition` | string | required | — |
| `termination_message` | string | required | — |
| `success_flag` | boolean | required | — |
| `stage_1_shortage` | number | nullable/conditional | — |
| `stage_2_value_cost` | number | nullable/conditional | — |
| `stage_3_tiebreak` | number | nullable/conditional | — |
| `incumbent_primal_objective` | number | nullable/conditional | — |
| `best_bound` | number | nullable/conditional | — |
| `absolute_gap` | number | nullable/conditional | — |
| `relative_gap` | number | nullable/conditional | — |
| `random_seed` | integer | required | — |
| `number_of_starts` | integer | required | — |
| `selected_start` | integer | nullable/conditional | — |
| `warm_start_source` | string | nullable/conditional | — |
| `iteration_or_node_count` | integer | nullable/conditional | — |
| `started_at` | string | required | — |
| `completed_at` | string | required | — |
| `runtime_seconds` | number | required | — |
| `hardware_profile` | string | required | — |
| `peak_memory_mb` | number | nullable/conditional | — |
| `hard_violation_count` | integer | required | — |
| `max_quantity_residual` | number | required | — |
| `max_value_residual_eur` | number | required | — |
| `max_unit_cost_residual_eur_per_unit` | number | required | — |
| `reconciliation_pass_flag` | boolean | required | — |
| `input_checksums_hash` | string | required | — |
| `configuration_hash` | string | required | — |
| `output_checksums_hash` | string | required | — |

### `metrics.json`

Path: `artifacts/evaluation/metrics.json`  
Run-level business, validation and resilience metrics.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `capstone_id` | string | required | constant `CAP-001` |
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `demand_quantity` | number | required | — |
| `served_quantity` | number | required | — |
| `shortage_quantity` | number | required | — |
| `service_rate` | number | required | — |
| `weighted_shortage` | number | required | — |
| `terminal_served_value_eur` | number | required | — |
| `incremental_spend_eur` | number | required | — |
| `closing_inventory_quantity` | number | required | — |
| `closing_inventory_value_eur` | number | required | — |
| `noncapitalised_cost_eur` | number | required | — |
| `hard_violation_count` | integer | required | — |
| `maximum_residual` | number | required | — |
| `resilience_metrics` | object | required | — |

### `orders.csv`

Path: `artifacts/solution/orders.csv`  
Contract-material dispatch-period orders.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `contract_id` | string | required | — |
| `material_id` | string | required | — |
| `dispatch_period_id` | string | required | — |
| `order_active` | boolean | required | — |
| `order_lots` | integer | required | — |
| `order_quantity` | number | required | — |
| `external_unit_price` | number | nullable/conditional | — |
| `fixed_order_cost_eur` | number | required | — |
| `horizon_activation_cost_eur` | number | required | — |

### `shipments.csv`

Path: `artifacts/solution/shipments.csv`  
Arc/lane material dispatch and arrival flows with value.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `approval_id` | string | required | — |
| `lane_id` | string | required | — |
| `material_id` | string | required | — |
| `dispatch_period_id` | string | required | — |
| `arrival_period_id` | string | required | — |
| `quantity` | number | required | — |
| `source_pool_unit_cost_eur` | number | required | — |
| `dispatched_value_eur` | number | required | — |
| `freight_eur` | number | required | — |
| `duty_eur` | number | required | — |
| `insurance_eur` | number | required | — |
| `fixed_shipment_addition_eur` | number | required | — |
| `receipt_value_eur` | number | required | — |

### `production.csv`

Path: `artifacts/solution/production.csv`  
Node-recipe-period production and value.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `node_id` | string | required | — |
| `recipe_id` | string | required | — |
| `period_id` | string | required | — |
| `output_quantity` | number | required | — |
| `input_quantity` | number | required | — |
| `input_value_eur` | number | required | — |
| `yield_rate` | number | required | — |
| `regular_capacity_used` | number | required | — |
| `surge_capacity_used` | number | required | — |
| `conversion_eur` | number | required | — |
| `setup_eur` | number | required | — |
| `overhead_eur` | number | required | — |
| `markup_eur` | number | required | — |
| `output_value_eur` | number | required | — |

### `inventory_cost_rollforward.csv`

Path: `artifacts/solution/inventory_cost_rollforward.csv`  
Node-material-period quantity and value pool roll-forward.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `node_id` | string | required | — |
| `material_id` | string | required | — |
| `period_id` | string | required | — |
| `opening_quantity` | number | required | — |
| `opening_value_eur` | number | required | — |
| `receipt_quantity` | number | required | — |
| `receipt_value_eur` | number | required | — |
| `production_quantity` | number | required | — |
| `production_value_eur` | number | required | — |
| `pool_quantity` | number | required | — |
| `pool_value_eur` | number | required | — |
| `pool_unit_cost_eur` | number | required | — |
| `shipped_quantity` | number | required | — |
| `consumed_quantity` | number | required | — |
| `served_quantity` | number | required | — |
| `closing_quantity` | number | required | — |
| `closing_value_eur` | number | required | — |

### `demand_service.csv`

Path: `artifacts/solution/demand_service.csv`  
Plant-terminal-material-period demand and service.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `plant_id` | string | required | — |
| `material_id` | string | required | — |
| `period_id` | string | required | — |
| `demand_quantity` | number | required | — |
| `served_quantity` | number | required | — |
| `shortage_quantity` | number | required | — |
| `unit_cost_eur` | number | required | — |
| `served_value_eur` | number | required | — |

### `cost_component_ledger.csv`

Path: `artifacts/solution/cost_component_ledger.csv`  
Unique cost-component ledger.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `ledger_entry_id` | string | required | — |
| `cost_component` | string | required | — |
| `entity_type` | string | required | — |
| `entity_id` | string | required | — |
| `period_id` | string | required | — |
| `amount_local` | number | required | — |
| `currency` | string | required | — |
| `amount_eur` | number | required | — |
| `capitalised_flag` | boolean | required | — |
| `capitalisation_stage` | string | required | — |
| `markup_eligible_flag` | boolean | required | — |
| `ledger_classification` | string | required | — |

### `cost_lineage.csv`

Path: `artifacts/solution/cost_lineage.csv`  
Terminal demand to source and value-add contributions.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `plant_id` | string | required | — |
| `terminal_material_id` | string | required | — |
| `period_id` | string | required | — |
| `contribution_type` | string | required | `EXTERNAL_SOURCE`, `VALUE_ADD` |
| `contribution_entity_id` | string | required | — |
| `cost_component` | string | required | — |
| `contribution_value_eur` | number | required | — |
| `contribution_share` | number | required | — |

### `recursive_cost_reconciliation.csv`

Path: `artifacts/solution/recursive_cost_reconciliation.csv`  
Equation-level recursive quantity/value reconciliation.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `equation_id` | string | required | — |
| `equation_family` | string | required | — |
| `entity_type` | string | required | — |
| `entity_id` | string | required | — |
| `period_id` | string | nullable/conditional | — |
| `lhs_value` | number | required | — |
| `rhs_value` | number | required | — |
| `absolute_residual` | number | required | — |
| `relative_residual` | number | required | — |
| `tolerance` | number | required | — |
| `pass_flag` | boolean | required | — |

### `constraint_report.csv`

Path: `artifacts/evaluation/constraint_report.csv`  
Constraint-family feasibility evidence.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `constraint_family` | string | required | — |
| `entity_type` | string | required | — |
| `entity_id` | string | required | — |
| `period_id` | string | nullable/conditional | — |
| `lhs_value` | number | required | — |
| `sense` | string | required | `<=`, `=`, `>=` |
| `rhs_value` | number | required | — |
| `slack` | number | required | — |
| `bound_or_dual_value` | number | nullable/conditional | — |
| `violation_amount` | number | required | — |
| `hard_constraint_flag` | boolean | required | — |

### `reconciliation_summary.json`

Path: `artifacts/evaluation/reconciliation_summary.json`  
Run-level reconciliation summary.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `run_id` | string | required | — |
| `scenario_id` | string | required | — |
| `quantity_checks` | integer | required | — |
| `value_checks` | integer | required | — |
| `unit_cost_checks` | integer | required | — |
| `failed_checks` | integer | required | — |
| `maximum_quantity_residual` | number | required | — |
| `maximum_value_residual_eur` | number | required | — |
| `maximum_unit_cost_residual_eur_per_unit` | number | required | — |
| `maximum_integrality_residual` | number | required | — |
| `maximum_bound_violation` | number | required | — |
| `reconciliation_pass_flag` | boolean | required | — |

### `baseline_comparison.csv`

Path: `artifacts/evaluation/baseline_comparison.csv`  
Fixed-price versus recursive method comparison by scenario.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `method` | string | required | — |
| `scenario_id` | string | required | — |
| `service_rate` | number | required | — |
| `weighted_shortage` | number | required | — |
| `economic_value_eur` | number | required | — |
| `closing_inventory_value_eur` | number | required | — |
| `resilience_metric` | number | nullable/conditional | — |
| `formulation_classification` | string | required | `EXACT`, `RELAXED`, `APPROXIMATE`, `HEURISTIC` |
| `status` | string | required | — |
| `runtime_seconds` | number | required | — |
| `caveats` | string | required | — |

### `scenario_comparison.csv`

Path: `artifacts/solution/scenario_comparison.csv`  
Detailed plan-scenario-run-mode comparison.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `plan_id` | string | required | — |
| `scenario_id` | string | required | — |
| `run_mode` | string | required | `STRESS_ONLY`, `REOPTIMISE` |
| `service_rate` | number | required | — |
| `shortage_quantity` | number | required | — |
| `economic_value_eur` | number | required | — |
| `incremental_spend_eur` | number | required | — |
| `closing_inventory_value_eur` | number | required | — |
| `resilience_metric_name` | string | required | — |
| `resilience_metric_value` | number | required | — |
| `status` | string | required | — |
| `runtime_seconds` | number | required | — |

### `scenario_results.csv`

Path: `artifacts/evaluation/scenario_results.csv`  
Common method-scenario evaluation summary.

| Field | Type | Required/nullable | Definition/constraints |
|---|---|---|---|
| `method` | string | required | — |
| `scenario_id` | string | required | — |
| `feasible` | boolean | required | — |
| `formulation_type` | string | required | — |
| `objective_value` | number | nullable/conditional | — |
| `runtime_seconds` | number | required | — |
| `primary_business_metric` | number | nullable/conditional | — |
| `secondary_business_metric` | number | nullable/conditional | — |
| `status` | string | required | — |
| `notes` | string | required | — |
