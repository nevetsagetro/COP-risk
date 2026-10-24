from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pandas as pd

from cop.evaluation.academic import run_academic_study

_fixture = getattr(
    import_module("tests.integration.test_uci_baseline_training"), "_fixture"
)


def test_academic_study_separates_oof_and_validation(tmp_path: Path) -> None:
    config = _fixture(tmp_path)
    study = run_academic_study(config, folds=3)

    results = json.loads((study / "study-results.json").read_text(encoding="utf-8"))
    oof = pd.read_csv(study / "oof-predictions.csv")
    validation = pd.read_csv(study / "validation-predictions.csv")
    threshold = pd.read_csv(study / "threshold-sweep.csv")

    assert results["test_status"] == "unopened"
    assert set(results["models"]) == {
        "logistic_regression",
        "lightgbm",
        "lightgbm_calibrated",
    }
    assert len(oof) == 60
    assert len(validation) == 20
    assert set(threshold["model"]) == {"logistic_regression", "lightgbm"}
    assert len(threshold) == 34
