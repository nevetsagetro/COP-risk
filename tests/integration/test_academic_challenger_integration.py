from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cop.evaluation.challenger import run_challenger_comparison


def test_challenger_comparison_keeps_test_closed() -> None:
    result = run_challenger_comparison(
        Path("configs/training/uci-baseline.yaml"), folds=3
    )

    assert result["authorized_use"] == "academic_baseline_only"
    assert result["test_status"] == "unopened"
    assert result["fit_split"] == "train"
    assert result["selection_split"] == "train_cross_validation"
    assert result["evaluation_split"] == "validation"
    assert result["feature_count"] == 33
    assert len(result["candidates"]) == 3
    assert set(result["baseline"]["metrics"]) >= {
        "roc_auc",
        "average_precision",
        "brier_score",
        "log_loss",
    }
    assert set(result["challenger"]["metrics"]) >= {
        "roc_auc",
        "average_precision",
        "brier_score",
        "log_loss",
    }
    assert set(result["validation_delta"]) == {
        "roc_auc",
        "average_precision",
        "brier_score",
        "log_loss",
    }


def test_final_test_command_requires_explicit_flag() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/finalize_academic_challenger.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--finalize-test" in result.stderr
