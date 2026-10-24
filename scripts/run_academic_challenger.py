"""Run the leakage-safe academic challenger comparison and print JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cop.evaluation.challenger import run_challenger_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/training/uci-baseline.yaml"),
    )
    parser.add_argument("--folds", type=int, default=3)
    args = parser.parse_args()
    result = run_challenger_comparison(args.config, folds=args.folds)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
