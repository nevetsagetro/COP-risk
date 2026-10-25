"""Explicit final-test evaluation for the academic challenger."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
import pandas as pd
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from cop.evaluation.binary import binary_classification_metrics, prevalence
from cop.evaluation.challenger import (
    build_challenger_model,
    positive_probability,
    run_challenger_comparison,
)
from cop.features.academic_challenger import engineer_uci_features
from cop.training.config import load_baseline_config
from cop.training.uci_baseline import (
    CLAIM_FILE,
    FINAL_RESULTS_FILE,
    _canonical_json,
    _claim_test,
    _exclusive_write,
    _expected_run_path,
    _load_test_data,
    _source_metadata,
    _verify_run,
    load_development_data,
)

CHALLENGER_FINAL_RESULTS_FILE = "final-challenger-test-results.json"
CHALLENGER_FINAL_PREDICTIONS_FILE = "final-challenger-test-predictions.csv"


def finalize_challenger_test(config_path: Path, *, folds: int = 3) -> Path:
    """Consume the shared final-test claim for an explicit challenger evaluation."""
    config = load_baseline_config(config_path)
    selection = run_challenger_comparison(config_path, folds=folds)
    metadata = _source_metadata(config, verify_test_file=True)
    run_directory = _expected_run_path(config, metadata)
    result_path = run_directory / CHALLENGER_FINAL_RESULTS_FILE
    prediction_path = run_directory / CHALLENGER_FINAL_PREDICTIONS_FILE
    if result_path.exists() or prediction_path.exists():
        raise RuntimeError("final challenger evaluation already exists for this run")
    if (run_directory / FINAL_RESULTS_FILE).exists() and not (
        run_directory / CLAIM_FILE
    ).exists():
        raise RuntimeError("baseline final artifacts exist without a consumption claim")
    manifest = _verify_run(config, metadata, run_directory)
    if not (run_directory / CLAIM_FILE).exists():
        _claim_test(run_directory, manifest)

    test = _load_test_data(config)
    development = load_development_data(config)
    selected_parameters = cast(dict[str, Any], selection["selected_parameters"])
    challenger = build_challenger_model(config, selected_parameters)
    challenger.fit(
        engineer_uci_features(development.train.features), development.train.target
    )

    baseline_artifact = manifest["models"]["lightgbm"]["artifact"]
    baseline = joblib.load(run_directory / baseline_artifact["path"])
    if not isinstance(baseline, Pipeline):
        raise ValueError("lightgbm artifact is not a fitted sklearn pipeline")
    baseline_probability = positive_probability(baseline, test.features)
    challenger_probability = positive_probability(
        challenger, engineer_uci_features(test.features)
    )
    metrics = {
        "lightgbm_baseline": binary_classification_metrics(
            test.target, baseline_probability, threshold=float(config.raw["threshold"])
        ),
        "lightgbm_challenger": binary_classification_metrics(
            test.target,
            challenger_probability,
            threshold=float(config.raw["threshold"]),
        ),
    }
    predictions = pd.DataFrame({"ID": test.identifiers, "target": test.target})
    predictions["lightgbm_baseline_probability"] = baseline_probability
    predictions["lightgbm_challenger_probability"] = challenger_probability
    prediction_payload = predictions.to_csv(
        index=False, lineterminator="\n", float_format="%.17g"
    ).encode()
    results = {
        "phase": "final_challenger_test",
        "run_id": manifest["run_id"],
        "authorized_use": "academic_baseline_only",
        "evaluation_split": "test",
        "test_status": "consumed",
        "test_prevalence": prevalence(test.target),
        "threshold": config.raw["threshold"],
        "selection": {
            "folds": folds,
            "split": "train_cross_validation",
            "selected_parameters": selected_parameters,
            "derived_features": selection["derived_features"],
        },
        "models": metrics,
        "validation_reference": {
            "baseline": selection["baseline"]["metrics"],
            "challenger": selection["challenger"]["metrics"],
        },
        "predictions_sha256": hashlib.sha256(prediction_payload).hexdigest(),
        "claims_not_made": ["champion", "winner", "production_validity"],
    }
    _exclusive_write(prediction_path, prediction_payload)
    _exclusive_write(result_path, _canonical_json(results))
    return result_path
