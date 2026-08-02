#!/usr/bin/env python3
"""Create or verify frozen synthetic-v1 splits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cop.data.splitting.synthetic import SplitError, create_splits, verify_splits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.verify is not None:
            manifest = verify_splits(args.snapshot, args.verify)
            print(f"Verified splits: {manifest['logical_splits_sha256']}")
            return 0
        output_root = args.output_root or Path("data/processed/synthetic-v1")
        destination = create_splits(args.snapshot, output_root)
        print(f"Created splits: {destination}")
        return 0
    except (OSError, ValueError, KeyError, SplitError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
