#!/usr/bin/env python3
"""Run the reproducible academic cross-validation study."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.evaluation.academic import run_academic_study


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/training/uci-baseline.yaml")
    )
    parser.add_argument("--folds", type=int, default=5)
    arguments = parser.parse_args()
    print(run_academic_study(arguments.config, folds=arguments.folds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
