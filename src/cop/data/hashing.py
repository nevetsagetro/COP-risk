"""Dataset-neutral physical and logical hashing utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa

LOGICAL_HASH_ALGORITHM = "cop-logical-v1"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _scalar_bytes(value: Any) -> bytes:
    if value is None or value is pd.NA or pd.isna(value):
        return b"N"
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            raise ValueError("logical hash rejects naive timestamps")
        micros = value.tz_convert("UTC").value // 1_000
        return b"T" + int(micros).to_bytes(8, "big", signed=True)
    if isinstance(value, bool):
        return b"B1" if value else b"B0"
    if isinstance(value, int):
        payload = str(value).encode()
        return b"I" + len(payload).to_bytes(4, "big") + payload
    if isinstance(value, float):
        payload = format(value, ".12g").encode()
        return b"F" + len(payload).to_bytes(4, "big") + payload
    payload = str(value).encode("utf-8")
    return b"S" + len(payload).to_bytes(4, "big") + payload


def logical_table_hash(frame: pd.DataFrame, primary_key: tuple[str, ...]) -> str:
    """Hash typed values after canonical row and column ordering."""
    ordered_columns = sorted(frame.columns)
    ordered = frame.sort_values(list(primary_key), kind="mergesort")
    schema = pa.Table.from_pandas(
        ordered[ordered_columns], preserve_index=False
    ).schema.remove_metadata()
    digest = hashlib.sha256()
    digest.update(LOGICAL_HASH_ALGORITHM.encode())
    digest.update(str(schema).encode())
    for row in ordered[ordered_columns].itertuples(index=False, name=None):
        for value in row:
            encoded = _scalar_bytes(value)
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
    return digest.hexdigest()


def logical_snapshot_hash(table_hashes: dict[str, str]) -> str:
    """Combine named logical table hashes into one deterministic digest."""
    payload = json.dumps(table_hashes, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b"cop-snapshot-logical-v1\0" + payload).hexdigest()
