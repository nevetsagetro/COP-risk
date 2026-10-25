"""Frozen input contract for the academic UCI baseline."""

from __future__ import annotations

import pandas as pd

UCI_CATEGORICAL_FEATURES = (
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6",
)
UCI_NUMERIC_FEATURES = (
    "LIMIT_BAL",
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6",
)
UCI_APPROVED_FEATURES = (
    "LIMIT_BAL",
    *UCI_CATEGORICAL_FEATURES,
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6",
)


def validate_uci_features(frame: pd.DataFrame) -> None:
    """Reject missing, reordered, extra, protected, identifier, or target columns."""
    if tuple(frame.columns) != UCI_APPROVED_FEATURES:
        raise ValueError(
            "model matrix must contain exactly the 19 approved UCI features"
        )
    if frame.isna().any(axis=None):
        raise ValueError(
            "missing_policy=fail: UCI model matrix contains missing values"
        )
