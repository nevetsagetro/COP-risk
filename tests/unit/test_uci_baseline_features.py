from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cop.evaluation.binary import binary_classification_metrics
from cop.features.uci import (
    UCI_APPROVED_FEATURES,
    UCI_CATEGORICAL_FEATURES,
    validate_uci_features,
)
from cop.training.config import load_baseline_config
from cop.training.uci_baseline import build_models

CONFIG = Path("configs/training/uci-baseline.yaml")


def _feature_frame(rows: int = 6) -> pd.DataFrame:
    values = {
        name: np.arange(rows, dtype=np.float64) + position
        for position, name in enumerate(UCI_APPROVED_FEATURES)
    }
    for name in UCI_CATEGORICAL_FEATURES:
        values[name] = np.resize(np.array([-1, 0, 1]), rows)
    return pd.DataFrame(values, columns=UCI_APPROVED_FEATURES)


def test_feature_contract_is_exact_and_missing_policy_fails() -> None:
    valid = _feature_frame()
    validate_uci_features(valid)

    with pytest.raises(ValueError, match="exactly the 19"):
        validate_uci_features(valid.assign(ID=range(len(valid))))
    missing = valid.copy()
    missing.loc[0, "LIMIT_BAL"] = np.nan
    with pytest.raises(ValueError, match="missing_policy=fail"):
        validate_uci_features(missing)


def test_preprocessing_is_fit_only_from_train_and_has_no_imputer() -> None:
    config = load_baseline_config(CONFIG)
    train = _feature_frame()
    validation = _feature_frame(2)
    validation.loc[:, "LIMIT_BAL"] = 1_000_000
    validation.loc[:, "PAY_0"] = 99
    target = np.array([0, 1, 0, 1, 0, 1])

    models = build_models(config)
    logistic = models["logistic_regression"]
    logistic.fit(train, target)
    logistic.predict_proba(validation)

    preprocessor = logistic.named_steps["preprocessor"]
    scaler = preprocessor.named_transformers_["numeric"]
    encoder = preprocessor.named_transformers_["categorical"]
    expected_mean = float(train["LIMIT_BAL"].mean())
    assert scaler.mean_[0] == pytest.approx(expected_mean)
    assert 99 not in encoder.categories_[0]
    assert all("imput" not in name.lower() for name, _ in logistic.steps)


def test_model_parameters_are_frozen_without_balancing_or_tuning() -> None:
    config = load_baseline_config(CONFIG)
    models = build_models(config)
    logistic = models["logistic_regression"].named_steps["classifier"]
    lightgbm = models["lightgbm"].named_steps["classifier"]

    assert logistic.class_weight is None
    assert logistic.random_state == 42
    assert logistic.solver == "liblinear"
    assert logistic.l1_ratio == 0.0
    assert lightgbm.class_weight is None
    assert lightgbm.n_jobs == 1
    assert lightgbm.random_state == 42
    assert lightgbm.n_estimators == 200
    assert not hasattr(models["lightgbm"], "sampler")


def test_metric_set_uses_fixed_half_threshold() -> None:
    metrics = binary_classification_metrics(
        np.array([0, 0, 1, 1]), np.array([0.1, 0.6, 0.4, 0.9])
    )

    assert set(metrics) == {
        "roc_auc",
        "average_precision",
        "log_loss",
        "brier_score",
        "precision",
        "recall",
        "f1",
        "confusion_matrix",
        "threshold",
    }
    assert metrics["threshold"] == 0.5
    assert metrics["confusion_matrix"]["values"] == [[1, 1], [1, 1]]
