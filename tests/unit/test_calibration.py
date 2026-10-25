import numpy as np
import pytest

from cop.evaluation.calibration import calibration_bins


def test_calibration_bins_report_predicted_and_observed_rates() -> None:
    result = calibration_bins(
        np.array([0, 1, 1, 0]),
        np.array([0.1, 0.2, 0.8, 0.9]),
        bins=2,
    )

    assert len(result) == 2
    assert result[0]["cases"] == 2
    assert result[0]["mean_predicted_probability"] == pytest.approx(0.15)
    assert result[0]["observed_default_rate"] == pytest.approx(0.5)


def test_calibration_bins_reject_invalid_bin_count() -> None:
    with pytest.raises(ValueError, match="between 2 and 50"):
        calibration_bins(np.array([0, 1]), np.array([0.1, 0.9]), bins=1)
