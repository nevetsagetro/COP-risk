from __future__ import annotations

from pathlib import Path

from cop.evaluation.model_lab import run_model_lab


def test_model_lab_tunes_both_families_without_opening_test() -> None:
    result = run_model_lab(Path("configs/training/uci-baseline.yaml"), folds=3)

    assert result["test_status"] == "unopened"
    assert result["selection_split"] == "train_cross_validation_out_of_fold"
    assert result["primary_selection_metric"] == "average_precision"
    assert set(result["models"]) == {"logistic_regression", "lightgbm", "knn"}
    for model in result["models"].values():
        assert len(model["candidates"]) >= 3
        assert model["selection_rule"].startswith("rank by validation-free")
        assert {candidate["rank"] for candidate in model["candidates"]} == set(
            range(1, len(model["candidates"]) + 1)
        )
        assert all(
            "cross_validation_std" in candidate for candidate in model["candidates"]
        )
        assert (
            0.05 <= model["selected"]["parameters"].get("C", 0.05)
            or "C" not in model["selected"]["parameters"]
        )
        assert (
            0.05
            <= model["selected"]["validation_at_selected_threshold"]["threshold"]
            <= 0.95
        )
