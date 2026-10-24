"""Explicitly consume the final test for the academic challenger comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.training.challenger import finalize_challenger_test


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--finalize-test",
        action="store_true",
        help="irreversibly consume the shared final-test claim",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/training/uci-baseline.yaml"),
    )
    parser.add_argument("--folds", type=int, default=3)
    arguments = parser.parse_args()
    if not arguments.finalize_test:
        parser.error("pass --finalize-test explicitly to consume the final test")
    print(finalize_challenger_test(arguments.config, folds=arguments.folds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
