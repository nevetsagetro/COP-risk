"""Read-only serving facade for the materialized static Home Credit reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from cop.data.home_credit import (
    HOME_CREDIT_FEATURE_VERSION_V0,
    HOME_CREDIT_SPLIT_SEED,
)
from cop.evaluation.calibration import calibration_bins
from cop.training.home_credit import HOME_CREDIT_EXPERIMENT_SEED


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return cast(dict[str, Any], value)


class HomeCreditService:
    """Expose cached local reports; this service never trains or opens test."""

    def __init__(
        self,
        snapshot_directory: Path,
        run_directory: Path,
        comparison_snapshot_directory: Path | None = None,
        comparison_run_directory: Path | None = None,
    ) -> None:
        self._snapshot_directory = snapshot_directory.resolve()
        self._run_directory = run_directory.resolve()
        self._comparison_snapshot_directory = (
            comparison_snapshot_directory.resolve()
            if comparison_snapshot_directory is not None
            else None
        )
        self._comparison_run_directory = (
            comparison_run_directory.resolve()
            if comparison_run_directory is not None
            else None
        )

    def summary(self) -> dict[str, Any]:
        manifest = _json(self._snapshot_directory / "manifest.json")
        baseline = _json(self._run_directory / "results.json")
        model_lab = _json(self._run_directory.parent / "model-lab-results.json")
        policy = _json(self._run_directory.parent / "policy-results.json")
        models = []
        for name, result in cast(dict[str, Any], baseline["models"]).items():
            selected = cast(dict[str, Any], model_lab["models"][name])
            candidates = cast(list[dict[str, Any]], selected["candidates"])
            chosen = next(
                candidate for candidate in candidates if candidate["selected"]
            )
            validation = cast(dict[str, Any], result["validation"])
            models.append(
                {
                    "model": name,
                    "validation": validation,
                    "selected_trial": chosen["trial_id"],
                    "selected_parameters": chosen["parameters"],
                    "cv_average_precision": chosen["cross_validation"][
                        "average_precision"
                    ],
                    "cv_average_precision_std": chosen["cross_validation_std"][
                        "average_precision"
                    ],
                }
            )
        return {
            "dataset": "Home Credit Default Risk",
            "authorized_use": "academic_static_benchmark_only",
            "test_status": "unopened",
            "snapshot": {
                "rows": manifest["rows"],
                "features": len(manifest["model_features"]),
                "train_rows": manifest["files"]["train"]["rows"],
                "validation_rows": manifest["files"]["validation"]["rows"],
                "test_rows": manifest["files"]["test"]["rows"],
                "split_strategy": manifest["static_split_strategy"],
            },
            "models": models,
            "policy": policy,
            "limitation": baseline["static_limitation"],
            "note": (
                "Static academic benchmark only. No temporal stability, champion, "
                "production, or real-credit claim is made."
            ),
        }

    def eda_report(self) -> dict[str, Any]:
        """Expose the cached EDA report without inspecting data at request time."""
        report_path = self._run_directory.parent / "eda-report.json"
        if not report_path.exists():
            raise FileNotFoundError(
                "The Home Credit EDA report has not been materialized"
            )
        return _json(report_path)

    def academic_evidence(self) -> dict[str, Any]:
        """Expose the cached evidence chain used by the Home Credit story."""
        manifest = _json(self._snapshot_directory / "manifest.json")
        baseline = _json(self._run_directory / "results.json")
        model_lab = _json(self._run_directory.parent / "model-lab-results.json")
        policy = _json(self._run_directory.parent / "policy-results.json")
        validation_predictions = pd.read_csv(
            self._run_directory / "validation-predictions.csv"
        )

        feature_columns = [str(value) for value in manifest["model_features"]]
        feature_groups = [
            {
                "id": "application",
                "label": "Application data",
                "source_tables": ["application_train.csv"],
                "features": [
                    feature
                    for feature in feature_columns
                    if not feature.startswith(("BUREAU_", "PREVIOUS_", "INSTALLMENT_"))
                ],
                "explanation": (
                    "Values supplied by the application table at the static snapshot."
                ),
            },
            {
                "id": "bureau",
                "label": "Bureau aggregates",
                "source_tables": ["bureau.csv"],
                "features": [
                    feature
                    for feature in feature_columns
                    if feature.startswith("BUREAU_")
                ],
                "explanation": "Counts and balances aggregated from the bureau table.",
            },
            {
                "id": "previous_application",
                "label": "Previous application aggregates",
                "source_tables": ["previous_application.csv"],
                "features": [
                    feature
                    for feature in feature_columns
                    if feature.startswith("PREVIOUS_")
                ],
                "explanation": (
                    "Historical application counts and amounts aggregated per entity."
                ),
            },
            {
                "id": "installments",
                "label": "Installment payment aggregates",
                "source_tables": ["installments_payments.csv"],
                "features": [
                    feature
                    for feature in feature_columns
                    if feature.startswith("INSTALLMENT_")
                ],
                "explanation": (
                    "Payment count, lateness, shortfall, and amount aggregates."
                ),
            },
        ]

        model_evidence: list[dict[str, Any]] = []
        iterations: list[dict[str, Any]] = []
        for name, payload in cast(dict[str, Any], model_lab["models"]).items():
            candidates = cast(list[dict[str, Any]], payload["candidates"])
            validation = cast(dict[str, Any], baseline["models"][name]["validation"])
            selected = next(
                candidate for candidate in candidates if candidate["selected"]
            )
            baseline_candidate = candidates[0]
            model_evidence.append(
                {
                    "model": name,
                    "selected_trial": selected["trial_id"],
                    "selected_parameters": selected["parameters"],
                    "validation": validation,
                    "selected_validation": payload["selected_validation"],
                    "candidates": candidates,
                    "iteration_comparison": {
                        "baseline_trial": baseline_candidate["trial_id"],
                        "selected_trial": selected["trial_id"],
                        "baseline_average_precision": baseline_candidate[
                            "cross_validation"
                        ]["average_precision"],
                        "selected_average_precision": selected["cross_validation"][
                            "average_precision"
                        ],
                        "average_precision_delta": selected["cross_validation"][
                            "average_precision"
                        ]
                        - baseline_candidate["cross_validation"]["average_precision"],
                        "selection_basis": "train cross-validation Average Precision",
                    },
                }
            )
            for candidate in candidates:
                iterations.append(
                    {
                        "model": name,
                        "iteration_id": candidate["trial_id"],
                        "stage": "selected_candidate"
                        if candidate["selected"]
                        else "candidate",
                        "selected": candidate["selected"],
                        "rank": candidate["rank"],
                        "parameters": candidate["parameters"],
                        "fit_split": "train",
                        "selection_evaluation": (
                            "3-fold stratified cross-validation on train"
                        ),
                        "primary_metric": "average_precision",
                        "cross_validation": candidate["cross_validation"],
                        "cross_validation_std": candidate["cross_validation_std"],
                        "validation": payload["selected_validation"]
                        if candidate["selected"]
                        else None,
                    }
                )

        class_counts = {
            str(key): int(value) for key, value in manifest["class_counts"].items()
        }
        total_rows = int(manifest["rows"])
        policy_models = cast(dict[str, Any], policy["models"])
        lightgbm_policy = cast(list[dict[str, Any]], policy_models["lightgbm"])
        validation_prevalence = float(lightgbm_policy[0]["prevalence"])
        feature_version = str(
            manifest.get("feature_version", HOME_CREDIT_FEATURE_VERSION_V0)
        )
        split_seed = int(manifest.get("split_seed", HOME_CREDIT_SPLIT_SEED))
        experiment_seed = int(
            baseline.get("experiment_seed", HOME_CREDIT_EXPERIMENT_SEED)
        )
        cv_folds = int(model_lab["folds"])
        calibration_models = []
        for name in ("logistic_regression", "lightgbm"):
            calibration_models.append(
                {
                    "model": name,
                    "points": calibration_bins(
                        validation_predictions["TARGET"].to_numpy(),
                        validation_predictions[f"{name}_probability"].to_numpy(),
                        bins=10,
                    ),
                }
            )
        evidence: dict[str, Any] = {
            "dataset": {
                "name": "Home Credit Default Risk",
                "dataset_id": manifest["dataset_id"],
                "source_tables": manifest["source_tables"],
                "target": manifest["target"],
                "entity_key": manifest["entity_key"],
                "rows": total_rows,
                "class_counts": class_counts,
                "overall_prevalence": class_counts.get("1", 0) / total_rows,
                "validation_prevalence": validation_prevalence,
                "authorized_use": manifest["authorized_use"],
                "temporal_status": manifest["temporal_status"],
            },
            "evidence_boundary": {
                "fit_split": baseline["fit_split"],
                "selection_split": model_lab["selection_split"],
                "evaluation_split": baseline["evaluation_split"],
                "test_status": baseline["test_status"],
                "split_strategy": manifest["static_split_strategy"],
                "split_rows": manifest["split_rows"],
            },
            "reproducibility": {
                "feature_version": feature_version,
                "dataset_fingerprint": manifest["logical_sha256"],
                "split_seed": split_seed,
                "experiment_seed": experiment_seed,
                "cross_validation_folds": cv_folds,
                "split_strategy": manifest["static_split_strategy"],
                "human_explanation": (
                    "The seed makes the split and experiment repeatable; it does "
                    "not make the model more accurate. Confidence comes from "
                    "checking whether the result remains stable across folds and "
                    "future seeds."
                ),
            },
            "feature_groups": feature_groups,
            "audit_only": {
                "columns": manifest["audit_only_columns"],
                "explanation": (
                    "Separated from model inputs and not used as decision features."
                ),
            },
            "models": model_evidence,
            "iterations": iterations,
            "classical_benchmark": self._classical_benchmark(),
            "deep_learning": self._deep_learning_benchmark(),
            "policy": {
                "capacities": policy["capacities"],
                "models": policy["models"],
                "test_status": policy["test_status"],
            },
            "calibration": {
                "status": "available",
                "split": "validation",
                "bins": 10,
                "models": calibration_models,
                "reason": (
                    "Bins are computed from cached validation probabilities; the "
                    "final test remains unopened."
                ),
            },
            "interpretation": {
                "average_precision": (
                    "Ranks positive target cases above negative cases, with more "
                    "weight on precision when positives are uncommon."
                ),
                "roc_auc": (
                    "Measures ranking separation across thresholds; it is not a "
                    "probability of default."
                ),
                "brier_score": "Measures squared probability error; lower is better.",
                "precision_at_capacity": (
                    "Among reviewed cases, the fraction matching the observed target."
                ),
                "recall_at_capacity": (
                    "Among observed target-positive cases, the fraction found by "
                    "the review budget."
                ),
                "static_warning": baseline["static_limitation"],
            },
            "future_iteration_contract": {
                "required_fields": [
                    "iteration_id",
                    "model",
                    "parameters",
                    "fit_split",
                    "primary_metric",
                    "validation",
                    "decision",
                ],
                "rule": (
                    "A new iteration is compared with the recorded evidence; it is "
                    "not promoted automatically."
                ),
            },
            "test_status": "unopened",
            "authorized_use": "academic_static_benchmark_only",
        }
        evidence["feature_comparison"] = self._feature_comparison()
        return evidence

    def _classical_benchmark(self) -> dict[str, Any]:
        """Expose the cached classical tuning evidence without training on request."""
        report_paths = [self._run_directory.parent / "model-benchmark-v2.json"]
        if self._comparison_run_directory is not None:
            report_paths.append(
                self._comparison_run_directory.parent / "model-benchmark-v2.json"
            )
        report_path = next((path for path in report_paths if path.exists()), None)
        if report_path is None:
            return {
                "status": "unavailable",
                "reason": "The classical benchmark has not been materialized.",
            }
        report = _json(report_path)
        models = []
        for name, payload in cast(dict[str, Any], report["models"]).items():
            validation = payload.get("validation")
            cv = payload.get("cross_validation")
            models.append(
                {
                    "model": name,
                    "status": payload.get("status", "available"),
                    "validation_average_precision": (
                        validation.get("average_precision")
                        if isinstance(validation, dict)
                        else None
                    ),
                    "cross_validation_average_precision": (
                        cv.get("average_precision") if isinstance(cv, dict) else None
                    ),
                    "cross_validation_std": payload.get("cross_validation_std"),
                    "parameters": payload.get("parameters", {}),
                    "search": payload.get("search", "fixed challenger"),
                    "trials": payload.get("trial_history", []),
                    "reason": payload.get("reason"),
                }
            )
        return {
            "status": "available",
            "primary_metric": report["primary_metric"],
            "fit_split": report["fit_split"],
            "selection_split": report["selection_split"],
            "evaluation_split": report["evaluation_split"],
            "experiment_seed": report["experiment_seed"],
            "cross_validation_folds": report["cross_validation_folds"],
            "models": models,
            "test_status": report["test_status"],
            "human_explanation": (
                "Optuna searches LightGBM parameters inside train cross-validation. "
                "Validation is checked after selection, while CatBoost and XGBoost "
                "act as fixed classical challengers. The highest validation score "
                "is evidence for this split, not an automatic promotion."
            ),
        }

    def _deep_learning_benchmark(self) -> dict[str, Any]:
        """Expose the cached neural benchmark without importing or training it."""
        report_paths: list[Path] = []
        for run_directory in (
            self._run_directory,
            self._comparison_run_directory,
        ):
            if run_directory is not None:
                report_paths.append(
                    run_directory.parent
                    / "deep-learning"
                    / "deep-learning-results.json"
                )
        report_path = next((path for path in report_paths if path.exists()), None)
        if report_path is None:
            return {
                "status": "unavailable",
                "reason": "The deep-learning benchmark has not been materialized.",
            }
        report = _json(report_path)
        return {
            "status": report.get("status", "available"),
            "test_status": report.get("test_status", "unopened"),
            "feature_version": report.get("feature_version"),
            "experiment_seed": report.get("experiment_seed"),
            "fit_split": report.get("fit_split"),
            "early_stopping_split": report.get("early_stopping_split"),
            "evaluation_split": report.get("evaluation_split"),
            "raw_feature_count": report.get("raw_feature_count"),
            "encoded_feature_count": report.get("encoded_feature_count"),
            "architecture": report.get("architecture"),
            "parameter_count": report.get("parameter_count"),
            "hyperparameters": report.get("hyperparameters", {}),
            "best_epoch": report.get("best_epoch"),
            "best_internal_average_precision": report.get(
                "best_internal_average_precision"
            ),
            "learning_curve": report.get("learning_curve", []),
            "validation": report.get("validation"),
            "classical_comparison": report.get("classical_comparison", {}),
            "human_explanation": report.get("human_explanation"),
        }

    def _feature_comparison(self) -> dict[str, Any]:
        """Compare the frozen baseline with an optional local feature challenger."""
        if (
            self._comparison_snapshot_directory is None
            or self._comparison_run_directory is None
        ):
            return {
                "status": "unavailable",
                "reason": "No versioned feature challenger has been materialized.",
            }
        manifest_path = self._comparison_snapshot_directory / "manifest.json"
        result_path = self._comparison_run_directory / "results.json"
        if not manifest_path.exists() or not result_path.exists():
            return {
                "status": "unavailable",
                "reason": "The feature challenger artifacts are not available.",
            }
        challenger_manifest = _json(manifest_path)
        challenger_result = _json(result_path)
        baseline_result = _json(self._run_directory / "results.json")
        ablation_path = (
            self._comparison_run_directory.parent / "feature-ablation-results.json"
        )
        models: list[dict[str, Any]] = []
        for name, result in cast(dict[str, Any], challenger_result["models"]).items():
            baseline_model = cast(dict[str, Any], baseline_result["models"][name])
            baseline_ap = float(baseline_model["validation"]["average_precision"])
            challenger_ap = float(result["validation"]["average_precision"])
            models.append(
                {
                    "model": name,
                    "baseline_validation_average_precision": baseline_ap,
                    "challenger_validation_average_precision": challenger_ap,
                    "validation_average_precision_delta": challenger_ap - baseline_ap,
                    "decision": (
                        "challenger_improves_validation_ap"
                        if challenger_ap > baseline_ap
                        else "baseline_remains_stronger"
                    ),
                }
            )
        ablation: dict[str, Any]
        if ablation_path.exists():
            ablation_report = _json(ablation_path)
            ablation = {
                "status": "available",
                "model": ablation_report["model"],
                "primary_metric": ablation_report["primary_metric"],
                "results": ablation_report["results"],
            }
        else:
            ablation = {
                "status": "unavailable",
                "reason": "No feature-family ablation report has been materialized.",
            }
        return {
            "status": "available",
            "baseline_feature_version": str(
                _json(self._snapshot_directory / "manifest.json").get(
                    "feature_version", HOME_CREDIT_FEATURE_VERSION_V0
                )
            ),
            "challenger_feature_version": str(
                challenger_manifest.get("feature_version", "unknown")
            ),
            "baseline_feature_count": len(
                _json(self._snapshot_directory / "manifest.json")["model_features"]
            ),
            "challenger_feature_count": len(challenger_manifest["model_features"]),
            "models": models,
            "ablation": ablation,
            "test_status": "unopened",
            "human_explanation": (
                "The challenger adds versioned features while keeping the dataset "
                "split, primary metric, and validation boundary unchanged. A "
                "higher validation AP is evidence of improvement for this static "
                "benchmark, not a production guarantee."
            ),
        }
