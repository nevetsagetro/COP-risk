"""Materialize the cached Home Credit descriptive EDA report."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.evaluation.home_credit_eda import write_home_credit_eda_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot", type=Path, default=Path("data/processed/home-credit-static")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/home-credit-static/eda-report.json"),
    )
    args = parser.parse_args()
    destination = write_home_credit_eda_report(args.snapshot, args.output)
    print(f"created Home Credit EDA report: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
