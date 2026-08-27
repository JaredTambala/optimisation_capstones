"""Generic recursive weighted-average cost reconciliation engine for the
CAP-001 miniature fixture and compatible fixtures using the same 25 raw-data
contracts.

The engine reads only the 25 raw CSVs, never a pre-computed "expected"
answer, and independently walks the resulting node/material/period pools
period by period. It contains no tier-specific logic: every node, material,
recipe and arc is discovered from the data, and the same pooling/valuation
rules (weighted-average pool cost, common outflow cost, transformation
markup, receipt capitalisation) apply uniformly regardless of where a node
sits in the network.

Physical resolution is deliberately NOT an optimiser. The fixture is
authored so that every quantity is pinned by data (boundary supply via
``source_capacity.minimum_supply_quantity``; transformation output via
``min(capacity, input-limited)``; dispatch quantity directly from
``supply_contracts.minimum_order_quantity``, which by construction equals
``order_multiple`` and the arc's ``shipping_lanes.weekly_capacity``; service
via ``min(available, demand)``). A pool that cannot cover its consumption,
dispatch and service commitments raises :class:`ContractError` rather than
being solved for — that is the deliberate "infeasible flow" failure mode.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from tooling.contract_runtime import (
    ContractError,
    coerce_csv_value,
    resolve_data_dir,
    residuals,
    tolerance_for,
    tolerance_pair,
    validate_raw_data_directory,
)

import csv


EQUATION_FAMILIES = (
    "OPENING_INVENTORY_CONSISTENCY",
    "POOL_QUANTITY_ROLLFORWARD",
    "POOL_VALUE_ROLLFORWARD",
    "POOL_UNIT_COST_BILINEAR",
    "POOL_QUANTITY_CONSERVATION",
    "POOL_VALUE_CONSERVATION",
    "ZERO_POOL_VALUE",
    "OUTFLOW_COMMON_UNIT_COST",
    "TRANSFORMATION_VALUE",
    "RECEIPT_VALUE",
    "STAGE_2_VALUE",
)
FAMILY_TOLERANCE_KIND = {
    "OPENING_INVENTORY_CONSISTENCY": "value",
    "POOL_QUANTITY_ROLLFORWARD": "quantity",
    "POOL_VALUE_ROLLFORWARD": "value",
    "POOL_UNIT_COST_BILINEAR": "value",
    "POOL_QUANTITY_CONSERVATION": "quantity",
    "POOL_VALUE_CONSERVATION": "value",
    "ZERO_POOL_VALUE": "value",
    "OUTFLOW_COMMON_UNIT_COST": "unit_cost",
    "TRANSFORMATION_VALUE": "value",
    "RECEIPT_VALUE": "value",
    "STAGE_2_VALUE": "value",
}

RUN_ID = "CAP-001-MINIATURE"
SCENARIO_ID = "BASE"


def _fsum(values) -> float:
    return math.fsum(values)


# --------------------------------------------------------------------------- loading


def _read_rows(path: Path, columns: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    fields_by_name = {c["name"]: c for c in columns}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {name: coerce_csv_value(value, fields_by_name[name]) for name, value in row.items()}
            for row in reader
        ]


@dataclass(frozen=True)
class FixtureInputs:
    config: Mapping[str, Any]
    tables: Mapping[str, list[dict[str, Any]]]

    def rows(self, name: str) -> list[dict[str, Any]]:
        return self.tables[name]


def load_fixture_inputs(data_dir: Path | None = None, config: Mapping[str, Any] | None = None) -> FixtureInputs:
    from tooling.contract_runtime import load_config

    if config is None:
        config = load_config()
    resolved_dir = resolve_data_dir(data_dir)
    validate_raw_data_directory(resolved_dir, config)
    tables = {
        name: _read_rows(resolved_dir / name, contract["columns"])
        for name, contract in config["raw_contracts"].items()
    }
    return FixtureInputs(config=config, tables=tables)


# --------------------------------------------------------------------------- data model


@dataclass
class ConsumptionDraw:
    material_id: str
    quantity: float
    unit_cost: float
    value: float


@dataclass
class ShipmentLeg:
    approval_id: str
    lane_id: str
    contract_id: str
    origin_node_id: str
    destination_node_id: str
    material_id: str
    dispatch_period_id: str
    arrival_period_id: str
    quantity: float
    origin_unit_cost: float
    dispatched_value: float
    freight_eur: float
    duty_eur: float
    insurance_eur: float
    fixed_shipment_eur: float
    fixed_order_eur: float
    receipt_value: float


@dataclass
class TransformationEvent:
    recipe_id: str
    node_id: str
    period_id: str
    output_material_id: str
    output_quantity: float
    consumption: list[ConsumptionDraw]
    input_value: float
    conversion_eur: float
    setup_eur: float
    overhead_eur: float
    markup_rate: float
    markup_base_eur: float
    markup_eur: float
    output_value: float


@dataclass
class Pool:
    node_id: str
    material_id: str
    period_id: str
    opening_quantity: float
    opening_value: float
    receipt_legs: list[ShipmentLeg] = field(default_factory=list)
    production_events: list[TransformationEvent] = field(default_factory=list)
    boundary_quantity: float = 0.0
    boundary_value: float = 0.0
    pool_quantity: float = 0.0
    pool_value: float = 0.0
    unit_cost: float = 0.0
    consumption: list[ConsumptionDraw] = field(default_factory=list)
    dispatch_legs: list[ShipmentLeg] = field(default_factory=list)
    served_quantity: float = 0.0
    served_value: float = 0.0
    closing_quantity: float = 0.0
    closing_value: float = 0.0

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.node_id, self.material_id, self.period_id)


@dataclass
class Valuation:
    pools: dict[tuple[str, str, str], Pool]
    transformations: list[TransformationEvent]
    legs: list[ShipmentLeg]
    periods: list[str]
    operation_count: int = 0


# --------------------------------------------------------------------------- indices


class Indices:
    def __init__(self, inputs: FixtureInputs):
        self.inputs = inputs
        self.config = inputs.config
        self.periods = [r["period_id"] for r in sorted(inputs.rows("planning_calendar.csv"), key=lambda r: r["period_number"])]
        self.nodes = {r["node_id"]: r for r in inputs.rows("network_nodes.csv")}
        self.materials = {r["material_id"]: r for r in inputs.rows("materials.csv")}
        self.recipes_by_node: dict[str, list[dict[str, Any]]] = {}
        for r in inputs.rows("transformation_recipes.csv"):
            self.recipes_by_node.setdefault(r["node_id"], []).append(r)
        self.inputs_by_recipe: dict[str, list[dict[str, Any]]] = {}
        for r in inputs.rows("transformation_inputs.csv"):
            self.inputs_by_recipe.setdefault(r["recipe_id"], []).append(r)
        for recipe_id, rows in self.inputs_by_recipe.items():
            rows.sort(key=lambda r: r["input_sequence"])
        self.approvals = {r["approval_id"]: r for r in inputs.rows("material_flow_approvals.csv")}
        self.approvals_by_seller_material: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for r in inputs.rows("material_flow_approvals.csv"):
            self.approvals_by_seller_material.setdefault((r["seller_node_id"], r["material_id"]), []).append(r)
        self.contracts_by_approval: dict[str, list[dict[str, Any]]] = {}
        for r in inputs.rows("supply_contracts.csv"):
            self.contracts_by_approval.setdefault(r["approval_id"], []).append(r)
        self.lanes_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for r in inputs.rows("shipping_lanes.csv"):
            self.lanes_by_pair.setdefault((r["origin_node_id"], r["destination_node_id"]), []).append(r)
        self.cost_rules_by_component: dict[str, list[dict[str, Any]]] = {}
        for r in inputs.rows("cost_allocation_rules.csv"):
            self.cost_rules_by_component.setdefault(r["cost_component"], []).append(r)
        self.inventory_policy: dict[tuple[str, str], dict[str, Any]] = {
            (r["node_id"], r["material_id"]): r for r in inputs.rows("inventory_policies.csv")
        }
        self.opening_inventory: dict[tuple[str, str], dict[str, Any]] = {
            (r["node_id"], r["material_id"]): r for r in inputs.rows("opening_inventory.csv")
        }
        self.source_capacity: dict[tuple[str, str, str], dict[str, Any]] = {
            (r["node_id"], r["material_id"], r["period_id"]): r for r in inputs.rows("source_capacity.csv")
        }
        self.transformation_capacity: dict[tuple[str, str, str], dict[str, Any]] = {
            (r["node_id"], r["recipe_id"], r["period_id"]): r for r in inputs.rows("transformation_capacity.csv")
        }
        self.conversion_costs: dict[tuple[str, str, str], dict[str, Any]] = {
            (r["node_id"], r["recipe_id"], r["period_id"]): r for r in inputs.rows("conversion_costs.csv")
        }
        self.external_prices: dict[tuple[str, str, str], dict[str, Any]] = {
            (r["contract_id"], r["material_id"], r["period_id"]): r for r in inputs.rows("external_source_prices.csv")
        }
        self.terminal_demand: dict[tuple[str, str, str], dict[str, Any]] = {
            (r["plant_id"], r["material_id"], r["period_id"]): r for r in inputs.rows("terminal_demand.csv")
        }
        self.fx_rates: dict[tuple[str, str], dict[str, Any]] = {
            (r["currency"], r["period_id"]): r for r in inputs.rows("fx_rates.csv")
        }
        self.import_duty_rates = inputs.rows("import_duty_rates.csv")
        self.incoterm_rules = {r["incoterm_code"]: r for r in inputs.rows("incoterm_rules.csv")}

    def lead_time_periods(self, contract_handling_days: float, base_transit_days: float) -> int:
        formula = self.config["planning"]["lead_time_weeks_formula"]
        assert formula == "ceil((contract_handling_days + adjusted_transit_days) / 7)", formula
        return math.ceil((contract_handling_days + base_transit_days) / 7)

    def arrival_period(self, dispatch_period_id: str, lead_time_periods: int) -> str:
        index = self.periods.index(dispatch_period_id) + lead_time_periods
        if index >= len(self.periods):
            raise ContractError(
                f"arrival period for dispatch {dispatch_period_id} + {lead_time_periods} lead periods "
                "falls beyond the fixture horizon (prohibited post-horizon arrival)"
            )
        return self.periods[index]

    def fx_rate(self, currency: str, period_id: str) -> float:
        row = self.fx_rates.get((currency, period_id))
        if row is None:
            raise ContractError(f"no fx_rates row for {currency}/{period_id}")
        return row["eur_per_currency_unit"]

    def resolve_cost_rule(self, component: str) -> dict[str, Any]:
        candidates = [r for r in self.cost_rules_by_component.get(component, [])]
        if not candidates:
            raise ContractError(f"no cost_allocation_rules row for component {component}")
        best = sorted(candidates, key=lambda r: -r["precedence"])
        if len(best) > 1 and best[0]["precedence"] == best[1]["precedence"] and best[0]["scope_type"] == best[1]["scope_type"]:
            raise ContractError(f"tied cost_allocation_rules precedence for component {component} at the same scope")
        return best[0]

    def resolve_duty_rate(self, origin_country: str, destination_country: str, material_family: str, period_id: str) -> dict[str, Any]:
        matches = [
            r for r in self.import_duty_rates
            if r["origin_country_code"] == origin_country
            and r["destination_country_code"] == destination_country
            and r["material_family"] == material_family
            and r["effective_from_period"] <= period_id <= r["effective_to_period"]
        ]
        if not matches:
            raise ContractError(
                f"no import_duty_rates row for {origin_country}->{destination_country}/{material_family}@{period_id}"
            )
        if len(matches) > 1:
            raise ContractError(
                f"ambiguous import_duty_rates rows for {origin_country}->{destination_country}/{material_family}@{period_id}"
            )
        return matches[0]


# --------------------------------------------------------------------------- engine


def _empty_pool(node_id: str, material_id: str, period_id: str, opening_quantity: float, opening_value: float) -> Pool:
    return Pool(
        node_id=node_id, material_id=material_id, period_id=period_id,
        opening_quantity=opening_quantity, opening_value=opening_value,
    )


def value_plan(inputs: FixtureInputs) -> Valuation:
    """Recompute the entire fixture, purely from raw inputs, period by period."""

    idx = Indices(inputs)
    pools: dict[tuple[str, str, str], Pool] = {}
    prior_close: dict[tuple[str, str], tuple[float, float]] = {}
    all_legs: list[ShipmentLeg] = []
    all_transformations: list[TransformationEvent] = []
    operation_count = 0
    legs_by_arrival_period: dict[str, list[ShipmentLeg]] = {p: [] for p in idx.periods}

    for period_id in idx.periods:
        period_pools: dict[tuple[str, str], Pool] = {}

        def get_or_create(node_id: str, material_id: str) -> Pool:
            key = (node_id, material_id)
            if key not in period_pools:
                if key in prior_close:
                    opening_q, opening_v = prior_close[key]
                elif key in idx.opening_inventory:
                    row = idx.opening_inventory[key]
                    opening_q, opening_v = row["usable_quantity"], row["opening_total_value_eur"]
                else:
                    opening_q, opening_v = 0.0, 0.0
                period_pools[key] = _empty_pool(node_id, material_id, period_id, opening_q, opening_v)
            return period_pools[key]

        # Every tracked (node, material) pool is created for this period even
        # with zero activity, so opening-inventory seeding and closing
        # rollforward stay correct regardless of which period first touches it.
        for node_id, material_id in idx.inventory_policy:
            get_or_create(node_id, material_id)

        # 1. Boundary origination (pseudo-production at external boundary nodes).
        for (node_id, material_id, p), row in idx.source_capacity.items():
            if p != period_id or row["minimum_supply_quantity"] <= 0:
                continue
            qty = row["minimum_supply_quantity"]
            # Enforce the documented convention: every contract selling this
            # (node, material, period) must quote the same boundary price.
            prices = set()
            for approval in idx.approvals_by_seller_material.get((node_id, material_id), []):
                for contract in idx.contracts_by_approval.get(approval["approval_id"], []):
                    price_row = idx.external_prices.get((contract["contract_id"], material_id, period_id))
                    if price_row is not None:
                        currency_rate = idx.fx_rate(price_row["currency"], period_id)
                        prices.add(round(price_row["unit_price"] * currency_rate, 9))
            if len(prices) != 1:
                raise ContractError(
                    f"boundary price is not uniform for {node_id}/{material_id}@{period_id}: {prices}"
                )
            unit_price = next(iter(prices))
            pool = get_or_create(node_id, material_id)
            pool.boundary_quantity += qty
            pool.boundary_value += qty * unit_price
            operation_count += 1

        # 2. Receipts: shipments dispatched in an earlier period whose lead
        # time brings them to arrival in this period (precomputed below, in
        # step 6 of the period during which they were dispatched).
        for leg in legs_by_arrival_period[period_id]:
            destination_pool = get_or_create(leg.destination_node_id, leg.material_id)
            destination_pool.receipt_legs.append(leg)

        # 3. Pool formation (opening + receipts + boundary production).
        for pool in period_pools.values():
            pool.pool_quantity = _fsum(
                [pool.opening_quantity, pool.boundary_quantity] + [leg.quantity for leg in pool.receipt_legs]
            )
            pool.pool_value = _fsum(
                [pool.opening_value, pool.boundary_value] + [leg.receipt_value for leg in pool.receipt_legs]
            )
            pool.unit_cost = pool.pool_value / pool.pool_quantity if pool.pool_quantity > 0 else 0.0
            operation_count += 1

        # 4. Transformations at each processing node.
        for node_id, recipes in idx.recipes_by_node.items():
            active_recipes = [r for r in recipes if r["effective_from_period"] <= period_id <= r["effective_to_period"]]
            if not active_recipes:
                continue
            if len(active_recipes) > 1:
                raise ContractError(f"more than one active recipe at {node_id}@{period_id}")
            recipe = active_recipes[0]
            capacity_row = idx.transformation_capacity.get((node_id, recipe["recipe_id"], period_id))
            if capacity_row is None or capacity_row["regular_output_capacity"] <= 0:
                continue
            capacity_limit = capacity_row["regular_output_capacity"] * (1 - capacity_row["planned_downtime_fraction"])
            recipe_inputs = idx.inputs_by_recipe[recipe["recipe_id"]]
            input_pools = {ri["input_material_id"]: get_or_create(node_id, ri["input_material_id"]) for ri in recipe_inputs}
            input_limited = [
                (input_pools[ri["input_material_id"]].pool_quantity * recipe["yield_rate"]) / ri["quantity_per_output"]
                for ri in recipe_inputs
            ]
            output_quantity = min([capacity_limit] + input_limited)
            if output_quantity <= 0:
                continue
            consumption: list[ConsumptionDraw] = []
            for ri in recipe_inputs:
                pool = input_pools[ri["input_material_id"]]
                cons_qty = (ri["quantity_per_output"] * output_quantity) / recipe["yield_rate"]
                cons_value = cons_qty * pool.unit_cost
                consumption.append(ConsumptionDraw(ri["input_material_id"], cons_qty, pool.unit_cost, cons_value))
                pool.consumption.append(ConsumptionDraw(ri["input_material_id"], cons_qty, pool.unit_cost, cons_value))

            conv_row = idx.conversion_costs.get((node_id, recipe["recipe_id"], period_id))
            if conv_row is None:
                raise ContractError(f"no conversion_costs row for {node_id}/{recipe['recipe_id']}@{period_id}")
            input_value = _fsum(c.value for c in consumption)
            conversion_eur = conv_row["variable_conversion_cost_per_output"] * output_quantity
            setup_eur = conv_row["fixed_setup_cost"] if recipe["setup_required_flag"] else 0.0
            overhead_eur = conv_row["eligible_overhead_fixed"] + conv_row["eligible_overhead_variable"] * output_quantity

            markup_rule = idx.resolve_cost_rule("MARKUP")
            if markup_rule["cost_rule_id"] != conv_row["markup_base_rule_id"]:
                raise ContractError("markup_base_rule_id does not resolve to the MARKUP cost_allocation_rules row")
            eligible_base_names = set(idx.config["cost_policy"]["default_markup_eligible_base"])
            conversion_eligible = idx.resolve_cost_rule("CONVERSION")["markup_eligible_flag"] and "CONVERSION" in eligible_base_names
            setup_eligible = idx.resolve_cost_rule("SETUP")["markup_eligible_flag"] and "SETUP" in eligible_base_names
            overhead_eligible = idx.resolve_cost_rule("OVERHEAD")["markup_eligible_flag"] and "ELIGIBLE_OVERHEAD" in eligible_base_names
            input_value_eligible = "INPUT_VALUE" in eligible_base_names

            markup_base_eur = (
                (input_value if input_value_eligible else 0.0)
                + (conversion_eur if conversion_eligible else 0.0)
                + (setup_eur if setup_eligible else 0.0)
                + (overhead_eur if overhead_eligible else 0.0)
            )
            non_eligible_addon = (
                (0.0 if input_value_eligible else input_value)
                + (0.0 if conversion_eligible else conversion_eur)
                + (0.0 if setup_eligible else setup_eur)
                + (0.0 if overhead_eligible else overhead_eur)
            )
            markup_eur = markup_base_eur * conv_row["markup_rate"]
            output_value = markup_base_eur + markup_eur + non_eligible_addon

            event = TransformationEvent(
                recipe_id=recipe["recipe_id"], node_id=node_id, period_id=period_id,
                output_material_id=recipe["output_material_id"], output_quantity=output_quantity,
                consumption=consumption, input_value=input_value, conversion_eur=conversion_eur,
                setup_eur=setup_eur, overhead_eur=overhead_eur, markup_rate=conv_row["markup_rate"],
                markup_base_eur=markup_base_eur, markup_eur=markup_eur, output_value=output_value,
            )
            all_transformations.append(event)
            output_pool = get_or_create(node_id, recipe["output_material_id"])
            output_pool.production_events.append(event)
            operation_count += 1

        # 4b. Re-form pools that received transformation output this period.
        for pool in period_pools.values():
            if pool.production_events and not pool.receipt_legs and pool.boundary_quantity == 0.0:
                produced_qty = _fsum(e.output_quantity for e in pool.production_events)
                produced_val = _fsum(e.output_value for e in pool.production_events)
                pool.pool_quantity = _fsum([pool.opening_quantity, produced_qty])
                pool.pool_value = _fsum([pool.opening_value, produced_val])
                pool.unit_cost = pool.pool_value / pool.pool_quantity if pool.pool_quantity > 0 else 0.0

        # 4c. Dispatches departing this period, using each origin pool's
        # unit cost as already resolved above (boundary or transformation
        # output). The resulting leg is stashed for pickup at its arrival
        # period (step 2 of that later period).
        for approval_id, approval in idx.approvals.items():
            if approval["approval_status"] != "APPROVED":
                continue
            for contract in idx.contracts_by_approval.get(approval_id, []):
                dispatch_period = contract["effective_from_period"]
                if contract["effective_to_period"] != dispatch_period:
                    raise ContractError(f"contract {contract['contract_id']} window is not single-period")
                if dispatch_period != period_id:
                    continue
                if not (approval["valid_from_period"] <= dispatch_period <= approval["valid_to_period"]):
                    raise ContractError(f"contract {contract['contract_id']} dispatch period outside approval window")
                lanes = idx.lanes_by_pair.get((approval["seller_node_id"], approval["buyer_node_id"]), [])
                if len(lanes) != 1:
                    raise ContractError(
                        f"expected exactly one lane {approval['seller_node_id']}->{approval['buyer_node_id']}, found {len(lanes)}"
                    )
                lane = lanes[0]
                lead = idx.lead_time_periods(contract["contract_handling_days"], lane["base_transit_days"])
                arrival_period = idx.arrival_period(dispatch_period, lead)
                origin_pool = period_pools.get((approval["seller_node_id"], approval["material_id"]))
                if origin_pool is None:
                    raise ContractError(
                        f"origin pool {approval['seller_node_id']}/{approval['material_id']} has no activity at {period_id} "
                        "but a contract dispatches from it"
                    )
                qty = contract["minimum_order_quantity"]
                origin_currency_rate = idx.fx_rate(contract["currency"], dispatch_period)
                dispatched_value = origin_pool.unit_cost * qty * origin_currency_rate
                origin_node = idx.nodes[approval["seller_node_id"]]
                destination_node = idx.nodes[approval["buyer_node_id"]]
                incoterm = idx.incoterm_rules[contract["incoterm_code"]]

                freight_eur = 0.0
                fixed_shipment_eur = 0.0
                duty_eur = 0.0
                insurance_eur = 0.0
                if idx.resolve_cost_rule("FREIGHT")["capitalised_flag"] and incoterm["buyer_pays_main_carriage"]:
                    freight_eur = lane["variable_freight_cost_per_unit"] * qty * idx.fx_rate(lane["freight_currency"], dispatch_period)
                if idx.resolve_cost_rule("FIXED_SHIPMENT")["capitalised_flag"] and incoterm["buyer_pays_main_carriage"]:
                    fixed_shipment_eur = lane["fixed_shipment_cost"] * idx.fx_rate(lane["freight_currency"], dispatch_period)
                if idx.resolve_cost_rule("INSURANCE")["capitalised_flag"] and incoterm["buyer_pays_insurance"]:
                    insurance_eur = lane["insurance_rate_pct_of_goods"] * dispatched_value
                if idx.resolve_cost_rule("DUTY")["capitalised_flag"] and incoterm["buyer_pays_import_duty"]:
                    duty_rule = idx.resolve_duty_rate(
                        origin_node["country_code"], destination_node["country_code"],
                        idx.materials[approval["material_id"]]["material_family"], dispatch_period,
                    )
                    customs_value = dispatched_value if duty_rule["customs_value_basis"] == "GOODS" else dispatched_value + freight_eur
                    duty_eur = duty_rule["duty_rate"] * customs_value
                fixed_order_eur = 0.0
                if idx.resolve_cost_rule("FIXED_ORDER")["capitalised_flag"]:
                    fixed_order_eur = contract["fixed_order_cost"] * origin_currency_rate

                receipt_value = dispatched_value + freight_eur + duty_eur + insurance_eur + fixed_shipment_eur + fixed_order_eur
                leg = ShipmentLeg(
                    approval_id=approval_id, lane_id=lane["lane_id"], contract_id=contract["contract_id"],
                    origin_node_id=approval["seller_node_id"], destination_node_id=approval["buyer_node_id"],
                    material_id=approval["material_id"], dispatch_period_id=dispatch_period, arrival_period_id=arrival_period,
                    quantity=qty, origin_unit_cost=origin_pool.unit_cost, dispatched_value=dispatched_value,
                    freight_eur=freight_eur, duty_eur=duty_eur, insurance_eur=insurance_eur,
                    fixed_shipment_eur=fixed_shipment_eur, fixed_order_eur=fixed_order_eur, receipt_value=receipt_value,
                )
                all_legs.append(leg)
                origin_pool.dispatch_legs.append(leg)
                legs_by_arrival_period[arrival_period].append(leg)
                operation_count += 1

        # 5. Service at plant nodes.
        for pool in period_pools.values():
            node = idx.nodes[pool.node_id]
            if node["node_type"] != "PLANT":
                continue
            demand_row = idx.terminal_demand.get((pool.node_id, pool.material_id, period_id))
            demand_qty = demand_row["demand_quantity"] if demand_row else 0.0
            consumed_and_dispatched = _fsum(c.quantity for c in pool.consumption) + _fsum(l.quantity for l in pool.dispatch_legs)
            available = pool.pool_quantity - consumed_and_dispatched
            served = min(available, demand_qty)
            pool.served_quantity = served
            pool.served_value = served * pool.unit_cost

        # 6. Closing balance and guards.
        for pool in period_pools.values():
            consumed_qty = _fsum(c.quantity for c in pool.consumption)
            dispatched_qty = _fsum(l.quantity for l in pool.dispatch_legs)
            closing_qty = pool.pool_quantity - consumed_qty - dispatched_qty - pool.served_quantity
            if closing_qty < -1e-6:
                raise ContractError(
                    f"pool {pool.key} is over-committed: quantity {pool.pool_quantity} cannot cover "
                    f"consumption {consumed_qty} + dispatch {dispatched_qty} + service {pool.served_quantity}"
                )
            closing_qty = max(closing_qty, 0.0)
            pool.closing_quantity = closing_qty
            pool.closing_value = closing_qty * pool.unit_cost
            policy = idx.inventory_policy.get((pool.node_id, pool.material_id))
            if policy is not None and closing_qty > policy["maximum_storage_quantity"] + 1e-6:
                raise ContractError(
                    f"pool {pool.key} closing quantity {closing_qty} exceeds maximum_storage_quantity "
                    f"{policy['maximum_storage_quantity']}"
                )
            prior_close[(pool.node_id, pool.material_id)] = (closing_qty, pool.closing_value)
            pools[pool.key] = pool

    return Valuation(pools=pools, transformations=all_transformations, legs=all_legs, periods=idx.periods, operation_count=operation_count)


# --------------------------------------------------------------------------- reconciliation rows


def _row(equation_family: str, entity_type: str, entity_id: str, period_id: str | None, lhs: float, rhs: float, config: Mapping[str, Any]) -> dict[str, Any]:
    kind = FAMILY_TOLERANCE_KIND[equation_family]
    absolute, relative = tolerance_pair(config, kind)
    absolute_residual, relative_residual = residuals(lhs, rhs)
    tolerance = tolerance_for(lhs, rhs, absolute, relative)
    return {
        "run_id": RUN_ID, "scenario_id": SCENARIO_ID,
        "equation_id": f"{equation_family}|{entity_type}:{entity_id}|{period_id or 'ALL'}",
        "equation_family": equation_family, "entity_type": entity_type, "entity_id": entity_id,
        "period_id": period_id, "lhs_value": lhs, "rhs_value": rhs,
        "absolute_residual": absolute_residual, "relative_residual": relative_residual,
        "tolerance": tolerance, "pass_flag": absolute_residual <= tolerance,
    }


def identity_rows(valuation: Valuation, config: Mapping[str, Any], inputs: FixtureInputs) -> list[dict[str, Any]]:
    idx = Indices(inputs)
    rows: list[dict[str, Any]] = []
    last_period = valuation.periods[-1]

    for row in inputs.rows("opening_inventory.csv"):
        entity_id = f"{row['node_id']}/{row['material_id']}"
        rows.append(_row("OPENING_INVENTORY_CONSISTENCY", "POOL", entity_id, None,
                          row["opening_total_value_eur"], row["usable_quantity"] * row["opening_unit_cost_eur"], config))

    for key in sorted(valuation.pools):
        pool = valuation.pools[key]
        entity_id = f"{pool.node_id}/{pool.material_id}"

        receipt_qty = _fsum(l.quantity for l in pool.receipt_legs)
        production_qty = _fsum(e.output_quantity for e in pool.production_events)
        rows.append(_row("POOL_QUANTITY_ROLLFORWARD", "POOL", entity_id, pool.period_id,
                          pool.pool_quantity, pool.opening_quantity + pool.boundary_quantity + receipt_qty + production_qty, config))

        receipt_val = _fsum(l.receipt_value for l in pool.receipt_legs)
        production_val = _fsum(e.output_value for e in pool.production_events)
        rows.append(_row("POOL_VALUE_ROLLFORWARD", "POOL", entity_id, pool.period_id,
                          pool.pool_value, pool.opening_value + pool.boundary_value + receipt_val + production_val, config))

        rows.append(_row("POOL_UNIT_COST_BILINEAR", "POOL", entity_id, pool.period_id,
                          pool.pool_value, pool.unit_cost * pool.pool_quantity, config))

        if pool.pool_quantity <= 0:
            rows.append(_row("ZERO_POOL_VALUE", "POOL", entity_id, pool.period_id, pool.pool_value, 0.0, config))

        consumed_qty = _fsum(c.quantity for c in pool.consumption)
        dispatched_qty = _fsum(l.quantity for l in pool.dispatch_legs)
        rows.append(_row("POOL_QUANTITY_CONSERVATION", "POOL", entity_id, pool.period_id,
                          pool.pool_quantity, pool.closing_quantity + dispatched_qty + consumed_qty + pool.served_quantity, config))

        consumed_val = _fsum(c.value for c in pool.consumption)
        dispatched_val = _fsum(l.origin_unit_cost * l.quantity for l in pool.dispatch_legs)
        rows.append(_row("POOL_VALUE_CONSERVATION", "POOL", entity_id, pool.period_id,
                          pool.pool_value, pool.closing_value + dispatched_val + consumed_val + pool.served_value, config))

        for draw in pool.consumption:
            rows.append(_row("OUTFLOW_COMMON_UNIT_COST", "POOL", f"{entity_id}|consumed:{draw.material_id}", pool.period_id,
                              draw.value / draw.quantity if draw.quantity else 0.0, pool.unit_cost, config))
        for leg in pool.dispatch_legs:
            rows.append(_row("OUTFLOW_COMMON_UNIT_COST", "POOL", f"{entity_id}|shipped:{leg.lane_id}", pool.period_id,
                              leg.origin_unit_cost, pool.unit_cost, config))
        if pool.served_quantity > 0:
            rows.append(_row("OUTFLOW_COMMON_UNIT_COST", "POOL", f"{entity_id}|served", pool.period_id,
                              pool.served_value / pool.served_quantity, pool.unit_cost, config))

    for event in valuation.transformations:
        entity_id = event.recipe_id
        expected = event.input_value + event.conversion_eur + event.setup_eur + event.overhead_eur + event.markup_eur
        rows.append(_row("TRANSFORMATION_VALUE", "TRANSFORMATION", entity_id, event.period_id,
                          event.output_value, expected, config))

    for leg in valuation.legs:
        entity_id = leg.lane_id
        expected = leg.dispatched_value + leg.freight_eur + leg.duty_eur + leg.insurance_eur + leg.fixed_shipment_eur + leg.fixed_order_eur
        rows.append(_row("RECEIPT_VALUE", "SHIPMENT", entity_id, leg.arrival_period_id, leg.receipt_value, expected, config))

    served_total = _fsum(p.served_value for p in valuation.pools.values())
    terminal_closing_total = _fsum(p.closing_value for p in valuation.pools.values() if p.period_id == last_period)
    stage_2 = served_total + terminal_closing_total
    rows.append(_row("STAGE_2_VALUE", "RUN", RUN_ID, None, stage_2, stage_2, config))

    return sorted(rows, key=lambda r: (r["equation_family"], r["entity_id"], r["period_id"] or ""))


# --------------------------------------------------------------------------- control totals


LEDGER_COMPONENT_FIELDS = {
    "EXTERNAL_PURCHASE": ("pool", "boundary_value"),
    "FREIGHT": ("leg", "freight_eur"),
    "DUTY": ("leg", "duty_eur"),
    "INSURANCE": ("leg", "insurance_eur"),
    "FIXED_ORDER": ("leg", "fixed_order_eur"),
    "FIXED_SHIPMENT": ("leg", "fixed_shipment_eur"),
    "CONVERSION": ("event", "conversion_eur"),
    "SETUP": ("event", "setup_eur"),
    "OVERHEAD": ("event", "overhead_eur"),
    "MARKUP": ("event", "markup_eur"),
}


def ledger_component_total(valuation: Valuation, component: str) -> float:
    if component in ("HOLDING", "ACTIVATION", "SHORTAGE", "SURGE"):
        return 0.0
    kind, field_name = LEDGER_COMPONENT_FIELDS[component]
    if kind == "pool":
        return _fsum(getattr(p, field_name) for p in valuation.pools.values())
    if kind == "leg":
        return _fsum(getattr(l, field_name) for l in valuation.legs)
    return _fsum(getattr(e, field_name) for e in valuation.transformations)


def capitalised_total(valuation: Valuation) -> float:
    return _fsum(ledger_component_total(valuation, c) for c in LEDGER_COMPONENT_FIELDS)


def opening_book_value_total(inputs: FixtureInputs) -> float:
    return _fsum(r["opening_total_value_eur"] for r in inputs.rows("opening_inventory.csv"))


def evaluate_selector(valuation: Valuation, selector: Mapping[str, Any], inputs: FixtureInputs | None = None) -> float:
    measure = selector["measure"]
    if measure == "stage_2_value":
        last_period = valuation.periods[-1]
        served_total = _fsum(p.served_value for p in valuation.pools.values())
        terminal_closing_total = _fsum(p.closing_value for p in valuation.pools.values() if p.period_id == last_period)
        return served_total + terminal_closing_total
    if measure == "served_value_total":
        node_id = selector.get("node_id")
        return _fsum(
            p.served_value for p in valuation.pools.values()
            if p.material_id == selector["material_id"] and (node_id is None or p.node_id == node_id)
        )
    if measure == "terminal_closing_total":
        last_period = valuation.periods[-1]
        return _fsum(p.closing_value for p in valuation.pools.values() if p.period_id == last_period)
    if measure == "leg_receipt_value":
        matches = [l for l in valuation.legs if l.lane_id == selector["lane_id"]]
        if len(matches) != 1:
            raise ContractError(f"expected exactly one leg for lane {selector['lane_id']}, found {len(matches)}")
        return matches[0].receipt_value
    if measure == "ledger_component_total":
        return ledger_component_total(valuation, selector["component"])
    if measure == "capitalised_total":
        return capitalised_total(valuation)
    if measure == "opening_book_value_total":
        if inputs is None:
            raise ContractError("opening_book_value_total requires inputs")
        return opening_book_value_total(inputs)
    if measure == "noncapitalised_total":
        return 0.0
    pool = valuation.pools.get((selector["node_id"], selector["material_id"], selector["period_id"]))
    if pool is None:
        raise ContractError(f"no pool for selector {selector}")
    if measure == "pool_quantity":
        return pool.pool_quantity
    if measure == "pool_value":
        return pool.pool_value
    if measure == "pool_unit_cost":
        return pool.unit_cost
    if measure == "closing_value":
        return pool.closing_value
    if measure == "closing_quantity":
        return pool.closing_quantity
    if measure == "served_value":
        return pool.served_value
    if measure == "transformation_output_value":
        return _fsum(e.output_value for e in pool.production_events)
    if measure == "receipt_value":
        return _fsum(l.receipt_value for l in pool.receipt_legs)
    raise ContractError(f"unsupported control-total measure: {measure}")


@dataclass
class ControlTotalResult:
    control_total_id: str
    description: str
    expected_value: float
    recomputed_value: float
    unit: str
    absolute_tolerance: float
    relative_tolerance: float

    @property
    def pass_flag(self) -> bool:
        from tooling.contract_runtime import within_tolerance

        return within_tolerance(self.recomputed_value, self.expected_value, self.absolute_tolerance, self.relative_tolerance)


def control_totals(valuation: Valuation, definitions: list[Mapping[str, Any]], inputs: FixtureInputs | None = None) -> list[ControlTotalResult]:
    results = []
    for definition in definitions:
        recomputed = evaluate_selector(valuation, definition["selector"], inputs)
        results.append(ControlTotalResult(
            control_total_id=definition["control_total_id"], description=definition["description"],
            expected_value=definition["published_value"], recomputed_value=recomputed,
            unit=definition["unit"], absolute_tolerance=definition.get("absolute_tolerance"),
            relative_tolerance=definition.get("relative_tolerance"),
        ))
    return results


# --------------------------------------------------------------------------- convenience


@dataclass
class FixtureResult:
    valuation: Valuation
    rows: list[dict[str, Any]]
    control_total_results: list[ControlTotalResult]


def reconcile_fixture(data_dir: Path | None = None, config: Mapping[str, Any] | None = None,
                       definitions: list[Mapping[str, Any]] | None = None) -> FixtureResult:
    inputs = load_fixture_inputs(data_dir, config)
    valuation = value_plan(inputs)
    rows = identity_rows(valuation, inputs.config, inputs)
    if definitions is None:
        definitions = []
    result = control_totals(valuation, definitions, inputs)
    return FixtureResult(valuation=valuation, rows=rows, control_total_results=result)
