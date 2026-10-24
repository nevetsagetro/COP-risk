"""Run the versioned Home Credit feature-family ablation."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.evaluation.feature_ablation import write_feature_ablation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline", type=Path, default=Path("data/processed/home-credit-static")
    )
    parser.add_argument(
        "--challenger", type=Path, default=Path("data/processed/home-credit-static-v2")
    )
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/home-credit-static-v2/feature-ablation-results.json"),
    )
    args = parser.parse_args()
    destination = write_feature_ablation(
        args.baseline, args.challenger, args.output, folds=args.folds
    )
    print(f"created feature ablation report: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
