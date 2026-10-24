from __future__ import annotations

import numpy as np

from cop.evaluation.model_lab import _select_threshold


def test_threshold_selection_is_bounded_and_deterministic() -> None:
    target = np.array([0, 0, 1, 1, 1, 0], dtype=np.int64)
    probability = np.array([0.01, 0.20, 0.30, 0.60, 0.90, 0.80], dtype=np.float64)

    first = _select_threshold(target, probability)
    second = _select_threshold(target, probability)

    assert first == second
    assert 0.05 <= first[0] <= 0.95
    assert first[1]["threshold"] == first[0]
