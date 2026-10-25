"""Leakage-safe comparison for an academic LightGBM challenger."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.model_selection import StratifiedKFold  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import OneHotEncoder  # type: ignore[import-untyped]

from cop.evaluation.binary import binary_classification_metrics
from cop.features.academic_challenger import (
    CHALLENGER_DERIVED_FEATURES,
    CHALLENGER_FEATURES,
    engineer_uci_features,
)
from cop.features.uci import UCI_CATEGORICAL_FEATURES
from cop.training.config import load_baseline_config
from cop.training.uci_baseline import (
    MODEL_NAMES,
    DevelopmentData,
    build_models,
    load_development_data,
)

CHALLENGER_CANDIDATES: tuple[dict[str, Any], ...] = (
    {"learning_rate": 0.03, "n_estimators": 300, "num_leaves": 31},
    {"learning_rate": 0.05, "n_estimators": 200, "num_leaves": 63},
    {"learning_rate": 0.05, "n_estimators": 300, "num_leaves": 31},
)


def positive_probability(
    model: Pipeline, features: pd.DataFrame
) -> npt.NDArray[np.float64]:
    probability = np.asarray(model.predict_proba(features), dtype=np.float64)
    classes = np.asarray(model.classes_)
    positions = np.flatnonzero(classes == 1)
    if probability.ndim != 2 or len(positions) != 1:
        raise ValueError("model does not expose one positive-class probability")
    return cast(npt.NDArray[np.float64], probability[:, int(positions[0])])


def build_challenger_model(config: Any, overrides: dict[str, Any]) -> Pipeline:
    base = dict(config.raw["models"]["lightgbm"])
    base.update(overrides)
    seed = int(config.raw["random_seed"])
    numeric = [
        feature
        for feature in CHALLENGER_FEATURES
        if feature not in UCI_CATEGORICAL_FEATURES
    ]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", dtype=np.float64),
                list(UCI_CATEGORICAL_FEATURES),
            ),
            ("numeric", "passthrough", numeric),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LGBMClassifier(**base, random_state=seed)),
        ]
    )


def _cv_metrics(
    data: pd.DataFrame,
    target: npt.NDArray[np.int64],
    config: Any,
    overrides: dict[str, Any],
    *,
    folds: int,
) -> dict[str, float]:
    splitter = StratifiedKFold(
        n_splits=folds, shuffle=True, random_state=int(config.raw["random_seed"])
    )
    metrics: list[dict[str, Any]] = []
    for train_index, validation_index in splitter.split(data, target):
        model = build_challenger_model(config, overrides)
        model.fit(data.iloc[train_index], target[train_index])
        probability = positive_probability(model, data.iloc[validation_index])
        metrics.append(
            binary_classification_metrics(
                target[validation_index], probability, threshold=0.5
            )
        )
    return {
        key: float(np.mean([float(item[key]) for item in metrics]))
        for key in ("roc_auc", "average_precision", "brier_score", "log_loss")
    }


def run_challenger_comparison(config_path: Any, *, folds: int = 3) -> dict[str, Any]:
    """Compare a feature-engineered challenger using train CV and validation."""
    if folds < 3:
        raise ValueError("challenger comparison requires at least three folds")
    config = load_baseline_config(config_path)
    data: DevelopmentData = load_development_data(config)
    train_features = engineer_uci_features(data.train.features)
    validation_features = engineer_uci_features(data.validation.features)

    cv_candidates = [
        {
            "parameters": candidate,
            "cross_validation": _cv_metrics(
                train_features,
                data.train.target,
                config,
                candidate,
                folds=folds,
            ),
        }
        for candidate in CHALLENGER_CANDIDATES
    ]
    selected = max(
        cv_candidates,
        key=lambda item: (
            item["cross_validation"]["roc_auc"],
            item["cross_validation"]["average_precision"],
        ),
    )
    selected_parameters = selected["parameters"]

    baseline = build_models(config)["lightgbm"]
    baseline.fit(data.train.features, data.train.target)
    baseline_probability = positive_probability(baseline, data.validation.features)

    challenger = build_challenger_model(config, selected_parameters)
    challenger.fit(train_features, data.train.target)
    challenger_probability = positive_probability(challenger, validation_features)

    baseline_metrics = binary_classification_metrics(
        data.validation.target, baseline_probability, threshold=0.5
    )
    challenger_metrics = binary_classification_metrics(
        data.validation.target, challenger_probability, threshold=0.5
    )
    return {
        "authorized_use": "academic_baseline_only",
        "test_status": "unopened",
        "fit_split": "train",
        "selection_split": "train_cross_validation",
        "evaluation_split": "validation",
        "feature_count": len(CHALLENGER_FEATURES),
        "derived_features": list(CHALLENGER_DERIVED_FEATURES),
        "candidates": cv_candidates,
        "selected_parameters": selected_parameters,
        "baseline": {"model": MODEL_NAMES[1], "metrics": baseline_metrics},
        "challenger": {
            "model": "lightgbm_feature_engineered",
            "metrics": challenger_metrics,
        },
        "validation_delta": {
            key: float(challenger_metrics[key] - baseline_metrics[key])
            for key in ("roc_auc", "average_precision", "brier_score", "log_loss")
        },
        "claims_not_made": ["winner", "champion", "production_validity"],
    }
