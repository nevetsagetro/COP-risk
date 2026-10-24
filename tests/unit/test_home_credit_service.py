import json
from pathlib import Path

from cop.serving.home_credit import HomeCreditService


def test_home_credit_service_exposes_reports_without_training(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    run = tmp_path / "run"
    snapshot.mkdir()
    run.mkdir()
    (snapshot / "manifest.json").write_text(
        json.dumps(
            {
                "rows": 4,
                "model_features": ["feature"],
                "files": {
                    "train": {"rows": 2},
                    "validation": {"rows": 1},
                    "test": {"rows": 1},
                },
                "static_split_strategy": "entity-disjoint",
            }
        ),
        encoding="utf-8",
    )
    (run / "results.json").write_text(
        json.dumps(
            {
                "static_limitation": "no temporal claims",
                "models": {"lightgbm": {"validation": {"average_precision": 0.2}}},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "model-lab-results.json").write_text(
        json.dumps(
            {
                "models": {
                    "lightgbm": {
                        "candidates": [
                            {
                                "selected": True,
                                "trial_id": "lightgbm-trial-01",
                                "parameters": {"n_estimators": 1},
                                "cross_validation": {"average_precision": 0.1},
                                "cross_validation_std": {"average_precision": 0.01},
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "policy-results.json").write_text(
        json.dumps({"models": {}, "capacities": [0.1]}), encoding="utf-8"
    )

    result = HomeCreditService(snapshot, run).summary()

    assert result["test_status"] == "unopened"
    assert result["models"][0]["selected_trial"] == "lightgbm-trial-01"
