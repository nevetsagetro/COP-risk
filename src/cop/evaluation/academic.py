"""Reproducible cross-validation and calibration study for the UCI baseline."""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV  # type: ignore[import-untyped]
from sklearn.model_selection import StratifiedKFold  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from cop.data.hashing import sha256_file
from cop.evaluation.binary import binary_classification_metrics
from cop.training.config import load_baseline_config
from cop.training.uci_baseline import (
    MODEL_NAMES,
    DevelopmentData,
    build_models,
    load_development_data,
)

STUDY_VERSION = 1


def _positive_probability(
    model: Pipeline | CalibratedClassifierCV, features: pd.DataFrame
) -> npt.NDArray[np.float64]:
    probabilities = np.asarray(model.predict_proba(features), dtype=np.float64)
    classes = np.asarray(model.classes_)
    positions = np.flatnonzero(classes == 1)
    if probabilities.ndim != 2 or len(positions) != 1:
        raise ValueError("model does not expose one positive-class probability")
    return cast(npt.NDArray[np.float64], probabilities[:, int(positions[0])])


def _aggregate(metrics: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    keys = ("roc_auc", "average_precision", "log_loss", "brier_score")
    return {
        key: {
            "mean": float(np.mean([float(item[key]) for item in metrics])),
            "std": float(np.std([float(item[key]) for item in metrics], ddof=1))
            if len(metrics) > 1
            else 0.0,
        }
        for key in keys
    }


def _cross_validate(
    data: DevelopmentData,
    factory: Callable[[], Pipeline],
    *,
    seed: int,
    folds: int,
) -> tuple[dict[str, Any], npt.NDArray[np.float64]]:
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    features = data.train.features.reset_index(drop=True)
    target = data.train.target
    out_of_fold = np.full(len(target), np.nan, dtype=np.float64)
    fold_metrics: list[dict[str, Any]] = []
    for fold, (train_index, validation_index) in enumerate(
        splitter.split(features, target), start=1
    ):
        model = factory()
        model.fit(features.iloc[train_index], target[train_index])
        probabilities = _positive_probability(model, features.iloc[validation_index])
        out_of_fold[validation_index] = probabilities
        metrics = binary_classification_metrics(
            target[validation_index], probabilities, threshold=0.5
        )
        fold_metrics.append(
            {
                "fold": fold,
                "rows": len(validation_index),
                **{
                    key: metrics[key]
                    for key in (
                        "roc_auc",
                        "average_precision",
                        "log_loss",
                        "brier_score",
                    )
                },
            }
        )
    if np.isnan(out_of_fold).any():
        raise RuntimeError("cross-validation did not produce complete OOF scores")
    return {
        "folds": fold_metrics,
        "aggregate": _aggregate(fold_metrics),
    }, out_of_fold


def _threshold_rows(
    target: npt.NDArray[np.int64], probability: npt.NDArray[np.float64]
) -> list[dict[str, Any]]:
    rows = []
    for threshold in np.linspace(0.1, 0.9, 17):
        metrics = binary_classification_metrics(
            target, probability, threshold=float(threshold)
        )
        matrix = cast(dict[str, Any], metrics["confusion_matrix"])["values"]
        rows.append(
            {
                "threshold": float(threshold),
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "true_negatives": matrix[0][0],
                "false_positives": matrix[0][1],
                "false_negatives": matrix[1][0],
                "true_positives": matrix[1][1],
            }
        )
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_academic_study(config_path: Path, *, folds: int = 5) -> Path:
    """Run the study using train only for CV and validation for final comparison."""
    if folds < 3:
        raise ValueError("academic study requires at least three folds")
    config = load_baseline_config(config_path)
    data = load_development_data(config)
    identity = {
        "study_version": STUDY_VERSION,
        "config_sha256": config.canonical_sha256,
        "folds": folds,
        "seed": config.raw["random_seed"],
    }
    study_id = (
        "academic-study-"
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    destination = config.run_root.parent / "academic-study" / study_id
    if destination.exists():
        return destination

    models: dict[str, Any] = {}
    prediction_frame = pd.DataFrame(
        {"ID": data.validation.identifiers, "target": data.validation.target}
    )
    oof_frame = pd.DataFrame(
        {"ID": data.train.identifiers, "target": data.train.target}
    )
    threshold_frame: list[dict[str, Any]] = []
    for name in MODEL_NAMES:

        def factory(model_name: str = name) -> Pipeline:
            return build_models(config)[model_name]

        cv_results, out_of_fold = _cross_validate(
            data,
            factory,
            seed=cast(int, config.raw["random_seed"]),
            folds=folds,
        )
        fitted = factory()
        fitted.fit(data.train.features, data.train.target)
        validation_probability = _positive_probability(fitted, data.validation.features)
        validation_metrics = binary_classification_metrics(
            data.validation.target, validation_probability, threshold=0.5
        )
        oof_frame[f"{name}_oof_probability"] = out_of_fold
        prediction_frame[f"{name}_validation_probability"] = validation_probability
        threshold_frame.extend(
            {"model": name, **row}
            for row in _threshold_rows(data.validation.target, validation_probability)
        )
        models[name] = {
            "cross_validation": cv_results,
            "validation": validation_metrics,
        }

    calibrated = CalibratedClassifierCV(
        estimator=build_models(config)["lightgbm"], method="sigmoid", cv=3, n_jobs=1
    )
    calibrated.fit(data.train.features, data.train.target)
    calibrated_probability = _positive_probability(calibrated, data.validation.features)
    models["lightgbm_calibrated"] = {
        "validation": binary_classification_metrics(
            data.validation.target, calibrated_probability, threshold=0.5
        )
    }
    prediction_frame["lightgbm_calibrated_validation_probability"] = (
        calibrated_probability
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".academic-study-", dir=destination.parent
    ) as temp:
        staging = Path(temp)
        _write_json(
            staging / "study-results.json",
            {
                "study_version": STUDY_VERSION,
                "study_id": study_id,
                "authorized_use": "academic_baseline_only",
                "test_status": "unopened",
                "identity": identity,
                "models": models,
                "claims_not_made": ["winner", "champion", "production_validity"],
            },
        )
        oof_frame.to_csv(
            staging / "oof-predictions.csv", index=False, lineterminator="\n"
        )
        prediction_frame.to_csv(
            staging / "validation-predictions.csv", index=False, lineterminator="\n"
        )
        pd.DataFrame(threshold_frame).to_csv(
            staging / "threshold-sweep.csv", index=False, lineterminator="\n"
        )
        manifest = {
            "study_id": study_id,
            "study_results": {
                "path": "study-results.json",
                "sha256": sha256_file(staging / "study-results.json"),
            },
            "oof_predictions": {
                "path": "oof-predictions.csv",
                "sha256": sha256_file(staging / "oof-predictions.csv"),
            },
            "validation_predictions": {
                "path": "validation-predictions.csv",
                "sha256": sha256_file(staging / "validation-predictions.csv"),
            },
            "threshold_sweep": {
                "path": "threshold-sweep.csv",
                "sha256": sha256_file(staging / "threshold-sweep.csv"),
            },
        }
        _write_json(staging / "study-manifest.json", manifest)
        for artifact in staging.iterdir():
            artifact.chmod(0o444)
        try:
            staging.rename(destination)
        except FileExistsError:
            return destination
    return destination
