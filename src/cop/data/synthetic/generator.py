"""Causally ordered deterministic synthetic data generation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from cop.data.schemas.synthetic import (
    APPLICATION_COLUMNS,
    AUDIT_ONLY_COLUMNS,
)
from cop.data.synthetic.config import SyntheticConfig

RNG_NAMESPACES = (
    "repeated-borrowers",
    "application-order",
    "decision-calendar",
    "financial-features",
    "payment-behavior",
    "default-month",
    "censoring",
    "audit-only",
)
RNG_DERIVATION_ALGORITHM = "sha256-first-64-bits-v1"


@dataclass(frozen=True)
class GeneratedTables:
    applications: pd.DataFrame
    ledger: pd.DataFrame
    audit_only: pd.DataFrame


def _rng(seed: int, namespace: str) -> np.random.Generator:
    if namespace not in RNG_NAMESPACES:
        raise ValueError(f"unregistered RNG namespace: {namespace}")
    payload = f"cop-synthetic-v1:{seed}:{namespace}".encode()
    derived = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return np.random.default_rng(derived)


def _borrower_assignments(config: SyntheticConfig) -> NDArray[np.int64]:
    base = np.arange(config.borrowers, dtype=np.int64)
    repeated_count = round(config.borrowers * config.repeated_borrowers_fraction)
    entity_rng = _rng(config.seed, "repeated-borrowers")
    repeated = np.sort(entity_rng.choice(base, repeated_count, replace=False))
    extras_count = config.applications - config.borrowers
    extras = np.concatenate(
        [
            repeated,
            entity_rng.choice(repeated, extras_count - repeated_count, replace=True),
        ]
    )
    assignments = np.concatenate([base, extras])
    _rng(config.seed, "application-order").shuffle(assignments)
    return cast(NDArray[np.int64], assignments.astype(np.int64))


def _decision_timestamps(config: SyntheticConfig) -> pd.DatetimeIndex:
    start = pd.Timestamp(config.decision_start)
    end = pd.Timestamp(config.decision_end)
    days = (end - start).days
    offsets = _rng(config.seed, "decision-calendar").integers(
        0, days, size=config.applications
    )
    return pd.DatetimeIndex(start + pd.to_timedelta(offsets, unit="D"))


def _risk_probabilities(
    monthly_income: NDArray[np.float64],
    debt_to_income: NDArray[np.float64],
    utilization: NDArray[np.float64],
    delinquencies: NDArray[np.int64],
    config: SyntheticConfig,
) -> NDArray[np.float64]:
    """Apply the frozen v1 risk mechanism without fitting snapshot statistics."""
    income_z = (
        np.log(monthly_income) - config.risk_log_income_mean
    ) / config.risk_log_income_std
    score = (
        -0.35 * income_z
        + 1.15 * (debt_to_income - config.risk_debt_to_income_center)
        + 0.8 * (utilization - config.risk_utilization_center)
        + 0.35 * delinquencies
    )
    result = 1 / (1 + np.exp(-(config.risk_intercept + score)))
    return cast(NDArray[np.float64], result.astype(np.float64))


def _base_applications(
    config: SyntheticConfig,
) -> tuple[pd.DataFrame, NDArray[np.bool_]]:
    borrower_index = _borrower_assignments(config)
    decision = _decision_timestamps(config)
    n = config.applications

    finance = _rng(config.seed, "financial-features")
    monthly_income = np.round(finance.lognormal(np.log(3200), 0.48, n), 2)
    requested_amount = np.round(finance.lognormal(np.log(9000), 0.55, n), 2)
    requested_term = finance.choice(np.array([12, 24, 36]), n, p=[0.25, 0.45, 0.30])
    employment_tenure = finance.negative_binomial(3, 0.08, n).clip(0, 480)
    existing_debt = np.round(finance.gamma(2.0, 280.0, n), 2)
    open_lines = finance.negative_binomial(3, 0.42, n).clip(0, 30)
    credit_limit = np.round(finance.lognormal(np.log(10500), 0.5, n), 2)
    utilization = np.clip(finance.beta(2.1, 3.2, n), 0, 1)
    revolving_balance = np.round(credit_limit * utilization, 2)
    inquiries = finance.negative_binomial(1, 0.55, n).clip(0, 15)
    delinquencies = finance.binomial(3, 0.07, n)
    debt_to_income = cast(
        NDArray[np.float64],
        np.round(np.clip(existing_debt / monthly_income, 0, 3), 6).astype(np.float64),
    )

    probabilities = _risk_probabilities(
        monthly_income,
        debt_to_income,
        utilization,
        delinquencies,
        config,
    )
    default_flags = _rng(config.seed, "payment-behavior").random(n) < probabilities

    frame = pd.DataFrame(
        {
            "application_id": [f"app_{index:08d}" for index in range(n)],
            "borrower_id": [f"borrower_{index:08d}" for index in borrower_index],
            "decision_timestamp": decision,
            "application_available_at": decision - pd.Timedelta(days=1),
            "income_available_at": decision - pd.Timedelta(days=2),
            "bureau_available_at": decision - pd.Timedelta(days=3),
            "requested_amount": requested_amount,
            "requested_term_months": requested_term.astype("int16"),
            "monthly_income": monthly_income,
            "employment_tenure_months": employment_tenure.astype("int16"),
            "existing_monthly_debt": existing_debt,
            "open_credit_lines": open_lines.astype("int16"),
            "revolving_balance": revolving_balance,
            "credit_limit": credit_limit,
            "utilization_ratio": np.round(utilization, 6),
            "recent_inquiries_count": inquiries.astype("int16"),
            "prior_delinquencies_count": delinquencies.astype("int8"),
            "debt_to_income": debt_to_income,
        }
    )
    return frame, default_flags


def _censor_followup(
    decision: pd.Series[pd.Timestamp], censor_month: NDArray[np.int64]
) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        [
            timestamp + pd.DateOffset(months=int(month))
            for timestamp, month in zip(decision, censor_month, strict=True)
        ]
    )


def _generate_ledger(
    applications: pd.DataFrame,
    default_flags: NDArray[np.bool_],
    censored_flags: NDArray[np.bool_],
    censor_month: NDArray[np.int64],
    config: SyntheticConfig,
) -> pd.DataFrame:
    n = len(applications)
    default_month = _rng(config.seed, "default-month").integers(1, 10, n)
    installment = np.round(
        applications["requested_amount"].to_numpy()
        / applications["requested_term_months"].to_numpy(),
        2,
    )
    pieces: list[pd.DataFrame] = []
    for month in range(1, config.horizon_months + 1):
        included = ~censored_flags | (censor_month >= month)
        due_at = pd.DatetimeIndex(
            applications.loc[included, "decision_timestamp"]
        ) + pd.DateOffset(months=month)
        indices = np.flatnonzero(included)
        is_defaulted = default_flags[indices] & (default_month[indices] <= month)
        days_past_due = np.where(is_defaulted, config.default_dpd_threshold, 0)
        event_at = due_at + pd.to_timedelta(days_past_due, unit="D")
        paid = np.where(is_defaulted, 0.0, installment[indices])
        piece = pd.DataFrame(
            {
                "application_id": applications.loc[
                    included, "application_id"
                ].to_numpy(),
                "installment_number": np.full(len(indices), month, dtype="int16"),
                "due_at": due_at,
                "event_at": event_at,
                "event_available_at": event_at + pd.Timedelta(days=2),
                "scheduled_amount": installment[indices],
                "paid_amount": paid,
                "days_past_due": days_past_due.astype("int16"),
            }
        )
        pieces.append(piece)
    ledger = pd.concat(pieces, ignore_index=True)
    censor_limits = pd.DataFrame(
        {
            "application_id": applications["application_id"],
            "is_censored": censored_flags,
            "censor_followup": _censor_followup(
                applications["decision_timestamp"], censor_month
            ),
            "horizon_end": pd.DatetimeIndex(applications["decision_timestamp"])
            + pd.DateOffset(months=config.horizon_months),
        }
    )
    ledger = ledger.merge(censor_limits, on="application_id", validate="many_to_one")
    ledger = ledger.loc[
        ~ledger["is_censored"]
        | (ledger["event_available_at"] <= ledger["censor_followup"])
    ]
    ledger = ledger.loc[ledger["event_at"] <= ledger["horizon_end"]].drop(
        columns=["is_censored", "censor_followup", "horizon_end"]
    )
    cutoff = pd.Timestamp(config.snapshot_as_of)
    ledger = ledger.loc[ledger["event_available_at"] <= cutoff].copy()
    return ledger.sort_values(
        ["application_id", "installment_number"], kind="mergesort"
    ).reset_index(drop=True)


def _derive_labels(
    applications: pd.DataFrame,
    ledger: pd.DataFrame,
    censored_flags: NDArray[np.bool_],
    censor_month: NDArray[np.int64],
    config: SyntheticConfig,
) -> pd.DataFrame:
    result = applications.copy()
    decision = pd.DatetimeIndex(result["decision_timestamp"])
    horizon_end = decision + pd.DateOffset(months=config.horizon_months)
    result["horizon_end"] = horizon_end

    censor_followup = _censor_followup(result["decision_timestamp"], censor_month)
    result["followup_end"] = pd.Series(
        np.where(censored_flags, censor_followup, horizon_end),
        dtype="datetime64[ns, UTC]",
    )

    qualifying = ledger.loc[
        (ledger["days_past_due"] >= config.default_dpd_threshold)
    ].merge(
        result[["application_id", "decision_timestamp", "horizon_end"]],
        on="application_id",
        how="inner",
    )
    qualifying = qualifying.loc[
        (qualifying["event_at"] > qualifying["decision_timestamp"])
        & (qualifying["event_at"] <= qualifying["horizon_end"])
    ]
    first = qualifying.groupby("application_id", sort=False).agg(
        outcome_timestamp=("event_at", "min"),
        positive_observed_at=("event_available_at", "min"),
    )
    result = result.join(first, on="application_id")

    label_ready = horizon_end + pd.Timedelta(days=config.reporting_lag_days)
    result["label_ready_at"] = pd.Series(label_ready, dtype="datetime64[ns, UTC]")
    result["label_available_at"] = result["label_ready_at"]
    result["label_observed_at"] = result["positive_observed_at"].where(
        result["outcome_timestamp"].notna(), result["label_ready_at"]
    )

    cutoff = pd.Timestamp(config.snapshot_as_of)
    result.loc[result["label_observed_at"] > cutoff, "label_observed_at"] = pd.NaT
    result.loc[censored_flags, ["label_ready_at", "label_available_at"]] = pd.NaT
    result.loc[censored_flags, "label_observed_at"] = pd.NaT
    mature = (~censored_flags) & (result["label_ready_at"] <= cutoff)
    status = np.where(
        censored_flags, "censored", np.where(mature, "mature", "immature")
    )
    result["label_status"] = pd.Series(status, dtype="string")
    censoring_reason = pd.Series(pd.NA, index=result.index, dtype="string")
    censoring_reason.loc[censored_flags] = "administrative_loss"
    result["censoring_reason"] = censoring_reason
    target = pd.Series(pd.NA, index=result.index, dtype="boolean")
    target.loc[mature] = result.loc[mature, "outcome_timestamp"].notna()
    result["default_within_horizon"] = target
    return result.drop(columns=["positive_observed_at"])[list(APPLICATION_COLUMNS)]


def _audit_only(config: SyntheticConfig, applications: pd.DataFrame) -> pd.DataFrame:
    unique_borrowers = applications["borrower_id"].drop_duplicates().sort_values()
    audit_rng = _rng(config.seed, "audit-only")
    borrower_audit = pd.DataFrame(
        {
            "borrower_id": unique_borrowers.to_numpy(),
            "age_band": audit_rng.choice(
                np.array(["18-29", "30-44", "45-59", "60+"]),
                len(unique_borrowers),
            ),
            "sex_group": audit_rng.choice(
                np.array(["group_a", "group_b", "unknown"]),
                len(unique_borrowers),
                p=[0.47, 0.47, 0.06],
            ),
        }
    )
    return (
        applications[["application_id", "borrower_id"]]
        .merge(borrower_audit, on="borrower_id", validate="many_to_one")
        .sort_values("application_id")
        .reset_index(drop=True)[list(AUDIT_ONLY_COLUMNS)]
    )


def generate_tables(config: SyntheticConfig) -> GeneratedTables:
    """Generate all v1 tables without writing files."""
    base, default_flags = _base_applications(config)
    censor_rng = _rng(config.seed, "censoring")
    censored_flags = censor_rng.random(config.applications) < config.censored_fraction
    censor_month = censor_rng.integers(3, 10, config.applications)
    ledger = _generate_ledger(base, default_flags, censored_flags, censor_month, config)
    applications = _derive_labels(base, ledger, censored_flags, censor_month, config)
    audit = _audit_only(config, applications)
    return GeneratedTables(
        applications=applications.sort_values("application_id").reset_index(drop=True),
        ledger=ledger,
        audit_only=audit,
    )
