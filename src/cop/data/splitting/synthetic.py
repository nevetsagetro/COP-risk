"""Frozen temporal and borrower-disjoint splits for synthetic-v1."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from cop.data.schemas.synthetic import INPUT_FEATURE_COLUMNS
from cop.data.synthetic.config import SyntheticConfig
from cop.data.synthetic.hashing import logical_table_hash, sha256_file
from cop.data.synthetic.snapshot import verify_snapshot

SPLIT_MANIFEST_VERSION = 1
SPLIT_ALGORITHM = "latest-borrower-window-v1"
FINGERPRINT_ALGORITHM = "sha256-predecision-content-v1"
SPLIT_NAMES = ("train", "validation", "calibration", "threshold", "test")


class SplitError(RuntimeError):
    """Raised when split construction or verification fails."""


@dataclass(frozen=True)
class SplitResult:
    frames: dict[str, pd.DataFrame]
    purge_rows: int
    purge_borrowers: int
    purge_labels: dict[str, int]
    excluded_labels: dict[str, int]
    source_labels: dict[str, int]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _observation_fingerprint(row: tuple[object, ...]) -> str:
    payload = "\0".join(str(value) for value in row).encode("utf-8")
    return hashlib.sha256(b"cop-observation-v1\0" + payload).hexdigest()


def _add_fingerprints(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    identity = result[
        [
            "decision_timestamp",
            "application_available_at",
            "income_available_at",
            "bureau_available_at",
            *INPUT_FEATURE_COLUMNS,
        ]
    ]
    result["observation_fingerprint"] = [
        _observation_fingerprint(row)
        for row in identity.itertuples(index=False, name=None)
    ]
    return result


def _window_series(
    applications: pd.DataFrame, config: SyntheticConfig
) -> pd.Series[Any]:
    timestamp = applications["decision_timestamp"]
    boundaries = (
        pd.Timestamp(config.decision_start),
        pd.Timestamp(config.train_end),
        pd.Timestamp(config.validation_end),
        pd.Timestamp(config.calibration_end),
        pd.Timestamp(config.threshold_end),
        pd.Timestamp(config.test_end),
    )
    result = pd.Series(pd.NA, index=applications.index, dtype="string")
    for name, left, right in zip(SPLIT_NAMES, boundaries, boundaries[1:]):
        result.loc[(timestamp >= left) & (timestamp < right)] = name
    if result.isna().any():
        raise SplitError("application outside frozen split windows")
    return result


def split_tables(applications: pd.DataFrame, config: SyntheticConfig) -> SplitResult:
    """Assign the latest borrower window, purge history, and retain mature labels."""
    working = applications.copy()
    working["split_name"] = _window_series(working, config)
    immature_test = (working["split_name"] == "test") & (
        working["label_status"] == "immature"
    )
    if immature_test.any():
        raise SplitError("final test contains immature non-censored labels")
    rank = {name: index for index, name in enumerate(SPLIT_NAMES)}
    working["_split_rank"] = working["split_name"].map(rank).astype("int8")
    latest = working.groupby("borrower_id", sort=False)["_split_rank"].transform("max")
    purged = working["_split_rank"] != latest
    purge_rows = int(purged.sum())
    purge_borrowers = int(working.loc[purged, "borrower_id"].nunique())
    purge_labels = {
        str(key): int(value)
        for key, value in working.loc[purged, "label_status"]
        .value_counts(dropna=False)
        .sort_index()
        .to_dict()
        .items()
    }
    source_labels = {
        str(key): int(value)
        for key, value in working["label_status"]
        .value_counts(dropna=False)
        .sort_index()
        .to_dict()
        .items()
    }
    retained = working.loc[~purged].copy()
    excluded = retained["label_status"] != "mature"
    excluded_labels = {
        str(key): int(value)
        for key, value in retained.loc[excluded, "label_status"]
        .value_counts(dropna=False)
        .sort_index()
        .to_dict()
        .items()
    }
    supervised = retained.loc[~excluded].drop(columns=["_split_rank"])
    frames = {
        name: _add_fingerprints(
            supervised.loc[supervised["split_name"] == name]
            .sort_values("application_id", kind="mergesort")
            .reset_index(drop=True)
        )
        for name in SPLIT_NAMES
    }
    _validate_frames(frames, config)
    return SplitResult(
        frames,
        purge_rows,
        purge_borrowers,
        purge_labels,
        excluded_labels,
        source_labels,
    )


def _validate_frames(frames: dict[str, pd.DataFrame], config: SyntheticConfig) -> None:
    if tuple(frames) != SPLIT_NAMES:
        raise SplitError("five frozen split identities are required")
    seen_borrowers: set[str] = set()
    seen_applications: set[str] = set()
    seen_fingerprints: set[str] = set()
    boundaries = (
        pd.Timestamp(config.decision_start),
        pd.Timestamp(config.train_end),
        pd.Timestamp(config.validation_end),
        pd.Timestamp(config.calibration_end),
        pd.Timestamp(config.threshold_end),
        pd.Timestamp(config.test_end),
    )
    for index, name in enumerate(SPLIT_NAMES):
        frame = frames[name]
        if not (frame["split_name"] == name).all():
            raise SplitError(f"split identity mismatch: {name}")
        if not (frame["label_status"] == "mature").all():
            raise SplitError(f"non-mature label included: {name}")
        if frame["default_within_horizon"].isna().any():
            raise SplitError(f"missing supervised label included: {name}")
        if not frame["application_id"].is_unique:
            raise SplitError(f"duplicate application_id within split: {name}")
        if not frame["observation_fingerprint"].is_unique:
            raise SplitError(f"duplicate observation fingerprint within split: {name}")
        timestamps = frame["decision_timestamp"]
        if not (
            (timestamps >= boundaries[index]) & (timestamps < boundaries[index + 1])
        ).all():
            raise SplitError(f"timestamp outside window: {name}")
        borrowers = set(frame["borrower_id"].astype(str))
        applications = set(frame["application_id"].astype(str))
        fingerprints = set(frame["observation_fingerprint"].astype(str))
        if seen_borrowers & borrowers:
            raise SplitError("borrower_id crosses splits")
        if seen_applications & applications:
            raise SplitError("application_id crosses splits")
        if seen_fingerprints & fingerprints:
            raise SplitError("observation fingerprint crosses splits")
        seen_borrowers |= borrowers
        seen_applications |= applications
        seen_fingerprints |= fingerprints


def _file_metadata(path: Path, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "path": path.name,
        "rows": len(frame),
        "borrowers": int(frame["borrower_id"].nunique()),
        "physical_sha256": sha256_file(path),
        "logical_sha256": logical_table_hash(frame, ("application_id",)),
    }


def _manifest(
    snapshot_manifest: dict[str, Any],
    config: SyntheticConfig,
    result: SplitResult,
    files: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    logical_payload = {name: str(files[name]["logical_sha256"]) for name in SPLIT_NAMES}
    split_hash = hashlib.sha256(
        b"cop-splits-logical-v1\0" + _canonical_json(logical_payload)
    ).hexdigest()
    return {
        "split_manifest_version": SPLIT_MANIFEST_VERSION,
        "split_algorithm": SPLIT_ALGORITHM,
        "fingerprint_algorithm": FINGERPRINT_ALGORITHM,
        "snapshot_id": snapshot_manifest["snapshot_id"],
        "snapshot_logical_sha256": snapshot_manifest["logical_snapshot_sha256"],
        "logical_splits_sha256": split_hash,
        "estimand": (
            "later synthetic applications from borrowers absent from other partitions"
        ),
        "assignment": "borrower assigned to its latest temporal window",
        "purge": {
            "rows": result.purge_rows,
            "borrowers": result.purge_borrowers,
            "labels": result.purge_labels,
            "rule": "remove borrower observations from every earlier window",
        },
        "source_label_counts": result.source_labels,
        "excluded_from_supervised_use": result.excluded_labels,
        "windows": {
            "train": [config.decision_start, config.train_end],
            "validation": [config.train_end, config.validation_end],
            "calibration": [config.validation_end, config.calibration_end],
            "threshold": [config.calibration_end, config.threshold_end],
            "test": [config.threshold_end, config.test_end],
        },
        "window_semantics": "UTC half-open [start,end)",
        "partition_purposes": {
            "train": "future internal temporal/grouped development only",
            "validation": "future external configuration comparison only",
            "calibration": "future calibrator fit only",
            "threshold": "future threshold selection only",
            "test": (
                "sealed final evaluation only; excluded from all gates and adaptation"
            ),
        },
        "intersection_checks": {
            "borrower_id": 0,
            "application_id": 0,
            "observation_fingerprint": 0,
        },
        "test_access": "sealed_not_used_for_acceptance_or_development",
        "files": files,
    }


def create_splits(snapshot_directory: Path, output_root: Path) -> Path:
    """Create immutable split Parquet files and a verifiable manifest."""
    snapshot_manifest = verify_snapshot(snapshot_directory)
    mapping = dict(snapshot_manifest["configuration"])
    mapping["output_root"] = "."
    config = SyntheticConfig.from_mapping(mapping)
    applications = pd.read_parquet(snapshot_directory / "applications.parquet")
    result = split_tables(applications, config)
    destination = output_root.resolve() / str(snapshot_manifest["snapshot_id"])
    if destination.exists():
        raise SplitError(f"split destination already exists: {destination}")
    output_root.resolve().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".splits-", dir=output_root.resolve()
    ) as temp:
        staging = Path(temp)
        files: dict[str, dict[str, Any]] = {}
        for name in SPLIT_NAMES:
            path = staging / f"{name}.parquet"
            table = pa.Table.from_pandas(result.frames[name], preserve_index=False)
            pq.write_table(
                table,
                path,
                compression=config.parquet_compression,
                compression_level=config.parquet_compression_level,
                row_group_size=config.parquet_row_group_size,
                version="2.6",
                coerce_timestamps="us",
                allow_truncated_timestamps=False,
            )
            persisted = pd.read_parquet(path)
            files[name] = _file_metadata(path, persisted)
        manifest = _manifest(snapshot_manifest, config, result, files)
        manifest_path = staging / "split-manifest.json"
        manifest_path.write_bytes(_canonical_json(manifest) + b"\n")
        (staging / "split-manifest.sha256").write_text(
            f"{sha256_file(manifest_path)}  split-manifest.json\n", encoding="utf-8"
        )
        staging.rename(destination)
    verify_splits(snapshot_directory, destination)
    return destination


def verify_splits(snapshot_directory: Path, split_directory: Path) -> dict[str, Any]:
    """Verify split inventory, hashes, source identity, and leakage invariants."""
    snapshot_manifest = verify_snapshot(snapshot_directory)
    expected = {
        *(f"{name}.parquet" for name in SPLIT_NAMES),
        "split-manifest.json",
        "split-manifest.sha256",
    }
    if {path.name for path in split_directory.iterdir()} != expected:
        raise SplitError("split inventory differs from contract")
    manifest_path = split_directory / "split-manifest.json"
    sidecar = (split_directory / "split-manifest.sha256").read_text().split()
    if len(sidecar) != 2 or sidecar[1] != manifest_path.name:
        raise SplitError("split manifest sidecar is invalid")
    if sidecar[0] != sha256_file(manifest_path):
        raise SplitError("split manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["snapshot_id"] != snapshot_manifest["snapshot_id"]:
        raise SplitError("split source snapshot mismatch")
    mapping = dict(snapshot_manifest["configuration"])
    mapping["output_root"] = "."
    config = SyntheticConfig.from_mapping(mapping)
    frames = {
        name: pd.read_parquet(split_directory / f"{name}.parquet")
        for name in SPLIT_NAMES
    }
    _validate_frames(frames, config)
    result = split_tables(
        pd.read_parquet(snapshot_directory / "applications.parquet"), config
    )
    files: dict[str, dict[str, Any]] = {}
    for name in SPLIT_NAMES:
        path = split_directory / f"{name}.parquet"
        files[name] = _file_metadata(path, frames[name])
        if not result.frames[name].equals(frames[name]):
            raise SplitError(
                f"persisted split differs from deterministic assignment: {name}"
            )
    expected_manifest = _manifest(snapshot_manifest, config, result, files)
    if manifest != expected_manifest:
        raise SplitError("split manifest differs from recomputed metadata")
    return cast(dict[str, Any], manifest)
