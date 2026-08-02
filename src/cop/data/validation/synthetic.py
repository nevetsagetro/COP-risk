"""Minimum schema, temporal, leakage, and relational validations."""

from __future__ import annotations

from typing import Any

import pandas as pd

from cop.data.schemas.synthetic import (
    APPLICATION_COLUMNS,
    AUDIT_ONLY_COLUMNS,
    FEATURE_AVAILABILITY,
    FEATURE_DEPENDENCIES,
    INPUT_FEATURE_COLUMNS,
    LEDGER_COLUMNS,
)
from cop.data.synthetic.config import SyntheticConfig
from cop.data.synthetic.generator import GeneratedTables


class ValidationError(ValueError):
    """Raised when a generated snapshot violates its contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _same_nullable_values(left: pd.Series[Any], right: pd.Series[Any]) -> bool:
    return bool(((left == right) | (left.isna() & right.isna())).all())


def validate_snapshot(tables: GeneratedTables, config: SyntheticConfig) -> None:
    """Validate generated tables before serialization."""
    applications = tables.applications
    ledger = tables.ledger
    audit = tables.audit_only

    _require(
        tuple(applications.columns) == APPLICATION_COLUMNS,
        "applications schema does not match v1",
    )
    _require(tuple(ledger.columns) == LEDGER_COLUMNS, "ledger schema mismatch")
    _require(tuple(audit.columns) == AUDIT_ONLY_COLUMNS, "audit_only schema mismatch")
    _require(len(applications) == config.applications, "application count mismatch")
    _require(
        applications["borrower_id"].nunique() == config.borrowers,
        "borrower count mismatch",
    )
    borrower_counts = applications["borrower_id"].value_counts()
    repeated_fraction = float((borrower_counts > 1).sum() / config.borrowers)
    _require(
        repeated_fraction == config.repeated_borrowers_fraction,
        "repeated borrower fraction mismatch",
    )
    _require(applications["application_id"].is_unique, "application IDs not unique")
    _require(applications["borrower_id"].notna().all(), "borrower_id contains null")
    _require(not applications.duplicated().any(), "duplicate application rows")
    _require(not ledger.duplicated().any(), "duplicate ledger rows")
    _require(
        not ledger.duplicated(["application_id", "installment_number"]).any(),
        "duplicate ledger natural keys",
    )
    recomputed_dpd = (
        ledger["event_at"].dt.normalize() - ledger["due_at"].dt.normalize()
    ).dt.days.clip(lower=0)
    _require(
        recomputed_dpd.equals(ledger["days_past_due"].astype("int64")),
        "days_past_due is inconsistent with ledger timestamps",
    )
    delinquent = ledger["days_past_due"] > 0
    _require(
        (
            ledger.loc[delinquent, "paid_amount"]
            < ledger.loc[delinquent, "scheduled_amount"]
        ).all(),
        "delinquent ledger event is fully paid",
    )
    _require(
        (
            ledger.loc[~delinquent, "paid_amount"]
            == ledger.loc[~delinquent, "scheduled_amount"]
        ).all(),
        "current ledger event has inconsistent payment",
    )

    start = pd.Timestamp(config.decision_start)
    end = pd.Timestamp(config.decision_end)
    _require(
        (
            (applications["decision_timestamp"] >= start)
            & (applications["decision_timestamp"] < end)
        ).all(),
        "decision timestamp outside configured semi-open range",
    )
    for column in (
        "decision_timestamp",
        "application_available_at",
        "income_available_at",
        "bureau_available_at",
        "horizon_end",
        "followup_end",
        "outcome_timestamp",
        "label_observed_at",
        "label_ready_at",
        "label_available_at",
    ):
        _require(
            isinstance(applications[column].dtype, pd.DatetimeTZDtype),
            f"{column} must be timezone-aware",
        )

    for feature in INPUT_FEATURE_COLUMNS:
        availability = FEATURE_AVAILABILITY[feature]
        _require(
            (applications[availability] <= applications["decision_timestamp"]).all(),
            f"{feature} is unavailable at decision time",
        )
    for feature, dependencies in FEATURE_DEPENDENCIES.items():
        feature_available = applications[FEATURE_AVAILABILITY[feature]]
        for dependency in dependencies:
            dependency_available = applications[FEATURE_AVAILABILITY[dependency]]
            _require(
                (feature_available >= dependency_available).all(),
                f"{feature} is declared available before dependency {dependency}",
            )

    _require(
        applications["label_available_at"].equals(applications["label_ready_at"]),
        "label_available_at must alias label_ready_at",
    )
    observed = applications["label_observed_at"].notna()
    _require(
        (
            applications.loc[observed, "label_observed_at"]
            <= applications.loc[observed, "label_ready_at"]
        ).all(),
        "label observed after ready timestamp",
    )
    _require(
        applications.loc[
            applications["label_status"].isin(["immature", "censored"]),
            "default_within_horizon",
        ]
        .isna()
        .all(),
        "unknown labels were converted to negatives",
    )
    censored = applications["label_status"] == "censored"
    _require(
        applications.loc[censored, ["label_ready_at", "label_available_at"]]
        .isna()
        .all()
        .all(),
        "censored label has a readiness timestamp",
    )
    known = applications["default_within_horizon"].notna()
    cutoff = pd.Timestamp(config.snapshot_as_of)
    _require(
        (applications.loc[known, "label_ready_at"] <= cutoff).all(),
        "known label precedes its availability",
    )
    _require(
        applications.loc[
            applications["label_status"] == "mature", "default_within_horizon"
        ]
        .notna()
        .all(),
        "mature label is null",
    )
    _require(
        (
            applications.loc[applications["label_status"] == "censored", "followup_end"]
            < applications.loc[
                applications["label_status"] == "censored", "horizon_end"
            ]
        ).all(),
        "censored rows have complete follow-up",
    )

    application_ids = set(applications["application_id"])
    _require(
        set(ledger["application_id"]).issubset(application_ids),
        "orphan ledger rows",
    )
    _require(
        (ledger["event_available_at"] <= cutoff).all(),
        "ledger reveals events after snapshot_as_of",
    )
    ledger_with_followup = ledger.merge(
        applications[["application_id", "label_status", "followup_end"]],
        on="application_id",
        validate="many_to_one",
    )
    censored_ledger = ledger_with_followup["label_status"] == "censored"
    _require(
        (
            ledger_with_followup.loc[censored_ledger, "event_available_at"]
            <= ledger_with_followup.loc[censored_ledger, "followup_end"]
        ).all(),
        "ledger reveals events after censoring",
    )
    _require(
        set(audit["application_id"]) == application_ids,
        "audit_only does not map one row per application",
    )
    _require(
        not set(INPUT_FEATURE_COLUMNS).intersection(audit.columns),
        "audit_only attribute leaked into inputs",
    )

    qualifying = ledger.loc[
        ledger["days_past_due"] >= config.default_dpd_threshold
    ].merge(
        applications[["application_id", "decision_timestamp", "horizon_end"]],
        on="application_id",
        how="inner",
    )
    qualifying = qualifying.loc[
        (qualifying["event_at"] > qualifying["decision_timestamp"])
        & (qualifying["event_at"] <= qualifying["horizon_end"])
    ]
    expected_horizon = pd.Series(
        pd.DatetimeIndex(applications["decision_timestamp"])
        + pd.DateOffset(months=config.horizon_months),
        index=applications.index,
    )
    _require(
        _same_nullable_values(applications["horizon_end"], expected_horizon),
        "horizon_end is not derived from decision timestamp",
    )
    expected_censored = applications["followup_end"] < expected_horizon
    _require(
        (
            applications.loc[~expected_censored, "followup_end"]
            == expected_horizon.loc[~expected_censored]
        ).all(),
        "non-censored followup_end differs from horizon",
    )
    _require(
        (
            applications.loc[expected_censored, "followup_end"]
            > applications.loc[expected_censored, "decision_timestamp"]
        ).all(),
        "censored followup_end is not after decision",
    )
    first = qualifying.groupby("application_id", sort=False).agg(
        expected_outcome=("event_at", "min"),
        expected_positive_observed=("event_available_at", "min"),
    )
    expected_outcome = pd.Series(
        pd.to_datetime(
            applications["application_id"].map(first["expected_outcome"]), utc=True
        ),
        index=applications.index,
    )
    expected_positive_observed = pd.Series(
        pd.to_datetime(
            applications["application_id"].map(first["expected_positive_observed"]),
            utc=True,
        ),
        index=applications.index,
    )
    _require(
        _same_nullable_values(applications["outcome_timestamp"], expected_outcome),
        "outcome_timestamp is not the first qualifying ledger event",
    )
    nominal_ready = expected_horizon + pd.Timedelta(days=config.reporting_lag_days)
    expected_ready = pd.Series(
        pd.to_datetime(nominal_ready.mask(expected_censored), utc=True),
        index=applications.index,
    )
    _require(
        _same_nullable_values(applications["label_ready_at"], expected_ready),
        "label_ready_at is not derived from horizon and reporting lag",
    )
    _require(
        _same_nullable_values(applications["label_available_at"], expected_ready),
        "label_available_at is not derived from label readiness",
    )
    expected_observed = pd.Series(
        pd.to_datetime(
            expected_positive_observed.where(expected_outcome.notna(), nominal_ready),
            utc=True,
        ),
        index=applications.index,
    )
    expected_observed = expected_observed.mask(
        (expected_observed > cutoff) | expected_censored
    )
    _require(
        _same_nullable_values(applications["label_observed_at"], expected_observed),
        "label_observed_at is not derived from ledger and readiness",
    )
    expected_mature = ~expected_censored & (nominal_ready <= cutoff)
    expected_status = pd.Series("immature", index=applications.index, dtype="string")
    expected_status.loc[expected_mature] = "mature"
    expected_status.loc[expected_censored] = "censored"
    _require(
        applications["label_status"].equals(expected_status),
        "label_status is not derived from cutoff and censoring",
    )
    expected_reason = pd.Series(pd.NA, index=applications.index, dtype="string")
    expected_reason.loc[expected_censored] = "administrative_loss"
    _require(
        applications["censoring_reason"].equals(expected_reason),
        "censoring_reason is inconsistent with follow-up",
    )
    derived_positive = set(qualifying["application_id"])
    mature = applications.loc[applications["label_status"] == "mature"]
    expected = mature["application_id"].isin(derived_positive)
    actual = mature["default_within_horizon"].astype(bool)
    _require(
        actual.reset_index(drop=True).equals(expected.reset_index(drop=True)),
        "target is not derived from ledger",
    )
    positive = applications["default_within_horizon"] == True  # noqa: E712
    _require(
        applications.loc[positive.fillna(False), "outcome_timestamp"].notna().all(),
        "positive label lacks outcome timestamp",
    )
    negative = applications["default_within_horizon"] == False  # noqa: E712
    _require(
        applications.loc[negative.fillna(False), "outcome_timestamp"].isna().all(),
        "negative label has outcome timestamp",
    )
