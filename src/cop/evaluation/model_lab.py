"""Reproducible academic tuning lab for the two baseline model families."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import numpy.typing as npt
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.model_selection import StratifiedKFold  # type: ignore[import-untyped]
from sklearn.neighbors import KNeighborsClassifier  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from cop.evaluation.binary import binary_classification_metrics
from cop.evaluation.challenger import positive_probability
from cop.training.config import BaselineConfig, load_baseline_config
from cop.training.uci_baseline import (
    DevelopmentData,
    _preprocessor,
    build_models,
    load_development_data,
)

MODEL_LAB_CANDIDATES: dict[str, tuple[dict[str, Any], ...]] = {
    "logistic_regression": (
        {"C": 0.1, "class_weight": None},
        {"C": 1.0, "class_weight": None},
        {"C": 1.0, "class_weight": "balanced"},
        {"C": 3.0, "class_weight": None},
    ),
    "lightgbm": (
        {"learning_rate": 0.03, "n_estimators": 300, "num_leaves": 31},
        {"learning_rate": 0.05, "n_estimators": 200, "num_leaves": 63},
        {"learning_rate": 0.05, "n_estimators": 300, "num_leaves": 31},
        {"learning_rate": 0.03, "n_estimators": 400, "num_leaves": 15},
    ),
    "knn": (
        {"n_neighbors": 15, "weights": "distance", "p": 2},
        {"n_neighbors": 25, "weights": "distance", "p": 2},
        {"n_neighbors": 15, "weights": "uniform", "p": 2},
        {"n_neighbors": 25, "weights": "distance", "p": 1},
    ),
}
MODEL_LAB_NAMES = ("logistic_regression", "lightgbm", "knn")


def _build_model(
    config: BaselineConfig, name: str, overrides: dict[str, Any]
) -> Pipeline:
    params = dict(cast(dict[str, Any], config.raw["models"].get(name, {})))
    params.update(overrides)
    seed = int(config.raw["random_seed"])
    classifier: Any
    if name == "logistic_regression":
        classifier = LogisticRegression(**params, random_state=seed)
        scale_numeric = True
    elif name == "lightgbm":
        classifier = LGBMClassifier(**params, random_state=seed)
        scale_numeric = False
    elif name == "knn":
        classifier = KNeighborsClassifier(**params)
        scale_numeric = True
    else:
        raise ValueError(f"unsupported model family: {name}")
    return Pipeline(
        steps=[
            ("preprocessor", _preprocessor(scale_numeric=scale_numeric)),
            ("classifier", classifier),
        ]
    )


def _threshold_grid() -> npt.NDArray[np.float64]:
    return np.arange(0.05, 0.951, 0.01, dtype=np.float64)


def _select_threshold(
    target: npt.NDArray[np.int64], probability: npt.NDArray[np.float64]
) -> tuple[float, dict[str, Any]]:
    candidates = []
    for threshold in _threshold_grid():
        metrics = binary_classification_metrics(
            target, probability, threshold=float(threshold)
        )
        candidates.append(
            (
                float(metrics["f1"]),
                float(metrics["recall"]),
                -float(threshold),
                float(threshold),
                metrics,
            )
        )
    _, _, _, selected, metrics = max(candidates)
    return selected, metrics


def _cross_validate_candidate(
    data: DevelopmentData,
    config: BaselineConfig,
    name: str,
    parameters: dict[str, Any],
    *,
    folds: int,
) -> dict[str, Any]:
    target = data.train.target
    splitter = StratifiedKFold(
        n_splits=folds, shuffle=True, random_state=int(config.raw["random_seed"])
    )
    out_of_fold = np.empty(len(target), dtype=np.float64)
    fold_metrics: list[dict[str, Any]] = []
    for train_index, validation_index in splitter.split(data.train.features, target):
        model = _build_model(config, name, parameters)
        model.fit(data.train.features.iloc[train_index], target[train_index])
        probability = positive_probability(
            model, data.train.features.iloc[validation_index]
        )
        out_of_fold[validation_index] = probability
        fold_metrics.append(
            binary_classification_metrics(
                target[validation_index], probability, threshold=0.5
            )
        )
    oof_metrics = binary_classification_metrics(target, out_of_fold, threshold=0.5)
    selected_threshold, threshold_metrics = _select_threshold(target, out_of_fold)
    fold_summary = {
        key: {
            "mean": float(np.mean([float(item[key]) for item in fold_metrics])),
            "std": float(np.std([float(item[key]) for item in fold_metrics], ddof=0)),
        }
        for key in ("roc_auc", "average_precision", "brier_score", "log_loss")
    }
    return {
        "parameters": parameters,
        "fold_count": folds,
        "fold_metrics": fold_metrics,
        "cross_validation": {
            key: values["mean"] for key, values in fold_summary.items()
        },
        "cross_validation_std": {
            key: values["std"] for key, values in fold_summary.items()
        },
        "out_of_fold_metrics_at_0_5": oof_metrics,
        "selected_threshold": selected_threshold,
        "out_of_fold_metrics_at_selected_threshold": threshold_metrics,
    }


def _evaluate_selected(
    data: DevelopmentData,
    config: BaselineConfig,
    name: str,
    selected: dict[str, Any],
) -> dict[str, Any]:
    model = _build_model(config, name, cast(dict[str, Any], selected["parameters"]))
    model.fit(data.train.features, data.train.target)
    probability = positive_probability(model, data.validation.features)
    threshold = float(selected["selected_threshold"])
    return {
        "model": name,
        "parameters": selected["parameters"],
        "validation_at_0_5": binary_classification_metrics(
            data.validation.target, probability, threshold=0.5
        ),
        "validation_at_selected_threshold": binary_classification_metrics(
            data.validation.target, probability, threshold=threshold
        ),
    }


def run_model_lab(config_path: Any, *, folds: int = 3) -> dict[str, Any]:
    """Tune both families on train and evaluate selected candidates on validation."""
    if folds < 3:
        raise ValueError("model lab requires at least three folds")
    config = load_baseline_config(config_path)
    data = load_development_data(config)
    models: dict[str, Any] = {}
    for name in MODEL_LAB_NAMES:
        candidates = [
            _cross_validate_candidate(data, config, name, parameters, folds=folds)
            for parameters in MODEL_LAB_CANDIDATES[name]
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
        models[name] = {
            "search_space": list(MODEL_LAB_CANDIDATES[name]),
            "selection_rule": (
                "rank by validation-free train CV Average Precision, then "
                "ROC-AUC, then lower log loss"
            ),
            "candidates": candidates,
            "selected": _evaluate_selected(data, config, name, selected),
        }
    fixed = build_models(config)
    fixed_metrics: dict[str, Any] = {}
    for name, model in fixed.items():
        model.fit(data.train.features, data.train.target)
        fixed_metrics[name] = binary_classification_metrics(
            data.validation.target,
            positive_probability(model, data.validation.features),
            threshold=0.5,
        )
    return {
        "authorized_use": "academic_baseline_only",
        "test_status": "unopened",
        "fit_split": "train",
        "selection_split": "train_cross_validation_out_of_fold",
        "evaluation_split": "validation",
        "primary_selection_metric": "average_precision",
        "threshold_selection": (
            "maximize_f1_on_train_out_of_fold; recall_tiebreak; "
            "threshold_grid_0.05_to_0.95_step_0.01"
        ),
        "folds": folds,
        "fixed_baseline_at_0_5": fixed_metrics,
        "models": models,
        "claims_not_made": [
            "winner",
            "champion",
            "production_validity",
            "real_world_calibration",
        ],
    }
