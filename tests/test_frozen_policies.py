from __future__ import annotations

from tooling.contract_runtime import load_config


def test_business_network_and_time_policies_are_frozen() -> None:
    config = load_config()
    assert config["business"]["organisation_id"] == "asterion_industrial_controls"
    assert config["business"]["intended_user"] == "European supply-planning and category-management team"
    assert config["business"]["commercial_authority"] == "NOMINATED_SOURCE_OPEN_COST"
    assert config["business"]["base_currency"] == "EUR"
    assert [(plant["name"], plant["country_code"], plant["local_currency"], plant["primary_role"]) for plant in config["business"]["plants"]] == [
        ("Birmingham", "GB", "GBP", "Motor-control units and control cabinets"),
        ("Dortmund", "DE", "EUR", "Variable-speed drives and high-capacity control systems"),
        ("Katowice", "PL", "PLN", "Standard control units and monitoring devices"),
        ("Zaragoza", "ES", "EUR", "Remote monitoring units and regional configurations"),
    ]

    network = config["network"]
    assert network["schema"] == "TIER_N_DAG"
    assert network["tier_numbering"] == "PROXIMITY_TO_ASTERION"
    assert network["release_instance_supplier_tiers"] == 4
    assert network["generic_node_material_arc_recipe_sets_required"] is True
    assert network["external_prices_boundary_only"] is True

    planning = config["planning"]
    assert (planning["start_date"], planning["end_date"], planning["periods"]) == ("2027-01-04", "2027-03-28", 12)
    assert planning["lead_time_weeks_formula"] == "ceil((contract_handling_days + adjusted_transit_days) / 7)"
    assert planning["scenario_transit_multiplier_applied_before_week_conversion"] is True
    assert planning["receipts_available_in_arrival_period"] is True
    assert planning["production_available_in_production_period"] is True
    assert planning["same_period_conversion"] is True
    assert planning["include_work_in_progress"] is False
    assert planning["include_open_orders"] is False
    assert planning["include_in_transit"] is False
    assert planning["prohibit_post_horizon_arrivals"] is True


def test_model_pooling_objective_and_cost_policies_are_frozen() -> None:
    config = load_config()
    model = config["model"]
    assert model["assessed_class"] == "NONCONVEX_MINLP"
    assert model["baseline_class"] == "MILP"
    assert model["bounded_formulation_required"] is True
    assert model["baseline_uses_identical_physical_commercial_and_timing_controls"] is True
    assert model["baseline_standard_costs_comparator_only"] is True
    assert model["base_zero_shortage_design_required"] is True
    assert model["global_optimality_not_required_for_main_case"] is True
    assert [stage["name"] for stage in model["objective_stages"]] == [
        "WEIGHTED_SHORTAGE",
        "SERVED_AND_CLOSING_RECURSIVE_VALUE_PLUS_NONCAPITALISED_COST",
        "SURPLUS_AND_UNNECESSARY_ACTIVATION_TIEBREAK",
    ]
    assert model["include_moq"] is True
    assert model["include_order_multiples"] is True
    assert model["include_fixed_order_costs"] is True
    assert model["include_activation_decisions"] is True
    assert model["alternative_recipes_blend_unless_group_is_exclusive"] is True

    pooling = config["pooling_and_value"]
    assert config["network"]["pooling_policy"] == "WEIGHTED_AVERAGE"
    assert pooling["opening_book_value_in_pool"] is True
    assert pooling["common_unit_cost_for_all_outflows"] is True
    assert pooling["closing_inventory_retains_value_at_all_nodes"] is True
    assert pooling["zero_quantity_pool_has_zero_value"] is True
    assert pooling["finite_quantity_value_and_unit_cost_bounds_required"] is True
    assert pooling["physical_and_financial_reconciliation_required"] is True
    assert pooling["anti_dilution_controls_required"] is True

    costs = config["cost_policy"]
    assert costs["single_ledger_required"] is True
    assert costs["markup_applied_once"] is True
    assert costs["default_markup_eligible_base"] == ["INPUT_VALUE", "CONVERSION", "SETUP", "ELIGIBLE_OVERHEAD"]
    assert costs["direct_fixed_cost_capitalised_only_when_attributable_to_receiving_pool"] is True
    assert costs["shortage_is_stage_1_and_reported_separately_from_material_value"] is True
    assert costs["baseline_cost_prohibited_from_recursive_route"] is True


def test_scenario_solution_and_runtime_policies_are_frozen() -> None:
    config = load_config()
    rules = {item["scenario_id"]: item["frozen_rule"] for item in config["scenarios"]}
    assert "30% in P03-P05, 60% in P06" in rules["SCN-01"]
    assert "transit multiplier 1.75" in rules["SCN-02"]
    assert "unavailable in P04" in rules["SCN-03"]
    assert "20-40% capacity reduction" in rules["SCN-04"]
    assert "10-15% uplift" in rules["SCN-05"]
    assert config["scenario_semantics"]["base_immutable"] is True
    assert config["scenario_semantics"]["deterministic_derived_views"] is True
    assert config["scenario_semantics"]["explicit_recovery_rows"] is True
    assert config["scenario_semantics"]["availability_false_overrides_capacity_or_lane"] is True
    assert config["scenario_semantics"]["applicable_multipliers_compose_multiplicatively"] is True
    assert config["scenario_semantics"]["replacement_requires_declared_semantics"] is True
    assert config["scenario_semantics"]["highest_impact_priority_wins_and_ties_fail"] is True
    assert config["scenario_semantics"]["transformed_values_must_be_nonnegative_finite_and_plausible"] is True
    assert config["scenario_semantics"]["downstream_intermediate_cost_changes_through_recursive_propagation"] is True
    assert config["scenario_semantics"]["distinguish_baseline_plan_stress_from_scenario_reoptimisation"] is True
    assert config["scenario_semantics"]["run_modes"] == ["BASELINE_MILP", "RECURSIVE_MINLP", "STRESS_ONLY", "REOPTIMISE"]
    assert config["solution_statuses"] == ["globally_optimal", "locally_optimal", "feasible_time_limited", "best_found", "infeasible", "solver_failed"]
    assert config["runtime_budgets"]["miniature_fixture_seconds"] == 120
    assert config["runtime_budgets"]["baseline_per_scenario_seconds"] == 300
    assert config["runtime_budgets"]["recursive_base"] == {"maximum_starts": 3, "seconds_per_start": 1200, "retain_incumbent": True}
    assert config["runtime_budgets"]["recursive_scenario_reoptimisation_seconds"] == 900


def test_assessment_application_and_release_controls_are_frozen() -> None:
    config = load_config()
    assessment = config["assessment"]
    assert assessment["ai_assistance_expected"] is True
    assert assessment["deterministic_checks_precede_ai_scoring"] is True
    assert assessment["technical_defence_minutes"] == {"minimum": 20, "maximum": 30}
    assert len(assessment["application_views"]) == 11
    assert assessment["resilience_requirement"] == {
        "evaluate_all_supplied_scenarios": True,
        "student_defines_quantitative_measures": True,
        "at_least_one_intervention_required": True,
        "prescribed_concentration_formula": False,
        "report_cost_service_inventory_resilience_tradeoff": True,
    }
    assert len(assessment["required_deliverables"]) == 8
    assert sum(item["points"] for item in assessment["rubric"]) == 100

    release = config["release_controls"]
    assert all(release.values())
    assert len(config["controlled_open_decisions"]) == 11
