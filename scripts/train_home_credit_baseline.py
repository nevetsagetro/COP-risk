"""Train the static Home Credit academic baseline without opening test."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.training.home_credit import run_home_credit_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path("data/processed/home-credit-static"),
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=Path("runs/home-credit-static"),
    )
    args = parser.parse_args()
    destination = run_home_credit_baseline(args.snapshot, run_directory=args.run_root)
    print(f"created or reused static baseline: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
