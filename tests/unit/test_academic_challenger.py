from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cop.features.academic_challenger import (
    CHALLENGER_DERIVED_FEATURES,
    CHALLENGER_FEATURES,
    engineer_uci_features,
)
from cop.features.uci import UCI_APPROVED_FEATURES


def _features() -> pd.DataFrame:
    frame = pd.DataFrame(
        {feature: np.zeros(2, dtype=float) for feature in UCI_APPROVED_FEATURES}
    )
    frame["LIMIT_BAL"] = [1000, 2000]
    frame["PAY_0"] = [2, 0]
    frame["PAY_2"] = [1, 0]
    frame["PAY_3"] = [0, 0]
    frame["PAY_4"] = [0, 0]
    frame["PAY_5"] = [0, 0]
    frame["PAY_6"] = [0, 0]
    frame["BILL_AMT1"] = [500, 1000]
    frame["BILL_AMT2"] = [400, 900]
    frame["BILL_AMT6"] = [100, 600]
    frame["PAY_AMT1"] = [250, 100]
    frame["PAY_AMT2"] = [200, 100]
    frame["PAY_AMT6"] = [50, 100]
    return frame


def test_engineering_is_deterministic_and_uses_only_approved_input() -> None:
    features = _features()
    first = engineer_uci_features(features)
    second = engineer_uci_features(features.copy())

    pd.testing.assert_frame_equal(first, second)
    assert tuple(first.columns) == CHALLENGER_FEATURES
    assert len(CHALLENGER_DERIVED_FEATURES) == 14
    assert first.loc[0, "PAY_DELAY_MAX"] == 2
    assert first.loc[0, "PAY_DELAY_COUNT"] == 2
    assert first.loc[0, "BILL_AMT_TREND"] == 400
    assert first.loc[0, "PAY_AMT_TREND"] == 200
    assert first.loc[0, "PAYMENT_COVERAGE_RECENT"] == pytest.approx(250 / 501)


def test_engineering_rejects_target_or_extra_columns() -> None:
    features = _features().assign(default_payment_next_month=1)
    with pytest.raises(ValueError, match="exactly the 19"):
        engineer_uci_features(features)
