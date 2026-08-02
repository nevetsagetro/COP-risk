from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from cop.data.synthetic.config import load_config
from cop.data.synthetic.generator import (
    GeneratedTables,
    _risk_probabilities,
    generate_tables,
)
from cop.data.validation.synthetic import ValidationError, validate_snapshot

FIXTURE = Path("tests/fixtures/synthetic-small.yaml")


def test_generated_tables_satisfy_contract() -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)

    validate_snapshot(tables, config)
    assert len(tables.applications) == 240
    assert tables.applications["borrower_id"].nunique() == 180
    borrower_counts = tables.applications["borrower_id"].value_counts()
    assert (borrower_counts > 1).sum() == round(180 * 0.15)
    assert set(tables.applications["label_status"]) == {"mature", "censored"}
    unknown = tables.applications["label_status"].isin(["immature", "censored"])
    assert tables.applications.loc[unknown, "default_within_horizon"].isna().all()
    censored = tables.applications["label_status"] == "censored"
    assert (
        tables.applications.loc[censored, ["label_ready_at", "label_available_at"]]
        .isna()
        .all()
        .all()
    )
    assert not set(tables.audit_only.columns).intersection(
        {"monthly_income", "debt_to_income", "default_within_horizon"}
    )


def test_target_tampering_is_detected() -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)
    applications = tables.applications.copy()
    mature_index = applications.index[applications["label_status"] == "mature"][0]
    current = bool(applications.at[mature_index, "default_within_horizon"])
    applications.at[mature_index, "default_within_horizon"] = not current
    tampered = GeneratedTables(applications, tables.ledger, tables.audit_only)

    with pytest.raises(ValidationError, match="derived from ledger"):
        validate_snapshot(tampered, config)


def test_immature_negative_is_detected() -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)
    applications = tables.applications.copy()
    immature_index = applications.index[applications["label_status"] == "mature"][0]
    applications.at[immature_index, "label_status"] = "immature"
    applications.at[immature_index, "default_within_horizon"] = False
    tampered = GeneratedTables(applications, tables.ledger, tables.audit_only)

    with pytest.raises(ValidationError, match="converted to negatives"):
        validate_snapshot(tampered, config)


def test_all_feature_availability_precedes_decision() -> None:
    tables = generate_tables(load_config(FIXTURE))
    availability = tables.applications[
        [
            "application_available_at",
            "income_available_at",
            "bureau_available_at",
        ]
    ]
    decision = tables.applications["decision_timestamp"]

    assert availability.le(decision, axis=0).all().all()
    assert isinstance(decision.dtype, pd.DatetimeTZDtype)


def test_future_rows_cannot_change_historical_risk_probabilities() -> None:
    config = load_config(FIXTURE)
    history = generate_tables(config).applications.iloc[:100]
    income = history["monthly_income"].to_numpy(dtype="float64")
    dti = history["debt_to_income"].to_numpy(dtype="float64")
    utilization = history["utilization_ratio"].to_numpy(dtype="float64")
    delinquencies = history["prior_delinquencies_count"].to_numpy(dtype="int64")
    baseline = _risk_probabilities(income, dti, utilization, delinquencies, config)

    future_income = pd.Series([1.0, 1_000_000.0]).to_numpy(dtype="float64")
    future_dti = pd.Series([0.0, 3.0]).to_numpy(dtype="float64")
    future_utilization = pd.Series([0.0, 1.0]).to_numpy(dtype="float64")
    future_delinquencies = pd.Series([0, 3]).to_numpy(dtype="int64")
    extended = _risk_probabilities(
        pd.concat([pd.Series(income), pd.Series(future_income)]).to_numpy(),
        pd.concat([pd.Series(dti), pd.Series(future_dti)]).to_numpy(),
        pd.concat([pd.Series(utilization), pd.Series(future_utilization)]).to_numpy(),
        pd.concat(
            [pd.Series(delinquencies), pd.Series(future_delinquencies)]
        ).to_numpy(),
        config,
    )

    assert (baseline == extended[: len(baseline)]).all()


def test_target_rate_is_reported_configuration_not_acceptance_gate() -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)

    validate_snapshot(tables, replace(config, target_positive_rate=0.99))


def test_advancing_future_cutoff_does_not_change_mature_historical_content() -> None:
    final_config = load_config(FIXTURE)
    earlier_config = replace(final_config, snapshot_as_of="2025-07-01T00:00:00Z")
    earlier = generate_tables(earlier_config)
    final = generate_tables(final_config)
    historical_ids = set(
        earlier.applications.loc[
            earlier.applications["label_status"] == "mature", "application_id"
        ]
    )

    earlier_applications = earlier.applications.loc[
        earlier.applications["application_id"].isin(historical_ids)
    ].reset_index(drop=True)
    final_applications = final.applications.loc[
        final.applications["application_id"].isin(historical_ids)
    ].reset_index(drop=True)
    assert earlier_applications.equals(final_applications)

    earlier_ledger = earlier.ledger.loc[
        earlier.ledger["application_id"].isin(historical_ids)
    ].reset_index(drop=True)
    final_ledger = final.ledger.loc[
        final.ledger["application_id"].isin(historical_ids)
    ].reset_index(drop=True)
    assert earlier_ledger.equals(final_ledger)


def test_duplicate_application_id_is_detected() -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)
    applications = tables.applications.copy()
    applications.at[1, "application_id"] = applications.at[0, "application_id"]
    tampered = GeneratedTables(applications, tables.ledger, tables.audit_only)

    with pytest.raises(ValidationError, match="IDs not unique"):
        validate_snapshot(tampered, config)


def test_ledger_dpd_tampering_is_detected() -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)
    ledger = tables.ledger.copy()
    ledger.at[0, "days_past_due"] = int(ledger.at[0, "days_past_due"]) + 1

    with pytest.raises(ValidationError, match="inconsistent with ledger timestamps"):
        validate_snapshot(
            GeneratedTables(tables.applications, ledger, tables.audit_only), config
        )


@pytest.mark.parametrize(
    ("field", "expected_message"),
    [
        ("horizon_end", "horizon_end"),
        ("followup_end", "followup_end"),
        ("outcome_timestamp", "outcome_timestamp"),
        ("label_observed_at", "label_observed_at"),
        ("label_ready_at", "label_ready_at"),
        ("label_available_at", "label_available_at"),
        ("label_status", "converted to negatives"),
    ],
)
def test_label_timeline_tampering_is_detected(
    field: str, expected_message: str
) -> None:
    config = load_config(FIXTURE)
    tables = generate_tables(config)
    applications = tables.applications.copy()
    positive_index = applications.index[
        applications["default_within_horizon"] == True  # noqa: E712
    ][0]
    if field == "label_status":
        applications.at[positive_index, field] = "immature"
    else:
        applications.at[positive_index, field] = applications.at[
            positive_index, field
        ] + pd.Timedelta(days=1)

    with pytest.raises(ValidationError, match=expected_message):
        validate_snapshot(
            GeneratedTables(applications, tables.ledger, tables.audit_only), config
        )
