"""Run the static Home Credit model-search experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cop.evaluation.home_credit import run_home_credit_model_lab


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot", type=Path, default=Path("data/processed/home-credit-static")
    )
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/home-credit-static/model-lab-results.json"),
    )
    args = parser.parse_args()
    result = run_home_credit_model_lab(args.snapshot, folds=args.folds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"created static model lab report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
