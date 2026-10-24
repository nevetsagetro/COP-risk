"""Run the reproducible multi-model academic tuning lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cop.evaluation.model_lab import run_model_lab


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/training/uci-baseline.yaml"),
    )
    parser.add_argument("--folds", type=int, default=3)
    args = parser.parse_args()
    result = run_model_lab(args.config, folds=args.folds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
