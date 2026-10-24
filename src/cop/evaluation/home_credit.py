"""Cross-validated model search for the static Home Credit benchmark."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.model_selection import StratifiedKFold  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from cop.evaluation.binary import binary_classification_metrics
from cop.training.home_credit import (
    HomeCreditData,
    _positive_probability,
    _preprocessor,
    load_static_development_data,
)

HOME_CREDIT_SEARCH_SPACE: dict[str, tuple[dict[str, Any], ...]] = {
    "logistic_regression": (
        {"C": 0.1},
        {"C": 0.5},
        {"C": 1.0},
    ),
    "lightgbm": (
        {"learning_rate": 0.03, "n_estimators": 200, "num_leaves": 15},
        {"learning_rate": 0.05, "n_estimators": 250, "num_leaves": 31},
        {"learning_rate": 0.05, "n_estimators": 350, "num_leaves": 31},
    ),
}


def _build_candidate(
    data: HomeCreditData, name: str, parameters: dict[str, Any]
) -> Pipeline:
    features = data.train.loc[:, list(data.feature_columns)]
    if name == "logistic_regression":
        classifier: Any = LogisticRegression(
            C=float(parameters["C"]),
            class_weight=None,
            max_iter=500,
            solver="liblinear",
            random_state=42,
        )
        scale_numeric = True
    elif name == "lightgbm":
        classifier = LGBMClassifier(
            **parameters,
            class_weight=None,
            n_jobs=1,
            random_state=42,
            verbosity=-1,
        )
        scale_numeric = False
    else:
        raise ValueError(f"unsupported Home Credit model family: {name}")
    return Pipeline(
        steps=[
            ("preprocessor", _preprocessor(features, scale_numeric=scale_numeric)),
            ("classifier", classifier),
        ]
    )


def _candidate_cv(
    data: HomeCreditData,
    name: str,
    parameters: dict[str, Any],
    *,
    folds: int,
) -> dict[str, Any]:
    target = data.train["TARGET"].to_numpy(dtype=np.int64)
    features = data.train.loc[:, list(data.feature_columns)]
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    fold_metrics: list[dict[str, float]] = []
    for train_index, validation_index in splitter.split(features, target):
        model = _build_candidate(data, name, parameters)
        model.fit(features.iloc[train_index], target[train_index])
        probability = _positive_probability(model, features.iloc[validation_index])
        fold_metrics.append(
            cast(
                dict[str, float],
                {
                    key: value
                    for key, value in binary_classification_metrics(
                        target[validation_index], probability
                    ).items()
                    if key
                    in {"roc_auc", "average_precision", "brier_score", "log_loss"}
                },
            )
        )
    aggregate = {
        key: float(np.mean([metric[key] for metric in fold_metrics]))
        for key in fold_metrics[0]
    }
    variation = {
        key: float(np.std([metric[key] for metric in fold_metrics], ddof=0))
        for key in fold_metrics[0]
    }
    return {
        "parameters": parameters,
        "folds": fold_metrics,
        "cross_validation": aggregate,
        "cross_validation_std": variation,
    }


def run_home_credit_model_lab(
    snapshot_directory: Any, *, folds: int = 3
) -> dict[str, Any]:
    """Search candidates on train CV and evaluate selected candidates on validation."""
    if folds < 3:
        raise ValueError("Home Credit model lab requires at least three folds")
    data = load_static_development_data(snapshot_directory)
    train_features = data.train.loc[:, list(data.feature_columns)]
    train_target = data.train["TARGET"].to_numpy(dtype=np.int64)
    validation_features = data.validation.loc[:, list(data.feature_columns)]
    validation_target = data.validation["TARGET"].to_numpy(dtype=np.int64)
    models: dict[str, Any] = {}
    for name, search_space in HOME_CREDIT_SEARCH_SPACE.items():
        candidates = [
            _candidate_cv(data, name, parameters, folds=folds)
            for parameters in search_space
        ]
        ranking = sorted(
            range(len(candidates)),
            key=lambda index: (
                candidates[index]["cross_validation"]["average_precision"],
                candidates[index]["cross_validation"]["roc_auc"],
                -candidates[index]["cross_validation"]["log_loss"],
            ),
            reverse=True,
        )
        for rank, index in enumerate(ranking, start=1):
            candidates[index]["rank"] = rank
            candidates[index]["trial_id"] = f"{name}-trial-{index + 1:02d}"
            candidates[index]["selected"] = rank == 1
        selected = candidates[ranking[0]]
        model = _build_candidate(
            data, name, cast(dict[str, Any], selected["parameters"])
        )
        model.fit(train_features, train_target)
        probability = _positive_probability(model, validation_features)
        models[name] = {
            "search_space": list(search_space),
            "candidates": candidates,
            "selected_validation": binary_classification_metrics(
                validation_target, probability, threshold=0.5
            ),
        }
    return {
        "authorized_use": "academic_static_benchmark_only",
        "test_status": "unopened",
        "fit_split": "train",
        "selection_split": "train_cross_validation",
        "evaluation_split": "validation",
        "primary_selection_metric": "average_precision",
        "folds": folds,
        "models": models,
        "static_limitation": "No application timestamp; no temporal stability claim.",
    }
