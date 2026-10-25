"""Run the offline Home Credit tabular MLP benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.training.deep_learning import run_deep_learning_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot", type=Path, default=Path("data/processed/home-credit-static-v2")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("runs/home-credit-static-v2/deep-learning")
    )
    parser.add_argument(
        "--classical-report",
        type=Path,
        default=Path("runs/home-credit-static-v2/model-benchmark-v2.json"),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--patience", type=int, default=3)
    args = parser.parse_args()
    report = run_deep_learning_benchmark(
        args.snapshot,
        output_directory=args.output,
        classical_report=args.classical_report,
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        patience=args.patience,
    )
    report_path = args.output / "deep-learning-results.json"
    print(f"created Home Credit deep-learning report: {report_path}")
    print(f"status={report['status']} test_status={report['test_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
