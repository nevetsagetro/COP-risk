"""Capacity-constrained ranking metrics for the academic decision demo."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt


def capacity_metrics(
    target: npt.ArrayLike,
    probability: npt.ArrayLike,
    *,
    capacity: float,
) -> dict[str, Any]:
    """Evaluate the cases selected by ranking scores up to a review capacity.

    The capacity is a review-budget fraction, not a probability threshold. The
    function uses stable descending ranking and never fits or selects a model.
    """
    actual = np.asarray(target, dtype=np.int64)
    score = np.asarray(probability, dtype=np.float64)
    if actual.ndim != 1 or score.ndim != 1 or actual.shape != score.shape:
        raise ValueError("target and probability must be aligned vectors")
    if actual.size == 0 or set(actual) != {0, 1}:
        raise ValueError("target must be a non-empty binary vector with both classes")
    if not 0 < capacity <= 1:
        raise ValueError("capacity must be greater than 0 and at most 1")
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError("probabilities must be finite and within [0, 1]")

    reviewed = max(1, int(np.ceil(actual.size * capacity)))
    order = np.argsort(-score, kind="mergesort")
    selected = order[:reviewed]
    defaults_found = int(actual[selected].sum())
    total_defaults = int(actual.sum())
    precision = defaults_found / reviewed
    recall = defaults_found / total_defaults
    prevalence = float(actual.mean())
    return {
        "capacity": float(capacity),
        "reviewed_rows": reviewed,
        "review_rate": reviewed / actual.size,
        "defaults_found": defaults_found,
        "total_defaults": total_defaults,
        "precision_at_capacity": precision,
        "recall_at_capacity": recall,
        "prevalence": prevalence,
        "lift": precision / prevalence,
        "minimum_selected_probability": float(score[selected[-1]]),
    }
