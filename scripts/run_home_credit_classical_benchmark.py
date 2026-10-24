"""Run the offline Optuna and classical challenger benchmark on Home Credit v2."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.evaluation.classical_benchmark_v2 import write_classical_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot", type=Path, default=Path("data/processed/home-credit-static-v2")
    )
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/home-credit-static-v2/model-benchmark-v2.json"),
    )
    args = parser.parse_args()
    destination = write_classical_benchmark(
        args.snapshot,
        args.output,
        folds=args.folds,
        optuna_trials=args.trials,
        seed=args.seed,
    )
    print(f"created model benchmark report: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
