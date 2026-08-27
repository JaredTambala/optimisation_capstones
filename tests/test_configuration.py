from __future__ import annotations

from copy import deepcopy

import pytest

from tooling.contract_runtime import (
    ContractError,
    EXPECTED_OUTPUT_FILES,
    EXPECTED_RAW_FILES,
    load_config,
    minimal_json_object,
    minimal_value,
    validate_config,
    validate_record,
)


def test_frozen_configuration_and_contract_counts() -> None:
    config = load_config()
    assert config["configuration_version"] == "0.3.3"
    assert tuple(config["raw_contracts"]) == EXPECTED_RAW_FILES
    assert tuple(config["output_contracts"]) == EXPECTED_OUTPUT_FILES
    assert sum(len(contract["columns"]) for contract in config["raw_contracts"].values()) == 240
    assert sum(len(contract["fields"]) for contract in config["output_contracts"].values()) == 201
    assert len(config["miniature_fixture_contracts"]) == 2
    assert len(config["adr_register"]) == 12
    assert sum(item["points"] for item in config["assessment"]["rubric"]) == 100


def test_config_rejects_unsupported_top_level_field() -> None:
    config = deepcopy(load_config())
    config["silent_semantic_override"] = True
    with pytest.raises(ContractError, match="unsupported"):
        validate_config(config)


def test_config_rejects_field_name_drift() -> None:
    config = deepcopy(load_config())
    config["raw_contracts"]["network_nodes.csv"]["columns"][0]["name"] = "renamed_node_id"
    with pytest.raises(ContractError, match="field names or order drifted"):
        validate_config(config)


def test_all_raw_row_contracts_accept_their_minimal_typed_record() -> None:
    config = load_config()
    for name, contract in config["raw_contracts"].items():
        record = {field["name"]: minimal_value(field) for field in contract["columns"]}
        validate_record(record, contract["columns"], require_all_columns=True)


def test_raw_row_rejects_extra_column_and_wrong_constant() -> None:
    config = load_config()
    contract = config["raw_contracts"]["network_nodes.csv"]
    record = {field["name"]: minimal_value(field) for field in contract["columns"]}
    record["unexpected"] = "not permitted"
    with pytest.raises(ContractError, match="unsupported fields"):
        validate_record(record, contract["columns"], require_all_columns=True)

    record.pop("unexpected")
    record["pooling_policy"] = "FIFO"
    with pytest.raises(ContractError, match="must equal"):
        validate_record(record, contract["columns"], require_all_columns=True)


def test_synthetic_intermediate_cost_contract_is_absent() -> None:
    config = load_config()
    assert "baseline_standard_costs.csv" not in config["raw_contracts"]
    assert config["cost_policy"]["derived_intermediate_cost_inputs_prohibited"]


def test_json_output_contracts_accept_minimal_objects_and_reject_status_drift() -> None:
    config = load_config()
    for name, contract in config["output_contracts"].items():
        if contract["format"] == "json_object":
            validate_record(minimal_json_object(contract), contract["fields"], require_all_columns=False)

    metadata = config["output_contracts"]["run_metadata.json"]
    record = minimal_json_object(metadata)
    record["status"] = "optimal"
    with pytest.raises(ContractError, match="controlled domain"):
        validate_record(record, metadata["fields"], require_all_columns=False)
