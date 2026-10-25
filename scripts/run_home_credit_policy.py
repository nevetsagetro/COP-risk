"""Evaluate static Home Credit ranking policies at bounded capacities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cop.evaluation.policy import capacity_metrics


def run(predictions_path: Path, output: Path) -> Path:
    frame = pd.read_csv(predictions_path)
    target = frame["TARGET"].to_numpy(dtype=int)
    capacities = (0.01, 0.05, 0.10, 0.20)
    models = {}
    for column in ("logistic_regression_probability", "lightgbm_probability"):
        name = column.removesuffix("_probability")
        models[name] = [
            capacity_metrics(
                target,
                frame[column].to_numpy(dtype=float),
                capacity=capacity,
            )
            for capacity in capacities
        ]
    result = {
        "authorized_use": "academic_static_benchmark_only",
        "evaluation_split": "validation",
        "test_status": "unopened",
        "capacities": capacities,
        "models": models,
        "note": (
            "Ranking policy comparison on validation predictions; this does not "
            "promote a model or support temporal or production claims."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path(
            "runs/home-credit-static/home-credit-static-0f5a4a4dadfb0e8d/"
            "validation-predictions.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/home-credit-static/policy-results.json"),
    )
    args = parser.parse_args()
    print(f"created static policy report: {run(args.predictions, args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
