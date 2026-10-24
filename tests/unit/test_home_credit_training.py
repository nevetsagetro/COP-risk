from pathlib import Path
from typing import Any

import pandas as pd

from cop.data.home_credit import HOME_CREDIT_APPLICATION_FEATURES
from cop.training.home_credit import (
    build_home_credit_models,
    load_static_development_data,
)


def _write_snapshot(root: Path) -> None:
    root.mkdir()
    rows = 8
    base: dict[str, list[Any]] = {
        feature: [float(index) for index in range(rows)]
        for feature in HOME_CREDIT_APPLICATION_FEATURES
    }
    base.update(
        {
            "SK_ID_CURR": list(range(rows)),
            "TARGET": [index % 2 for index in range(rows)],
            "split": ["train"] * 4 + ["validation"] * 4,
            "BUREAU_COUNT": [0.0] * rows,
        }
    )
    frame = pd.DataFrame(base)
    frame.iloc[:4].to_parquet(root / "train.parquet", index=False)
    frame.iloc[4:].to_parquet(root / "validation.parquet", index=False)


def test_home_credit_training_loads_only_development_and_builds_models(
    tmp_path: Path,
) -> None:
    root = tmp_path / "snapshot"
    _write_snapshot(root)

    data = load_static_development_data(root)
    models = build_home_credit_models(data)

    assert len(data.feature_columns) == len(HOME_CREDIT_APPLICATION_FEATURES) + 1
    assert set(models) == {"logistic_regression", "lightgbm"}
