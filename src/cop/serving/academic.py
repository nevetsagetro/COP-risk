"""Reusable read-only service for the local academic baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.metrics import roc_curve  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from cop.evaluation.academic import run_academic_study
from cop.evaluation.calibration import calibration_bins
from cop.evaluation.model_lab import run_model_lab
from cop.evaluation.policy import capacity_metrics
from cop.features.uci import UCI_APPROVED_FEATURES
from cop.training.config import BaselineConfig, load_baseline_config
from cop.training.uci_baseline import (
    MODEL_NAMES,
    load_development_data,
    train_development,
)


@dataclass(frozen=True)
class AcademicArtifacts:
    config: BaselineConfig
    run_directory: Path
    results: dict[str, Any]
    models: dict[str, Pipeline]
    study_directory: Path
    study_results: dict[str, Any]
    validation_predictions: pd.DataFrame
    validation_features: pd.DataFrame
    validation_target: npt.NDArray[np.int64]


@lru_cache(maxsize=1)
def load_academic_artifacts(config_path: str) -> AcademicArtifacts:
    """Load or create local academic artifacts without opening the test split."""
    config = load_baseline_config(Path(config_path))
    run_directory = train_development(Path(config_path))
    manifest = json.loads(
        (run_directory / "run-manifest.json").read_text(encoding="utf-8")
    )
    results = json.loads(
        (run_directory / "validation-results.json").read_text(encoding="utf-8")
    )
    models = {
        name: joblib.load(run_directory / manifest["models"][name]["artifact"]["path"])
        for name in MODEL_NAMES
    }
    if not all(isinstance(model, Pipeline) for model in models.values()):
        raise TypeError("Academic artifacts must contain sklearn pipelines")
    study_directory = run_academic_study(Path(config_path))
    study_results = json.loads(
        (study_directory / "study-results.json").read_text(encoding="utf-8")
    )
    development = load_development_data(config)
    return AcademicArtifacts(
        config=config,
        run_directory=run_directory,
        results=results,
        models=models,
        study_directory=study_directory,
        study_results=study_results,
        validation_predictions=pd.read_csv(
            run_directory / "validation-predictions.csv"
        ),
        validation_features=development.validation.features.reset_index(drop=True),
        validation_target=development.validation.target,
    )


@lru_cache(maxsize=2)
def load_model_lab_results(config_path: str) -> dict[str, Any]:
    """Run the explicit academic lab once per configuration and cache its report."""
    return run_model_lab(Path(config_path), folds=3)


class AcademicService:
    """Application-facing operations over the frozen academic artifacts."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path.resolve()

    @property
    def artifacts(self) -> AcademicArtifacts:
        return load_academic_artifacts(str(self._config_path))

    def overview(self) -> dict[str, Any]:
        artifacts = self.artifacts
        split_files = artifacts.config.raw["splits"]["development_files"]
        return {
            "title": "COP · Academic Credit-Risk Lab",
            "description": (
                "Local demo of an academic model estimating the probability "
                "of a default recorded next month."
            ),
            "target_event": "default recorded next month",
            "authorized_use": "academic_baseline_only",
            "test_status": "unopened",
            "models": list(MODEL_NAMES),
            "features": len(UCI_APPROVED_FEATURES),
            "run_id": artifacts.run_directory.name,
            "study_id": artifacts.study_directory.name,
            "disclaimer": "Not approved for real credit decisions.",
            "journey": {
                "dataset": {
                    "name": "UCI Default of Credit Card Clients",
                    "rows": 30000,
                    "approved_features": len(UCI_APPROVED_FEATURES),
                    "target": "default_payment_next_month",
                    "source": "UCI Machine Learning Repository",
                },
                "data_contract": {
                    "missing_policy": "fail",
                    "audit_only_attributes": "physically separated and excluded",
                    "use": "academic baseline only",
                },
                "splits": {
                    "train": int(split_files["train"]["rows"]),
                    "validation": int(split_files["validation"]["rows"]),
                    "test": 4500,
                    "test_status": "unopened",
                },
                "selection": {
                    "models": ["Logistic Regression", "LightGBM", "KNN"],
                    "primary_metric": "Average Precision",
                    "threshold_method": "F1 on train out-of-fold predictions",
                },
            },
        }

    def metrics(self) -> dict[str, Any]:
        artifacts = self.artifacts
        rows: list[dict[str, Any]] = []
        for name, value in artifacts.results["models"].items():
            rows.append(
                {
                    "model": name,
                    "roc_auc": value["roc_auc"],
                    "average_precision": value["average_precision"],
                    "precision": value["precision"],
                    "recall": value["recall"],
                    "f1": value["f1"],
                    "brier_score": value["brier_score"],
                }
            )
        return {
            "validation": rows,
            "cross_validation": self._cross_validation_metrics(),
            "explanations": {
                "precision": "Of all alerts, how many are observed defaults.",
                "recall": "Of all observed defaults, how many we find.",
                "f1": "Balance between precision and recall.",
                "roc_auc": "Ability to rank cases better than random.",
                "brier_score": "Distance between estimated probabilities and outcomes.",
            },
        }

    def _cross_validation_metrics(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for name, value in self.artifacts.study_results["models"].items():
            aggregate = value.get("cross_validation", {}).get("aggregate")
            if aggregate:
                rows.append(
                    {
                        "model": name,
                        "roc_auc_mean": aggregate["roc_auc"]["mean"],
                        "roc_auc_std": aggregate["roc_auc"]["std"],
                    }
                )
        return rows

    def roc(self) -> dict[str, Any]:
        predictions = self.artifacts.validation_predictions
        curves: list[dict[str, Any]] = []
        for name in MODEL_NAMES:
            fpr, tpr, thresholds = roc_curve(
                predictions["target"],
                predictions[f"{name}_probability"],
                drop_intermediate=False,
            )
            finite = np.isfinite(thresholds)
            points = [
                {
                    "fpr": float(x),
                    "tpr": float(y),
                    "threshold": float(threshold),
                }
                for x, y, threshold in zip(
                    fpr[finite], tpr[finite], thresholds[finite], strict=True
                )
            ]
            knee_index = int(np.argmax(tpr - fpr))
            knee = {
                "fpr": float(fpr[knee_index]),
                "tpr": float(tpr[knee_index]),
                "threshold": float(thresholds[knee_index])
                if np.isfinite(thresholds[knee_index])
                else None,
            }
            curves.append({"model": name, "points": points, "knee": knee})
        return {
            "curves": curves,
            "x_label": "Allowed false alarms",
            "y_label": "Risk cases found",
            "note": (
                "Each point changes the alert threshold; the knee is an approximation."
            ),
        }

    def probability_distribution(self) -> dict[str, Any]:
        predictions = self.artifacts.validation_predictions
        distributions: list[dict[str, Any]] = []
        bins = np.linspace(0, 1, 21)
        for name in MODEL_NAMES:
            counts, edges = np.histogram(predictions[f"{name}_probability"], bins=bins)
            distributions.append(
                {
                    "model": name,
                    "bins": [float(value) for value in edges[:-1]],
                    "counts": [int(value) for value in counts],
                    "highest_bin": int(np.argmax(counts)),
                }
            )
        return {
            "distributions": distributions,
            "threshold": 0.5,
            "note": "The tallest bar shows case concentration, not greater risk.",
        }

    def calibration(self, bins: int = 10) -> dict[str, Any]:
        """Return validation calibration bins without recalibrating models."""
        predictions = self.artifacts.validation_predictions
        target = predictions["target"].to_numpy(dtype=np.int64)
        return {
            "bins": bins,
            "models": [
                {
                    "model": name,
                    "points": calibration_bins(
                        target,
                        predictions[f"{name}_probability"].to_numpy(dtype=np.float64),
                        bins=bins,
                    ),
                }
                for name in MODEL_NAMES
            ],
            "reference": (
                "Perfect calibration follows observed rate = predicted probability."
            ),
            "note": (
                "Validation-only calibration evidence. Brier score summarizes the "
                "same probability error; this chart shows where it occurs."
            ),
            "test_status": "unopened",
        }

    def examples(self, limit: int = 6) -> dict[str, Any]:
        """Return public anonymized validation cases for interactive demos."""
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        artifacts = self.artifacts
        positive = np.flatnonzero(artifacts.validation_target == 1)
        negative = np.flatnonzero(artifacts.validation_target == 0)
        selected = list(negative[: limit // 2]) + list(positive[: limit - limit // 2])
        examples = []
        for position, index in enumerate(selected, start=1):
            row = artifacts.validation_features.iloc[int(index)]
            payment_statuses = [
                int(row[name])
                for name in ("PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6")
            ]
            maximum_delay = max(payment_statuses)
            if maximum_delay <= 0:
                history_summary = (
                    "no payment delays in the six months before the outcome"
                )
            else:
                history_summary = (
                    f"a maximum payment delay of {maximum_delay} months "
                    "in the six months before the outcome"
                )
            observed = int(artifacts.validation_target[int(index)])
            observed_summary = (
                "a default was recorded the following month"
                if observed == 1
                else "no default was recorded the following month"
            )
            examples.append(
                {
                    "case_id": f"UCI-VAL-{position:04d}",
                    "naming_convention": (
                        "UCI-VAL-#### = UCI dataset, validation split, anonymous number"
                    ),
                    "observed_default_next_month": observed,
                    "summary": (
                        "This public validation record shows "
                        f"{history_summary}; "
                        f"{observed_summary}."
                    ),
                    "features": {
                        name: float(row[name]) for name in UCI_APPROVED_FEATURES
                    },
                }
            )
        return {
            "cases": examples,
            "note": (
                "Public anonymized cases from the validation split. The observed "
                "outcome is only for comparison after prediction."
            ),
        }

    def threshold_sweep(self, model: str) -> dict[str, Any]:
        if model not in MODEL_NAMES:
            raise ValueError(f"Unknown model: {model}")
        frame = pd.read_csv(self.artifacts.study_directory / "threshold-sweep.csv")
        selected = frame[frame["model"] == model].copy()
        records = selected.to_dict(orient="records")
        best = selected.loc[selected["f1"].idxmax()].to_dict()
        return {
            "model": model,
            "points": records,
            "best_f1": best,
            "note": (
                "Raising the threshold usually increases precision and reduces recall."
            ),
        }

    def model_lab(self) -> dict[str, Any]:
        """Return the reproducible tuning report without opening the test."""
        return load_model_lab_results(str(self._config_path))

    def capacity_policy(self, capacity: float = 0.10) -> dict[str, Any]:
        """Compare top-capacity review policies on validation predictions."""
        predictions = self.artifacts.validation_predictions
        target = predictions["target"].to_numpy(dtype=np.int64)
        models = [
            {
                "model": name,
                **capacity_metrics(
                    target,
                    predictions[f"{name}_probability"].to_numpy(dtype=np.float64),
                    capacity=capacity,
                ),
            }
            for name in MODEL_NAMES
        ]
        return {
            "capacity": capacity,
            "models": models,
            "selection": (
                "Rank validation cases by predicted probability and review only "
                "the highest-risk fraction."
            ),
            "note": (
                "This is a validation policy comparison, not a production credit "
                "decision or a model promotion."
            ),
            "test_status": "unopened",
        }

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        expected = set(UCI_APPROVED_FEATURES)
        received = set(features)
        if received != expected:
            missing = sorted(expected - received)
            unknown = sorted(received - expected)
            raise ValueError(f"Invalid features; missing={missing}, unknown={unknown}")
        frame = pd.DataFrame(
            [[features[name] for name in UCI_APPROVED_FEATURES]],
            columns=list(UCI_APPROVED_FEATURES),
        )
        if not np.isfinite(frame.to_numpy(dtype=float)).all():
            raise ValueError("Feature values must be finite")
        models = self.artifacts.models
        predictions = [
            {
                "model": name,
                "probability": float(model.predict_proba(frame)[0, 1]),
                "descriptive_threshold": 0.5,
            }
            for name, model in models.items()
        ]
        return {
            "predictions": predictions,
            "note": "Academic estimate, not a credit decision.",
        }

    def predict_example(
        self, case_id: str, overrides: dict[str, float]
    ) -> dict[str, Any]:
        """Predict a validation case after applying only explicit overrides."""
        cases = self.examples()["cases"]
        case = next((item for item in cases if item["case_id"] == case_id), None)
        if case is None:
            raise ValueError(f"Unknown academic validation case: {case_id}")
        unknown = set(overrides) - set(UCI_APPROVED_FEATURES)
        if unknown:
            raise ValueError(f"Unknown override features: {sorted(unknown)}")
        baseline_features = dict(case["features"])
        scenario_features = dict(baseline_features)
        scenario_features.update(overrides)
        baseline = self.predict(baseline_features)
        result = self.predict(scenario_features)
        baseline_by_model = {
            row["model"]: float(row["probability"]) for row in baseline["predictions"]
        }
        probability_changes = []
        for row in result["predictions"]:
            baseline_probability = baseline_by_model[row["model"]]
            scenario_probability = float(row["probability"])
            absolute_change = scenario_probability - baseline_probability
            relative_change_pct = (
                None
                if baseline_probability == 0
                else absolute_change / baseline_probability * 100
            )
            probability_changes.append(
                {
                    "model": row["model"],
                    "baseline_probability": baseline_probability,
                    "scenario_probability": scenario_probability,
                    "absolute_change": absolute_change,
                    "relative_change_pct": relative_change_pct,
                }
            )
        result["case_id"] = case_id
        result["observed_default_next_month"] = case["observed_default_next_month"]
        result["overrides"] = overrides
        result["baseline_predictions"] = baseline["predictions"]
        result["scenario_predictions"] = result["predictions"]
        result["probability_changes"] = probability_changes
        return result
