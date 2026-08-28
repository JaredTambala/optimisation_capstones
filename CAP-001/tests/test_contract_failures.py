from __future__ import annotations

import csv
from pathlib import Path

import pytest

from tooling.contract_runtime import ContractError, load_config, validate_csv_file


def test_csv_header_drift_is_rejected(tmp_path: Path) -> None:
    config = load_config()
    contract = config["raw_contracts"]["planning_calendar.csv"]
    target = tmp_path / "planning_calendar.csv"
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([field["name"] for field in contract["columns"]] + ["undeclared_column"])
    with pytest.raises(ContractError, match="header drifted"):
        validate_csv_file(target, contract)


def test_invalid_boolean_and_period_are_rejected(tmp_path: Path) -> None:
    config = load_config()
    contract = config["raw_contracts"]["planning_calendar.csv"]
    target = tmp_path / "planning_calendar.csv"
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([field["name"] for field in contract["columns"]])
        writer.writerow(["P13", 13, "2027-03-29", "2027-04-04", "2027-03-28T12:00:00Z", "yes"])
    with pytest.raises(ContractError):
        validate_csv_file(target, contract)


def test_missing_and_extra_raw_files_are_rejected(tmp_path: Path) -> None:
    from tooling.contract_runtime import validate_raw_data_directory

    config = load_config()
    (tmp_path / "unexpected.csv").write_text("x\n")
    with pytest.raises(ContractError, match="file set drifted"):
        validate_raw_data_directory(tmp_path, config)

