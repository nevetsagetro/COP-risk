"""Fixed descriptive metrics for the academic binary baseline."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
from sklearn.metrics import (  # type: ignore[import-untyped]
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def prevalence(target: npt.ArrayLike) -> float:
    values = np.asarray(target, dtype=np.int64)
    if values.ndim != 1 or values.size == 0 or not set(values).issubset({0, 1}):
        raise ValueError("target must be a non-empty one-dimensional binary array")
    return float(values.mean())


def binary_classification_metrics(
    target: npt.ArrayLike,
    probability: npt.ArrayLike,
    *,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Calculate the frozen metric set without selecting a threshold."""
    actual = np.asarray(target, dtype=np.int64)
    score = np.asarray(probability, dtype=np.float64)
    if actual.ndim != 1 or score.ndim != 1 or actual.shape != score.shape:
        raise ValueError("target and probability must be aligned vectors")
    if actual.size == 0 or set(actual) != {0, 1}:
        raise ValueError("metrics require both binary target classes")
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError("probabilities must be finite and within [0, 1]")
    predicted = (score >= threshold).astype(np.int64)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    return {
        "roc_auc": float(roc_auc_score(actual, score)),
        "average_precision": float(average_precision_score(actual, score)),
        "log_loss": float(log_loss(actual, score, labels=[0, 1])),
        "brier_score": float(brier_score_loss(actual, score)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "confusion_matrix": {
            "labels": [0, 1],
            "values": [[int(value) for value in row] for row in matrix.tolist()],
        },
        "threshold": threshold,
    }
