#!/usr/bin/env python3
"""Generate or verify a deterministic COP synthetic snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cop.data.synthetic.config import ConfigError, load_config
from cop.data.synthetic.snapshot import (
    SnapshotError,
    generate_snapshot,
    verify_snapshot,
)
from cop.data.validation.synthetic import ValidationError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic synthetic COP snapshot."
    )
    parser.add_argument("--config", type=Path, help="versioned YAML configuration")
    parser.add_argument(
        "--output-root",
        type=Path,
        help="override the configured ignored output root",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="explicitly replace the same verified snapshot identity",
    )
    parser.add_argument(
        "--verify",
        type=Path,
        metavar="SNAPSHOT_DIR",
        help="verify an existing snapshot without writing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.verify is not None:
            if args.config is not None or args.force or args.output_root is not None:
                raise SnapshotError(
                    "--verify cannot be combined with generation arguments"
                )
            manifest = verify_snapshot(args.verify)
            print(
                "Verified snapshot "
                f"{manifest['snapshot_id']} "
                f"({manifest['logical_snapshot_sha256']})"
            )
            return 0
        if args.config is None:
            raise ConfigError("--config is required for generation")
        config = load_config(args.config)
        output_root = args.output_root or Path(config.output_root)
        destination = generate_snapshot(config, output_root, force=args.force)
        manifest = verify_snapshot(destination)
        print(f"Created snapshot: {destination}")
        print(f"Logical hash: {manifest['logical_snapshot_sha256']}")
        return 0
    except (ConfigError, SnapshotError, ValidationError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # defensive CLI boundary; library APIs remain specific
        print(f"error: unexpected snapshot failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
