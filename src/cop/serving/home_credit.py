"""Read-only serving facade for the materialized static Home Credit reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from cop.evaluation.calibration import calibration_bins


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return cast(dict[str, Any], value)


class HomeCreditService:
    """Expose cached local reports; this service never trains or opens test."""

    def __init__(self, snapshot_directory: Path, run_directory: Path) -> None:
        self._snapshot_directory = snapshot_directory.resolve()
        self._run_directory = run_directory.resolve()

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
        return {
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
            "feature_groups": feature_groups,
            "audit_only": {
                "columns": manifest["audit_only_columns"],
                "explanation": (
                    "Separated from model inputs and not used as decision features."
                ),
            },
            "models": model_evidence,
            "iterations": iterations,
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
