"""Reproducible, leakage-safe dataset splitting."""

from cop.data.splitting.synthetic import (
    SplitError,
    create_splits,
    split_tables,
    verify_splits,
)

__all__ = ["SplitError", "create_splits", "split_tables", "verify_splits"]
