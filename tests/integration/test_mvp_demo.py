from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import scripts.run_mvp_demo as demo


def test_mvp_demo_prints_reproducible_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run = tmp_path / "uci-baseline-demo"
    run.mkdir()
    (run / "validation-results.json").write_text(
        json.dumps(
            {
                "phase": "development",
                "fit_split": "train",
                "evaluation_split": "validation",
                "models": {
                    "logistic_regression": {
                        "roc_auc": 0.7,
                        "average_precision": 0.4,
                    },
                    "lightgbm": {"roc_auc": 0.8, "average_precision": 0.5},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(demo, "train_development", lambda _: run)
    monkeypatch.setattr(sys, "argv", ["run_mvp_demo.py"])

    assert demo.main() == 0
    output = capsys.readouterr().out
    assert "COP — academic local MVP" in output
    assert "train → validation" in output
    assert "lightgbm: ROC-AUC=0.800000" in output
    assert "test: unopened" in output
