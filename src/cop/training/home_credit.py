"""Train-only static Home Credit academic baselines."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.impute import SimpleImputer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import (  # type: ignore[import-untyped]
    OneHotEncoder,
    StandardScaler,
)

from cop.data.hashing import sha256_file
from cop.data.home_credit import (
    HOME_CREDIT_AUDIT_ONLY_COLUMNS,
    HOME_CREDIT_FEATURE_VERSION_V0,
    HOME_CREDIT_ID,
    HOME_CREDIT_SPLIT_SEED,
    HOME_CREDIT_TARGET,
)
from cop.evaluation.binary import binary_classification_metrics

HOME_CREDIT_MODEL_NAMES = ("logistic_regression", "lightgbm")
HOME_CREDIT_TRAINING_VERSION = 1
HOME_CREDIT_EXPERIMENT_SEED = 42


@dataclass(frozen=True)
class HomeCreditData:
    train: pd.DataFrame
    validation: pd.DataFrame
    feature_columns: tuple[str, ...]


def load_static_development_data(snapshot_directory: Path) -> HomeCreditData:
    """Load train and validation only; the static test file is never read."""
    train = pd.read_parquet(snapshot_directory / "train.parquet")
    validation = pd.read_parquet(snapshot_directory / "validation.parquet")
    for name, frame in (("train", train), ("validation", validation)):
        if frame[HOME_CREDIT_ID].duplicated().any():
            raise ValueError(f"{name} contains duplicate entity IDs")
        if set(frame["split"]) != {name}:
            raise ValueError(f"{name} contains an unexpected split label")
    if set(train[HOME_CREDIT_ID]) & set(validation[HOME_CREDIT_ID]):
        raise ValueError("entity ID crosses train and validation")
    feature_columns = tuple(
        column
        for column in train.columns
        if column not in {HOME_CREDIT_ID, HOME_CREDIT_TARGET, "split"}
    )
    if set(HOME_CREDIT_AUDIT_ONLY_COLUMNS) & set(feature_columns):
        raise ValueError("an audit-only column appears in model features")
    if not feature_columns:
        raise ValueError("static snapshot contains no model features")
    if tuple(validation.columns) != tuple(train.columns):
        raise ValueError("train and validation schemas differ")
    return HomeCreditData(train, validation, feature_columns)


def _preprocessor(features: pd.DataFrame, *, scale_numeric: bool) -> ColumnTransformer:
    categorical = [column for column in features if features[column].dtype == "object"]
    numeric = [column for column in features if column not in categorical]
    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore", dtype=np.float64),
                        ),
                    ]
                ),
                categorical,
            ),
            ("numeric", Pipeline(steps=numeric_steps), numeric),
        ],
        remainder="drop",
    )


def build_home_credit_models(data: HomeCreditData) -> dict[str, Pipeline]:
    numeric_features = data.train.loc[:, list(data.feature_columns)]
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", _preprocessor(numeric_features, scale_numeric=True)),
                (
                    "classifier",
                    LogisticRegression(
                        C=0.5,
                        class_weight=None,
                        max_iter=500,
                        solver="liblinear",
                        random_state=HOME_CREDIT_EXPERIMENT_SEED,
                    ),
                ),
            ]
        ),
        "lightgbm": Pipeline(
            steps=[
                ("preprocessor", _preprocessor(numeric_features, scale_numeric=False)),
                (
                    "classifier",
                    LGBMClassifier(
                        learning_rate=0.05,
                        n_estimators=250,
                        num_leaves=31,
                        class_weight=None,
                        n_jobs=1,
                        random_state=HOME_CREDIT_EXPERIMENT_SEED,
                        verbosity=-1,
                    ),
                ),
            ]
        ),
    }


def _positive_probability(
    model: Pipeline, features: pd.DataFrame
) -> npt.NDArray[np.float64]:
    probabilities = np.asarray(model.predict_proba(features), dtype=np.float64)
    classes = np.asarray(model.classes_)
    positive = np.flatnonzero(classes == 1)
    if probabilities.ndim != 2 or len(positive) != 1:
        raise ValueError("model does not expose one positive-class probability")
    return probabilities[:, int(positive[0])]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def run_home_credit_baseline(
    snapshot_directory: Path,
    *,
    run_directory: Path | None = None,
) -> Path:
    """Fit static candidates on train and evaluate them on validation only."""
    snapshot_directory = snapshot_directory.resolve(strict=True)
    manifest_path = snapshot_directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data = load_static_development_data(snapshot_directory)
    identity = {
        "training_version": HOME_CREDIT_TRAINING_VERSION,
        "snapshot_sha256": sha256_file(manifest_path),
        "models": HOME_CREDIT_MODEL_NAMES,
        "feature_version": manifest.get(
            "feature_version", HOME_CREDIT_FEATURE_VERSION_V0
        ),
        "split_seed": manifest.get("split_seed", HOME_CREDIT_SPLIT_SEED),
        "experiment_seed": HOME_CREDIT_EXPERIMENT_SEED,
    }
    run_id = (
        "home-credit-static-"
        + hashlib.sha256(_canonical_json(identity)).hexdigest()[:16]
    )
    destination = (run_directory or Path("runs/home-credit-static")) / run_id
    if destination.exists():
        return destination

    train_features = data.train.loc[:, list(data.feature_columns)]
    validation_features = data.validation.loc[:, list(data.feature_columns)]
    train_target = data.train[HOME_CREDIT_TARGET].to_numpy(dtype=np.int64)
    validation_target = data.validation[HOME_CREDIT_TARGET].to_numpy(dtype=np.int64)
    prediction_frame = pd.DataFrame(
        {
            HOME_CREDIT_ID: data.validation[HOME_CREDIT_ID],
            HOME_CREDIT_TARGET: validation_target,
        }
    )
    results: dict[str, Any] = {}
    models = build_home_credit_models(data)
    destination.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        model.fit(train_features, train_target)
        probability = _positive_probability(model, validation_features)
        results[name] = {
            "parameters": cast(Any, model.named_steps["classifier"]).get_params(),
            "validation": binary_classification_metrics(
                validation_target, probability, threshold=0.5
            ),
        }
        prediction_frame[f"{name}_probability"] = probability
        joblib.dump(model, destination / f"{name}.joblib")
    prediction_frame.to_csv(
        destination / "validation-predictions.csv", index=False, lineterminator="\n"
    )
    report = {
        "training_version": HOME_CREDIT_TRAINING_VERSION,
        "feature_version": manifest.get(
            "feature_version", HOME_CREDIT_FEATURE_VERSION_V0
        ),
        "split_seed": manifest.get("split_seed", HOME_CREDIT_SPLIT_SEED),
        "experiment_seed": HOME_CREDIT_EXPERIMENT_SEED,
        "authorized_use": "academic_static_benchmark_only",
        "test_status": "unopened",
        "dataset_id": manifest["dataset_id"],
        "snapshot_manifest_sha256": sha256_file(manifest_path),
        "target": HOME_CREDIT_TARGET,
        "entity_key": HOME_CREDIT_ID,
        "feature_columns": list(data.feature_columns),
        "fit_split": "train",
        "evaluation_split": "validation",
        "static_limitation": (
            "The source archive has no application timestamp; results do not "
            "support temporal stability or production claims."
        ),
        "models": results,
        "claims_not_made": ["temporal_stability", "champion", "production_validity"],
    }
    (destination / "results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return destination
