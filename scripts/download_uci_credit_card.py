#!/usr/bin/env python3
"""Download or verify UCI Default of Credit Card Clients from official UCI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cop.data.evaluation.contract import EvaluationError, load_dataset_contract
from cop.data.ingestion.uci_credit_card import (
    acquire_official_dataset,
    verify_acquisition,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/datasets/uci-default-credit-card.yaml"),
    )
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    try:
        contract = load_dataset_contract(args.config)
        if args.verify:
            manifest = verify_acquisition(contract, args.verify)
            print(f"Verified acquisition: {manifest['acquisition_id']}")
            return 0
        destination = acquire_official_dataset(contract)
        print(f"Acquired official UCI dataset: {destination}")
        return 0
    except (OSError, ValueError, EvaluationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
