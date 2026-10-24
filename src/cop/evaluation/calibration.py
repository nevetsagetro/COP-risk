"""Calibration-curve data for the academic validation report."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt


def calibration_bins(
    target: npt.ArrayLike,
    probability: npt.ArrayLike,
    *,
    bins: int = 10,
) -> list[dict[str, Any]]:
    """Return non-empty uniform probability bins with observed outcomes."""
    actual = np.asarray(target, dtype=np.int64)
    score = np.asarray(probability, dtype=np.float64)
    if actual.ndim != 1 or score.ndim != 1 or actual.shape != score.shape:
        raise ValueError("target and probability must be aligned vectors")
    if actual.size == 0 or set(actual) != {0, 1}:
        raise ValueError("target must be a non-empty binary vector with both classes")
    if not 2 <= bins <= 50:
        raise ValueError("bins must be between 2 and 50")
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError("probabilities must be finite and within [0, 1]")

    edges = np.linspace(0.0, 1.0, bins + 1)
    result: list[dict[str, Any]] = []
    for index in range(bins):
        lower, upper = float(edges[index]), float(edges[index + 1])
        if index == bins - 1:
            mask = (score >= lower) & (score <= upper)
        else:
            mask = (score >= lower) & (score < upper)
        if not mask.any():
            continue
        result.append(
            {
                "bin_lower": lower,
                "bin_upper": upper,
                "cases": int(mask.sum()),
                "mean_predicted_probability": float(score[mask].mean()),
                "observed_default_rate": float(actual[mask].mean()),
            }
        )
    return result
