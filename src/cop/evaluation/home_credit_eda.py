"""Offline descriptive EDA for the static Home Credit academic snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cop.data.home_credit import HOME_CREDIT_FEATURE_VERSION_V0, HOME_CREDIT_TARGET

EDA_DISTRIBUTION_FEATURES = (
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "BUREAU_CREDIT_SUM",
    "BUREAU_DEBT_SUM",
    "PREVIOUS_CREDIT_SUM",
    "INSTALLMENT_SHORTFALL_SUM",
    "INSTALLMENT_PAYMENT_SUM",
)

EDA_CORRELATION_FEATURES = (
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "REGION_POPULATION_RELATIVE",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "BUREAU_CREDIT_SUM",
    "BUREAU_DEBT_SUM",
    "PREVIOUS_CREDIT_SUM",
    "INSTALLMENT_SHORTFALL_SUM",
    "INSTALLMENT_PAYMENT_SUM",
)


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series[Any]:
    return pd.to_numeric(frame[column], errors="coerce")


def _summary(series: pd.Series[Any]) -> dict[str, float | int | None]:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return {
            "cases": 0,
            "missing": int(numeric.isna().sum()),
            "mean": None,
            "median": None,
            "p05": None,
            "p95": None,
        }
    return {
        "cases": int(numeric.notna().sum()),
        "missing": int(numeric.isna().sum()),
        "mean": float(numeric.mean()),
        "median": float(numeric.median()),
        "p05": float(numeric.quantile(0.05)),
        "p95": float(numeric.quantile(0.95)),
    }


def _feature_missingness(
    train: pd.DataFrame, features: list[str]
) -> list[dict[str, Any]]:
    rows = []
    for feature in features:
        missing = int(train[feature].isna().sum())
        rows.append(
            {
                "feature": feature,
                "missing_cases": missing,
                "missing_rate": float(missing / len(train)) if len(train) else 0.0,
                "dtype": str(train[feature].dtype),
            }
        )
    return sorted(rows, key=lambda row: (-row["missing_rate"], row["feature"]))


def _distributions(train: pd.DataFrame, features: list[str]) -> list[dict[str, Any]]:
    rows = []
    for feature in features:
        numeric = _numeric(train, feature)
        values = {
            str(target): _summary(
                train.loc[train[HOME_CREDIT_TARGET] == target, feature]
            )
            for target in (0, 1)
        }
        median_zero = values["0"]["median"]
        median_one = values["1"]["median"]
        iqr = float(numeric.quantile(0.75) - numeric.quantile(0.25))
        delta = (
            float(median_one - median_zero)
            if median_zero is not None and median_one is not None
            else None
        )
        rows.append(
            {
                "feature": feature,
                "by_target": values,
                "contrast": {
                    "median_difference_target_1_minus_0": delta,
                    "iqr": iqr,
                    "iqr_scaled_difference": (
                        float(delta / iqr) if delta is not None and iqr else None
                    ),
                },
            }
        )
    return rows


def _correlations(train: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    numeric = train.loc[:, features].apply(pd.to_numeric, errors="coerce")
    matrix = numeric.corr(method="pearson").fillna(0.0)
    pairs: list[dict[str, Any]] = []
    for index, left in enumerate(features):
        for right in features[index + 1 :]:
            value = float(matrix.loc[left, right])
            pairs.append(
                {
                    "left": left,
                    "right": right,
                    "correlation": value,
                    "absolute": abs(value),
                }
            )
    pairs.sort(key=lambda row: (-row["absolute"], row["left"], row["right"]))
    return {
        "method": "Pearson correlation",
        "population": "train split only",
        "selection_rule": (
            "Fixed numeric model-input subset covering application and aggregate "
            "families; no target-based ranking."
        ),
        "features": features,
        "matrix": [[float(value) for value in row] for row in matrix.to_numpy()],
        "strongest_pairs": pairs[:12],
    }


def build_home_credit_eda_report(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build a JSON-safe EDA report without loading or inspecting the final test."""
    model_features = [str(value) for value in manifest["model_features"]]
    available = [feature for feature in model_features if feature in train.columns]
    numeric_distribution_features = [
        feature for feature in EDA_DISTRIBUTION_FEATURES if feature in available
    ]
    correlation_features = [
        feature for feature in EDA_CORRELATION_FEATURES if feature in available
    ]
    snapshot_counts = {
        str(key): int(value) for key, value in manifest["class_counts"].items()
    }
    snapshot_rows = int(manifest["rows"])
    validation_target = pd.to_numeric(validation[HOME_CREDIT_TARGET], errors="coerce")
    return {
        "artifact_version": 1,
        "dataset_id": manifest["dataset_id"],
        "feature_version": HOME_CREDIT_FEATURE_VERSION_V0,
        "authorized_use": manifest["authorized_use"],
        "target": HOME_CREDIT_TARGET,
        "test_status": "unopened",
        "population": {
            "snapshot_rows": snapshot_rows,
            "train_rows": int(len(train)),
            "validation_rows": int(len(validation)),
            "analysis_split": "train",
            "validation_summary_split": "validation",
            "final_test_rows": int(manifest["files"]["test"]["rows"]),
            "final_test_used": False,
        },
        "prevalence": {
            "snapshot": {
                "cases": snapshot_rows,
                "positive_cases": snapshot_counts.get("1", 0),
                "rate": float(snapshot_counts.get("1", 0) / snapshot_rows),
                "source": "manifest class counts; descriptive only",
            },
            "validation": {
                "cases": int(validation_target.notna().sum()),
                "positive_cases": int(validation_target.sum()),
                "rate": float(validation_target.mean()),
                "source": "validation target summary; not used for feature selection",
            },
        },
        "missingness": {
            "population": "train split",
            "features": _feature_missingness(train, available),
        },
        "distributions": {
            "population": "train split",
            "target_groups": [0, 1],
            "features": _distributions(train, numeric_distribution_features),
        },
        "correlations": _correlations(train, correlation_features),
        "audit_only": {
            "columns": [str(value) for value in manifest["audit_only_columns"]],
            "explanation": (
                "Excluded physically from model-input EDA and model features; no "
                "decision-input claim is made."
            ),
        },
        "reproducibility": {
            "dataset_fingerprint": manifest["logical_sha256"],
            "split_seed": manifest.get("split_seed", 42),
            "split_strategy": manifest["static_split_strategy"],
            "correlation_method": "Pearson",
        },
        "limitations": [
            "Descriptive association is not feature importance or causality.",
            (
                "The source archive has no defensible application timestamp, so "
                "temporal stability is not evaluated."
            ),
            "The final test is unopened and excluded from feature-level analysis.",
        ],
    }


def write_home_credit_eda_report(snapshot_directory: Path, output: Path) -> Path:
    """Materialize the deterministic EDA report from train and validation only."""
    snapshot_directory = snapshot_directory.resolve()
    manifest = json.loads(
        (snapshot_directory / "manifest.json").read_text(encoding="utf-8")
    )
    train = pd.read_parquet(snapshot_directory / "train.parquet")
    validation = pd.read_parquet(snapshot_directory / "validation.parquet")
    report = build_home_credit_eda_report(train, validation, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output
