#!/usr/bin/env python3
"""Run the local COP academic MVP and print a portfolio-friendly summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cop.training.uci_baseline import train_development

DEFAULT_CONFIG = Path("configs/training/uci-baseline.yaml")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the validation summary as JSON",
    )
    return parser


def _summary(run_directory: Path) -> dict[str, Any]:
    results_path = run_directory / "validation-results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    return {
        "run_id": run_directory.name,
        "phase": results["phase"],
        "fit_split": results["fit_split"],
        "evaluation_split": results["evaluation_split"],
        "models": results["models"],
        "artifacts": [
            "logistic_regression.joblib",
            "lightgbm.joblib",
            "validation-predictions.csv",
            "validation-results.json",
        ],
        "test_status": "unopened",
    }


def _print_human(summary: dict[str, Any]) -> None:
    print("COP — academic local MVP")
    print(f"run: {summary['run_id']}")
    print(f"fit/evaluation: {summary['fit_split']} → {summary['evaluation_split']}")
    for name, metrics in summary["models"].items():
        print(
            f"{name}: ROC-AUC={metrics['roc_auc']:.6f} "
            f"average_precision={metrics['average_precision']:.6f}"
        )
    print("test: unopened (use train_uci_baseline.py --finalize-test explicitly)")


def main() -> int:
    arguments = _parser().parse_args()
    try:
        run_directory = train_development(arguments.config)
        summary = _summary(run_directory)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"MVP demo failed: {error}", file=sys.stderr)
        return 2
    if arguments.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_human(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
