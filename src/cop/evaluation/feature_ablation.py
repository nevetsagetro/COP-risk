"""Feature-family ablation for the Home Credit academic benchmark."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from cop.evaluation.binary import binary_classification_metrics
from cop.evaluation.home_credit import _build_candidate, _candidate_cv
from cop.training.home_credit import (
    HOME_CREDIT_EXPERIMENT_SEED,
    HomeCreditData,
    _positive_probability,
    load_static_development_data,
)

FEATURE_ABLATION_PARAMETERS: dict[str, Any] = {
    "learning_rate": 0.05,
    "n_estimators": 350,
    "num_leaves": 31,
}


def feature_families(
    baseline_columns: tuple[str, ...], challenger_columns: tuple[str, ...]
) -> dict[str, tuple[str, ...]]:
    """Return reproducible feature-family additions relative to the baseline."""
    additions = [
        column for column in challenger_columns if column not in baseline_columns
    ]
    baseline = tuple(baseline_columns)
    return {
        "baseline": baseline,
        "financial_ratios": baseline
        + tuple(column for column in additions if column.startswith("APP_")),
        "external_score_quality": baseline
        + tuple(column for column in additions if column.startswith("EXT_SOURCE_")),
        "credit_history_behavior": baseline
        + tuple(
            column
            for column in additions
            if column.startswith(("BUREAU_", "PREVIOUS_", "INSTALLMENT_"))
        ),
        "all_v2": tuple(challenger_columns),
    }


def _evaluate(
    data: HomeCreditData,
    columns: tuple[str, ...],
    *,
    folds: int,
) -> dict[str, Any]:
    candidate_data = replace(data, feature_columns=columns)
    cv = _candidate_cv(
        candidate_data,
        "lightgbm",
        FEATURE_ABLATION_PARAMETERS,
        folds=folds,
    )
    features = data.train.loc[:, list(columns)]
    validation_features = data.validation.loc[:, list(columns)]
    target = data.train["TARGET"].to_numpy(dtype=int)
    validation_target = data.validation["TARGET"].to_numpy(dtype=int)
    model = _build_candidate(candidate_data, "lightgbm", FEATURE_ABLATION_PARAMETERS)
    model.fit(features, target)
    probability = _positive_probability(model, validation_features)
    return {
        "feature_count": len(columns),
        "added_features": [
            column for column in columns if column not in data.feature_columns
        ],
        "cross_validation": cv["cross_validation"],
        "cross_validation_std": cv["cross_validation_std"],
        "validation": binary_classification_metrics(
            validation_target, probability, threshold=0.5
        ),
    }


def run_feature_ablation(
    baseline_snapshot: Path,
    challenger_snapshot: Path,
    *,
    folds: int = 3,
) -> dict[str, Any]:
    """Compare v2 feature families using one fixed LightGBM candidate."""
    baseline = load_static_development_data(baseline_snapshot)
    challenger = load_static_development_data(challenger_snapshot)
    if not baseline.train["SK_ID_CURR"].equals(challenger.train["SK_ID_CURR"]):
        raise ValueError("baseline and challenger train entities are not aligned")
    if not baseline.validation["SK_ID_CURR"].equals(
        challenger.validation["SK_ID_CURR"]
    ):
        raise ValueError("baseline and challenger validation entities are not aligned")
    families = feature_families(baseline.feature_columns, challenger.feature_columns)
    results = {
        name: _evaluate(challenger, columns, folds=folds)
        for name, columns in families.items()
    }
    return {
        "authorized_use": "academic_static_benchmark_only",
        "test_status": "unopened",
        "fit_split": "train",
        "evaluation_split": "validation",
        "selection_split": "train_cross_validation",
        "primary_metric": "average_precision",
        "folds": folds,
        "experiment_seed": HOME_CREDIT_EXPERIMENT_SEED,
        "model": "lightgbm",
        "parameters": FEATURE_ABLATION_PARAMETERS,
        "feature_versions": {"baseline": "features-v0", "challenger": "features-v2"},
        "hypotheses": {
            "financial_ratios": (
                "Affordability ratios capture scale-adjusted application risk."
            ),
            "external_score_quality": (
                "Score consensus and missingness capture signal quality."
            ),
            "credit_history_behavior": (
                "Historical debt, approval, refusal, and payment behavior add context."
            ),
        },
        "results": results,
    }


def write_feature_ablation(
    baseline_snapshot: Path,
    challenger_snapshot: Path,
    output: Path,
    *,
    folds: int = 3,
) -> Path:
    result = run_feature_ablation(baseline_snapshot, challenger_snapshot, folds=folds)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output
