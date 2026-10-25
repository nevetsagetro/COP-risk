"""Deterministic, leakage-safe features for the academic challenger."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cop.features.uci import UCI_APPROVED_FEATURES, validate_uci_features

CHALLENGER_DERIVED_FEATURES = (
    "PAY_DELAY_MAX",
    "PAY_DELAY_COUNT",
    "PAY_DELAY_MEAN",
    "PAY_DELAY_RECENT",
    "BILL_AMT_MEAN",
    "BILL_AMT_TREND",
    "BILL_AMT_RECENT_CHANGE",
    "BILL_AMT_VOLATILITY",
    "PAY_AMT_MEAN",
    "PAY_AMT_TREND",
    "PAY_AMT_RECENT_CHANGE",
    "PAY_AMT_VOLATILITY",
    "PAYMENT_COVERAGE_RECENT",
    "CREDIT_UTILIZATION_RECENT",
)

CHALLENGER_FEATURES = UCI_APPROVED_FEATURES + CHALLENGER_DERIVED_FEATURES


def engineer_uci_features(features: pd.DataFrame) -> pd.DataFrame:
    """Add history aggregates without reading target, test, or future columns.

    UCI suffix ``1`` is the most recent month and suffix ``6`` the oldest one.
    The transformation is deterministic and has no fitted state, so it can be
    applied independently to train, validation, and serving inputs.
    """
    validate_uci_features(features)
    result = features.copy()
    delay_columns = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    bill_columns = [f"BILL_AMT{i}" for i in range(1, 7)]
    payment_columns = [f"PAY_AMT{i}" for i in range(1, 7)]

    delays = result.loc[:, delay_columns].astype(float)
    bills = result.loc[:, bill_columns].astype(float)
    payments = result.loc[:, payment_columns].astype(float)

    result["PAY_DELAY_MAX"] = delays.max(axis=1)
    result["PAY_DELAY_COUNT"] = (delays > 0).sum(axis=1).astype(float)
    result["PAY_DELAY_MEAN"] = delays.mean(axis=1)
    result["PAY_DELAY_RECENT"] = delays["PAY_0"]
    result["BILL_AMT_MEAN"] = bills.mean(axis=1)
    result["BILL_AMT_TREND"] = bills["BILL_AMT1"] - bills["BILL_AMT6"]
    result["BILL_AMT_RECENT_CHANGE"] = bills["BILL_AMT1"] - bills["BILL_AMT2"]
    result["BILL_AMT_VOLATILITY"] = bills.std(axis=1, ddof=0)
    result["PAY_AMT_MEAN"] = payments.mean(axis=1)
    result["PAY_AMT_TREND"] = payments["PAY_AMT1"] - payments["PAY_AMT6"]
    result["PAY_AMT_RECENT_CHANGE"] = payments["PAY_AMT1"] - payments["PAY_AMT2"]
    result["PAY_AMT_VOLATILITY"] = payments.std(axis=1, ddof=0)
    result["PAYMENT_COVERAGE_RECENT"] = payments["PAY_AMT1"] / (
        bills["BILL_AMT1"].abs() + 1.0
    )
    result["CREDIT_UTILIZATION_RECENT"] = bills["BILL_AMT1"] / (
        result["LIMIT_BAL"].abs() + 1.0
    )

    if tuple(result.columns) != CHALLENGER_FEATURES:
        raise AssertionError("challenger feature order changed unexpectedly")
    values = result.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("challenger features must be finite")
    return result
