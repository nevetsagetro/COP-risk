import numpy as np
import pytest

from cop.evaluation.policy import capacity_metrics


def test_capacity_metrics_ranks_cases_and_reports_lift() -> None:
    result = capacity_metrics(
        np.array([1, 0, 1, 0]),
        np.array([0.9, 0.8, 0.2, 0.1]),
        capacity=0.5,
    )

    assert result["reviewed_rows"] == 2
    assert result["defaults_found"] == 1
    assert result["precision_at_capacity"] == pytest.approx(0.5)
    assert result["recall_at_capacity"] == pytest.approx(0.5)
    assert result["lift"] == pytest.approx(1.0)
    assert result["minimum_selected_probability"] == pytest.approx(0.8)


def test_capacity_metrics_rejects_invalid_capacity() -> None:
    with pytest.raises(ValueError, match="capacity"):
        capacity_metrics(np.array([0, 1]), np.array([0.1, 0.9]), capacity=0)
