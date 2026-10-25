"""Classical model benchmark with Optuna and optional challengers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from cop.evaluation.binary import binary_classification_metrics
from cop.evaluation.home_credit import (
    _build_candidate,
    _candidate_cv,
)
from cop.training.home_credit import (
    HOME_CREDIT_EXPERIMENT_SEED,
    HomeCreditData,
    _positive_probability,
    _preprocessor,
    build_home_credit_models,
    load_static_development_data,
)


def _fit_reference(data: HomeCreditData) -> dict[str, Any]:
    model = build_home_credit_models(data)["logistic_regression"]
    train_features = data.train.loc[:, list(data.feature_columns)]
    validation_features = data.validation.loc[:, list(data.feature_columns)]
    train_target = data.train["TARGET"].to_numpy(dtype=np.int64)
    validation_target = data.validation["TARGET"].to_numpy(dtype=np.int64)
    model.fit(train_features, train_target)
    probability = _positive_probability(model, validation_features)
    return {
        "parameters": model.named_steps["classifier"].get_params(),
        "evaluation_scope": "fixed_reference_validation",
        "validation": binary_classification_metrics(validation_target, probability),
    }


def _optuna_lightgbm(
    data: HomeCreditData, *, folds: int, trials: int, seed: int
) -> dict[str, Any]:
    try:
        import optuna
    except ImportError as error:  # pragma: no cover - depends on optional extra
        return {"status": "unavailable", "reason": str(error)}

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )

    def objective(trial: Any) -> float:
        parameters = {
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.10),
            "n_estimators": trial.suggest_int("n_estimators", 150, 450, step=50),
            "num_leaves": trial.suggest_int("num_leaves", 15, 63, step=8),
            "min_child_samples": trial.suggest_int(
                "min_child_samples", 20, 120, step=20
            ),
            "subsample": trial.suggest_float("subsample", 0.75, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.75, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
        }
        result = _candidate_cv(data, "lightgbm", parameters, folds=folds)
        trial.set_user_attr("cv_std", result["cross_validation_std"])
        return float(result["cross_validation"]["average_precision"])

    study.optimize(objective, n_trials=trials)
    best_parameters = dict(study.best_params)
    selected_cv = _candidate_cv(data, "lightgbm", best_parameters, folds=folds)
    train_features = data.train.loc[:, list(data.feature_columns)]
    validation_features = data.validation.loc[:, list(data.feature_columns)]
    train_target = data.train["TARGET"].to_numpy(dtype=np.int64)
    validation_target = data.validation["TARGET"].to_numpy(dtype=np.int64)
    model = _build_candidate(data, "lightgbm", best_parameters)
    model.fit(train_features, train_target)
    probability = _positive_probability(model, validation_features)
    return {
        "status": "available",
        "search": "Optuna TPE",
        "trials_requested": trials,
        "trials_completed": len(study.trials),
        "parameters": best_parameters,
        "cross_validation": selected_cv["cross_validation"],
        "cross_validation_std": selected_cv["cross_validation_std"],
        "validation": binary_classification_metrics(validation_target, probability),
        "trial_history": [
            {
                "number": trial.number,
                "state": trial.state.name,
                "value": trial.value,
                "parameters": trial.params,
            }
            for trial in study.trials
        ],
    }


def _external_challenger(data: HomeCreditData, name: str) -> dict[str, Any]:
    try:
        preprocessor = _preprocessor(
            data.train.loc[:, list(data.feature_columns)], scale_numeric=False
        )
        train_features = preprocessor.fit_transform(
            data.train.loc[:, list(data.feature_columns)]
        )
        validation_features = preprocessor.transform(
            data.validation.loc[:, list(data.feature_columns)]
        )
        train_target = data.train["TARGET"].to_numpy(dtype=np.int64)
        validation_target = data.validation["TARGET"].to_numpy(dtype=np.int64)
        if name == "catboost":
            from catboost import CatBoostClassifier  # type: ignore[import-untyped]

            model: Any = CatBoostClassifier(
                iterations=350,
                depth=6,
                learning_rate=0.05,
                loss_function="Logloss",
                random_seed=HOME_CREDIT_EXPERIMENT_SEED,
                verbose=False,
                thread_count=1,
            )
        elif name == "xgboost":
            from xgboost import XGBClassifier

            model = XGBClassifier(
                n_estimators=350,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=HOME_CREDIT_EXPERIMENT_SEED,
                n_jobs=1,
            )
        else:
            raise ValueError(f"unsupported challenger: {name}")
        model.fit(train_features, train_target)
        probability = np.asarray(model.predict_proba(validation_features))[:, 1]
        return {
            "status": "available",
            "evaluation_scope": "fixed_challenger_validation",
            "parameters": model.get_params(),
            "validation": binary_classification_metrics(validation_target, probability),
        }
    except ImportError as error:  # pragma: no cover - optional dependency
        return {"status": "unavailable", "reason": str(error)}


def run_classical_benchmark(
    snapshot_directory: Path,
    *,
    folds: int = 3,
    optuna_trials: int = 5,
    seed: int = HOME_CREDIT_EXPERIMENT_SEED,
) -> dict[str, Any]:
    """Run reproducible classical challengers without opening the test split."""
    data = load_static_development_data(snapshot_directory)
    return {
        "authorized_use": "academic_static_benchmark_only",
        "test_status": "unopened",
        "feature_version": "features-v2",
        "fit_split": "train",
        "selection_split": "train_cross_validation",
        "evaluation_split": "validation",
        "experiment_seed": seed,
        "cross_validation_folds": folds,
        "primary_metric": "average_precision",
        "models": {
            "logistic_regression": _fit_reference(data),
            "lightgbm_optuna": _optuna_lightgbm(
                data, folds=folds, trials=optuna_trials, seed=seed
            ),
            "catboost": _external_challenger(data, "catboost"),
            "xgboost": _external_challenger(data, "xgboost"),
        },
        "human_explanation": (
            "The benchmark keeps the same train-validation boundary and compares "
            "classical challengers under one primary ranking metric. A challenger "
            "is evidence, not an automatic promotion."
        ),
    }


def write_classical_benchmark(
    snapshot_directory: Path,
    output: Path,
    *,
    folds: int = 3,
    optuna_trials: int = 5,
    seed: int = HOME_CREDIT_EXPERIMENT_SEED,
) -> Path:
    report = run_classical_benchmark(
        snapshot_directory,
        folds=folds,
        optuna_trials=optuna_trials,
        seed=seed,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output
