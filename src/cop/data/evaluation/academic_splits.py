"""Stable stratified splits for approved academic-only snapshots."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from cop.data.evaluation.contract import DatasetContract, EvaluationError
from cop.data.evaluation.evaluator import load_evaluation
from cop.data.ingestion.uci_credit_card import (
    TARGET_NORMALIZED,
    verify_academic_snapshot,
)
from cop.data.synthetic.hashing import logical_table_hash, sha256_file

ACADEMIC_SPLIT_VERSION = 1
SPLIT_NAMES = ("train", "validation", "test")


def _stable_key(seed: int, identifier: int) -> str:
    return hashlib.sha256(f"cop-uci-split-v1:{seed}:{identifier}".encode()).hexdigest()


def stratified_assignments(
    contract: DatasetContract, frame: pd.DataFrame
) -> pd.DataFrame:
    split = cast(dict[str, Any], contract.raw["academic_split"])
    seed = int(split["seed"])
    pieces: list[pd.DataFrame] = []
    for target_value, group in frame.groupby(TARGET_NORMALIZED, sort=True):
        ordered = group[["ID", TARGET_NORMALIZED]].copy()
        ordered["_stable_key"] = [
            _stable_key(seed, int(identifier)) for identifier in ordered["ID"]
        ]
        ordered = ordered.sort_values("_stable_key", kind="mergesort").reset_index(
            drop=True
        )
        train_end = round(len(ordered) * float(split["train_fraction"]))
        validation_end = train_end + round(
            len(ordered) * float(split["validation_fraction"])
        )
        names = pd.Series("test", index=ordered.index, dtype="string")
        names.iloc[:train_end] = "train"
        names.iloc[train_end:validation_end] = "validation"
        ordered["split_name"] = names
        pieces.append(ordered.drop(columns="_stable_key"))
        if set(ordered[TARGET_NORMALIZED]) != {target_value}:
            raise EvaluationError("stratification group target changed")
    assignments = (
        pd.concat(pieces, ignore_index=True)
        .sort_values("ID", kind="mergesort")
        .reset_index(drop=True)
    )
    if not assignments["ID"].is_unique or len(assignments) != len(frame):
        raise EvaluationError("academic split assignments are incomplete")
    return assignments


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def create_academic_splits(
    contract: DatasetContract,
    acquisition: Path,
    snapshot: Path,
    evaluation: Path,
    output_root: Path,
) -> Path:
    snapshot_manifest = verify_academic_snapshot(
        contract, acquisition, evaluation, snapshot
    )
    report = load_evaluation(evaluation)
    if snapshot_manifest["evaluation_id"] != report["evaluation_id"]:
        raise EvaluationError("academic snapshot evaluation mismatch")
    frame = pd.read_parquet(snapshot / "dataset.parquet")
    assignments = stratified_assignments(contract, frame)
    destination = (
        output_root.resolve() / f"academic-splits-{snapshot_manifest['snapshot_id']}"
    )
    if destination.exists():
        verify_academic_splits(contract, acquisition, snapshot, evaluation, destination)
        return destination
    output_root.resolve().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}.tmp-", dir=output_root.resolve()
    ) as temp:
        staging = Path(temp)
        files = _write_split_files(assignments, staging)
        manifest = _split_manifest(contract, snapshot_manifest, report, files)
        manifest_path = staging / "split-manifest.json"
        manifest_path.write_bytes(_canonical_json(manifest) + b"\n")
        (staging / "split-manifest.sha256").write_text(
            f"{sha256_file(manifest_path)}  split-manifest.json\n", encoding="utf-8"
        )
        staging.rename(destination)
    verify_academic_splits(contract, acquisition, snapshot, evaluation, destination)
    return destination


def verify_academic_splits(
    contract: DatasetContract,
    acquisition: Path,
    snapshot: Path,
    evaluation: Path,
    directory: Path,
) -> dict[str, Any]:
    snapshot_manifest = verify_academic_snapshot(
        contract, acquisition, evaluation, snapshot
    )
    expected = {
        *(f"{name}.parquet" for name in SPLIT_NAMES),
        "split-manifest.json",
        "split-manifest.sha256",
    }
    if {path.name for path in directory.iterdir()} != expected:
        raise EvaluationError("academic split inventory differs from contract")
    manifest_path = directory / "split-manifest.json"
    sidecar = (directory / "split-manifest.sha256").read_text().split()
    if (
        len(sidecar) != 2
        or sidecar[1] != manifest_path.name
        or sidecar[0] != sha256_file(manifest_path)
    ):
        raise EvaluationError("academic split manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = load_evaluation(evaluation)
    if manifest["evaluation_id"] != report["evaluation_id"]:
        raise EvaluationError("academic split evaluation mismatch")
    if manifest["snapshot_id"] != snapshot_manifest["snapshot_id"]:
        raise EvaluationError("academic split snapshot mismatch")
    frame = pd.read_parquet(snapshot / "dataset.parquet")
    expected_assignments = stratified_assignments(contract, frame)
    seen: set[int] = set()
    files: dict[str, dict[str, Any]] = {}
    for name in SPLIT_NAMES:
        path = directory / manifest["files"][name]["path"]
        persisted = pd.read_parquet(path)
        expected_frame = expected_assignments.loc[
            expected_assignments["split_name"] == name
        ].reset_index(drop=True)
        if not persisted.equals(expected_frame):
            raise EvaluationError(f"academic split differs from assignment: {name}")
        identifiers = set(int(value) for value in persisted["ID"])
        if seen & identifiers:
            raise EvaluationError("ID crosses academic splits")
        seen |= identifiers
        files[name] = _split_file_manifest(path, persisted)
    expected_manifest = _split_manifest(contract, snapshot_manifest, report, files)
    expected_directory = f"academic-splits-{snapshot_manifest['snapshot_id']}"
    if directory.name != expected_directory or expected_manifest != manifest:
        raise EvaluationError("academic split manifest metadata mismatch")
    return cast(dict[str, Any], manifest)


def _write_split_files(
    assignments: pd.DataFrame, directory: Path
) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for name in SPLIT_NAMES:
        split_frame = assignments.loc[assignments["split_name"] == name].reset_index(
            drop=True
        )
        path = directory / f"{name}.parquet"
        pq.write_table(
            pa.Table.from_pandas(split_frame, preserve_index=False),
            path,
            compression="zstd",
            compression_level=9,
            version="2.6",
        )
        files[name] = _split_file_manifest(path, pd.read_parquet(path))
    return files


def _split_file_manifest(path: Path, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "path": path.name,
        "rows": len(frame),
        "class_counts": {
            str(key): int(value)
            for key, value in frame[TARGET_NORMALIZED]
            .value_counts()
            .sort_index()
            .to_dict()
            .items()
        },
        "physical_sha256": sha256_file(path),
        "logical_sha256": logical_table_hash(frame, ("ID",)),
    }


def _split_manifest(
    contract: DatasetContract,
    snapshot_manifest: dict[str, Any],
    report: dict[str, Any],
    files: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    logical = hashlib.sha256(
        b"cop-uci-academic-splits-v1\0"
        + _canonical_json({name: files[name]["logical_sha256"] for name in SPLIT_NAMES})
    ).hexdigest()
    return {
        "academic_split_version": ACADEMIC_SPLIT_VERSION,
        "snapshot_id": snapshot_manifest["snapshot_id"],
        "evaluation_id": report["evaluation_id"],
        "seed": contract.raw["academic_split"]["seed"],
        "strategy": "stable-hash stratified random split; no temporal claim",
        "logical_splits_sha256": logical,
        "files": files,
        "id_intersections": 0,
        "authorized_use": "academic_baseline_only",
    }
