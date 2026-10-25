#!/usr/bin/env python3
"""Train or finalize the frozen UCI academic baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

from cop.training.uci_baseline import finalize_test, train_development

DEFAULT_CONFIG = Path("configs/training/uci-baseline.yaml")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--finalize-test",
        action="store_true",
        help="irreversibly consume test for the frozen development run",
    )
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    output = (
        finalize_test(arguments.config)
        if arguments.finalize_test
        else train_development(arguments.config)
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
