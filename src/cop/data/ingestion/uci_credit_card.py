"""Official UCI Default of Credit Card Clients acquisition and inspection."""

from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from cop.data.evaluation.contract import DatasetContract, EvaluationError
from cop.data.synthetic.hashing import logical_table_hash, sha256_file

ACQUISITION_MANIFEST_VERSION = 1
SNAPSHOT_MANIFEST_VERSION = 2
TARGET_NORMALIZED = "default_payment_next_month"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "cop-credit-risk/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        final_url = response.geturl()
        if not final_url.startswith("https://archive.ics.uci.edu/"):
            raise EvaluationError("official UCI download redirected to another origin")
        return cast(bytes, response.read())


def _extract_member(payload: bytes, member: str) -> bytes:
    with tempfile.TemporaryFile() as stream:
        stream.write(payload)
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            matches = [name for name in archive.namelist() if Path(name).name == member]
            if len(matches) != 1:
                raise EvaluationError(
                    "official archive does not contain one expected XLS"
                )
            info = archive.getinfo(matches[0])
            if info.is_dir() or info.file_size > 20_000_000:
                raise EvaluationError("unsafe source member")
            return archive.read(info)


def acquisition_id(contract: DatasetContract, archive_sha256: str) -> str:
    return f"{contract.dataset_id}-{archive_sha256}"


def acquire_official_dataset(
    contract: DatasetContract, *, payload: bytes | None = None
) -> Path:
    """Acquire the official immutable archive and publish a hashed local copy."""
    archive = (
        payload
        if payload is not None
        else _download(contract.raw["official_download_url"])
    )
    source = _extract_member(archive, cast(str, contract.raw["source_member"]))
    archive_hash = hashlib.sha256(archive).hexdigest()
    identifier = acquisition_id(contract, archive_hash)
    destination = contract.output_root.resolve() / identifier
    if destination.exists():
        verify_acquisition(contract, destination)
        return destination
    contract.output_root.resolve().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{identifier}.tmp-", dir=contract.output_root.resolve()
    ) as temp:
        staging = Path(temp)
        archive_path = staging / cast(str, contract.raw["archive_filename"])
        source_path = staging / cast(str, contract.raw["source_filename"])
        archive_path.write_bytes(archive)
        source_path.write_bytes(source)
        manifest = {
            "manifest_version": ACQUISITION_MANIFEST_VERSION,
            "acquisition_id": identifier,
            "dataset_id": contract.dataset_id,
            "publisher": contract.raw["publisher"],
            "official_page_url": contract.raw["official_page_url"],
            "official_download_url": contract.raw["official_download_url"],
            "doi": contract.raw["doi"],
            "acquisition_date": contract.raw["acquisition_date"],
            "license": contract.raw["license"],
            "archive": {
                "path": archive_path.name,
                "bytes": len(archive),
                "sha256": archive_hash,
            },
            "source_file": {
                "path": source_path.name,
                "bytes": len(source),
                "sha256": hashlib.sha256(source).hexdigest(),
            },
        }
        manifest_path = staging / "acquisition-manifest.json"
        manifest_path.write_bytes(_canonical_json(manifest) + b"\n")
        (staging / "acquisition-manifest.sha256").write_text(
            f"{sha256_file(manifest_path)}  acquisition-manifest.json\n",
            encoding="utf-8",
        )
        staging.rename(destination)
    verify_acquisition(contract, destination)
    return destination


def verify_acquisition(contract: DatasetContract, directory: Path) -> dict[str, Any]:
    expected = {
        cast(str, contract.raw["archive_filename"]),
        cast(str, contract.raw["source_filename"]),
        "acquisition-manifest.json",
        "acquisition-manifest.sha256",
    }
    if (
        not directory.is_dir()
        or {path.name for path in directory.iterdir()} != expected
    ):
        raise EvaluationError("acquisition inventory differs from contract")
    manifest_path = directory / "acquisition-manifest.json"
    sidecar = (directory / "acquisition-manifest.sha256").read_text().split()
    if len(sidecar) != 2 or sidecar[1] != manifest_path.name:
        raise EvaluationError("invalid acquisition manifest sidecar")
    if sidecar[0] != sha256_file(manifest_path):
        raise EvaluationError("acquisition manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive_path = directory / cast(str, contract.raw["archive_filename"])
    source_path = directory / cast(str, contract.raw["source_filename"])
    archive_hash = sha256_file(archive_path)
    source_hash = sha256_file(source_path)
    identifier = acquisition_id(contract, archive_hash)
    expected_manifest = {
        "manifest_version": ACQUISITION_MANIFEST_VERSION,
        "acquisition_id": identifier,
        "dataset_id": contract.dataset_id,
        "publisher": contract.raw["publisher"],
        "official_page_url": contract.raw["official_page_url"],
        "official_download_url": contract.raw["official_download_url"],
        "doi": contract.raw["doi"],
        "acquisition_date": contract.raw["acquisition_date"],
        "license": contract.raw["license"],
        "archive": {
            "path": archive_path.name,
            "bytes": archive_path.stat().st_size,
            "sha256": archive_hash,
        },
        "source_file": {
            "path": source_path.name,
            "bytes": source_path.stat().st_size,
            "sha256": source_hash,
        },
    }
    if manifest != expected_manifest:
        raise EvaluationError("acquisition manifest differs from contract or files")
    if directory.name != identifier:
        raise EvaluationError("acquisition directory identity mismatch")
    extracted = _extract_member(
        archive_path.read_bytes(), cast(str, contract.raw["source_member"])
    )
    if hashlib.sha256(extracted).hexdigest() != source_hash:
        raise EvaluationError("archive member differs from extracted source")
    return cast(dict[str, Any], manifest)


def read_source_frame(contract: DatasetContract, acquisition: Path) -> pd.DataFrame:
    """Read and normalize the published UCI workbook without feature fitting."""
    source = acquisition / cast(str, contract.raw["source_filename"])
    frame = pd.read_excel(source, sheet_name="Data", header=1, engine="xlrd")
    frame = frame.rename(
        columns={cast(str, contract.raw["target"]["source_column"]): TARGET_NORMALIZED}
    )
    return frame


def inspect_schema(contract: DatasetContract, frame: pd.DataFrame) -> dict[str, Any]:
    expected = cast(dict[str, Any], contract.raw["expected_schema"])
    expected_columns = cast(list[str], expected["columns"])
    actual_columns = [str(column) for column in frame.columns]
    target = TARGET_NORMALIZED
    return {
        "rows": len(frame),
        "columns": actual_columns,
        "rows_match": len(frame) == expected["rows"],
        "columns_match": actual_columns == expected_columns,
        "missing_cells": int(frame.isna().sum().sum()),
        "id_unique": bool(frame["ID"].is_unique) if "ID" in frame else False,
        "target_values": (
            sorted(int(value) for value in frame[target].dropna().unique())
            if target in frame
            else []
        ),
        "target_missing": int(frame[target].isna().sum())
        if target in frame
        else len(frame),
    }


def materialize_academic_snapshot(
    contract: DatasetContract,
    acquisition: Path,
    frame: pd.DataFrame,
    evaluation: Path,
) -> Path:
    """Write modelable and audit-only Parquet after verified gates pass."""
    acquisition_manifest = verify_acquisition(contract, acquisition)
    report = _verified_academic_evaluation(contract, acquisition, frame, evaluation)
    contract_hash = hashlib.sha256(contract.canonical_json().encode()).hexdigest()
    evaluation_hash = sha256_file(evaluation / "evaluation.json")
    ordered = frame.sort_values("ID", kind="mergesort").reset_index(drop=True)
    source_logical_hash = logical_table_hash(ordered, ("ID",))
    identity = hashlib.sha256(
        b"cop-uci-academic-snapshot-v2\0"
        + _canonical_json(
            {
                "contract_sha256": contract_hash,
                "evaluation_sha256": evaluation_hash,
                "source_logical_sha256": source_logical_hash,
                "source_sha256": acquisition_manifest["source_file"]["sha256"],
            }
        )
    ).hexdigest()
    snapshot_id = f"{contract.dataset_id}-academic-{identity}"
    destination = contract.snapshot_root.resolve() / snapshot_id
    if destination.exists():
        verify_academic_snapshot(contract, acquisition, evaluation, destination)
        return destination
    contract.snapshot_root.resolve().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{snapshot_id}.tmp-", dir=contract.snapshot_root.resolve()
    ) as temp:
        staging = Path(temp)
        sensitive = cast(list[str], contract.raw["protected_or_sensitive_columns"])
        if "ID" in sensitive or TARGET_NORMALIZED in sensitive:
            raise EvaluationError("invalid audit-only column contract")
        missing_sensitive = set(sensitive) - set(ordered.columns)
        if missing_sensitive:
            raise EvaluationError("audit-only columns are absent from source")
        modelable = ordered.drop(columns=sensitive)
        audit_only = ordered[["ID", *sensitive]].copy()
        data_path = staging / "dataset.parquet"
        audit_path = staging / "audit_only.parquet"
        pq.write_table(
            pa.Table.from_pandas(modelable, preserve_index=False),
            data_path,
            compression="zstd",
            compression_level=9,
            version="2.6",
        )
        pq.write_table(
            pa.Table.from_pandas(audit_only, preserve_index=False),
            audit_path,
            compression="zstd",
            compression_level=9,
            version="2.6",
        )
        persisted = pd.read_parquet(data_path)
        persisted_audit = pd.read_parquet(audit_path)
        schema = inspect_schema(contract, ordered)
        data_file = _parquet_manifest(data_path, persisted)
        audit_file = _parquet_manifest(audit_path, persisted_audit)
        manifest = {
            "manifest_version": SNAPSHOT_MANIFEST_VERSION,
            "snapshot_id": snapshot_id,
            "dataset_id": contract.dataset_id,
            "accepted_use": "academic_baseline_only",
            "source_acquisition_id": acquisition_manifest["acquisition_id"],
            "source_sha256": acquisition_manifest["source_file"]["sha256"],
            "source_logical_sha256": source_logical_hash,
            "contract_sha256": contract_hash,
            "evaluation_id": report["evaluation_id"],
            "evaluation_sha256": evaluation_hash,
            "rows": len(ordered),
            "modelable_columns": list(persisted.columns),
            "audit_only_columns": list(persisted_audit.columns),
            "schema": schema,
            "target": contract.raw["target"],
            "protected_or_sensitive_columns": contract.raw[
                "protected_or_sensitive_columns"
            ],
            "file": data_file,
            "audit_only_file": audit_file,
            "files": {"modelable": data_file, "audit_only": audit_file},
            "prohibited_claims": [
                "temporal_validation",
                "longitudinal_monitoring",
                "production",
                "fairness",
                "real_credit_decisions",
            ],
        }
        manifest_path = staging / "snapshot-manifest.json"
        manifest_path.write_bytes(_canonical_json(manifest) + b"\n")
        (staging / "snapshot-manifest.sha256").write_text(
            f"{sha256_file(manifest_path)}  snapshot-manifest.json\n", encoding="utf-8"
        )
        staging.rename(destination)
    verify_academic_snapshot(contract, acquisition, evaluation, destination)
    return destination


def verify_academic_snapshot(
    contract: DatasetContract,
    acquisition: Path,
    evaluation: Path,
    snapshot: Path,
) -> dict[str, Any]:
    expected = {
        "dataset.parquet",
        "audit_only.parquet",
        "snapshot-manifest.json",
        "snapshot-manifest.sha256",
    }
    if not snapshot.is_dir():
        raise EvaluationError("academic snapshot directory is absent")
    if {path.name for path in snapshot.iterdir()} != expected:
        raise EvaluationError("academic snapshot inventory differs from contract")
    manifest_path = snapshot / "snapshot-manifest.json"
    sidecar = (snapshot / "snapshot-manifest.sha256").read_text().split()
    if (
        len(sidecar) != 2
        or sidecar[1] != manifest_path.name
        or sidecar[0] != sha256_file(manifest_path)
    ):
        raise EvaluationError("academic snapshot manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    acquisition_manifest = verify_acquisition(contract, acquisition)
    data_path = snapshot / "dataset.parquet"
    audit_path = snapshot / "audit_only.parquet"
    modelable = pd.read_parquet(data_path)
    audit_only = pd.read_parquet(audit_path)
    sensitive = cast(list[str], contract.raw["protected_or_sensitive_columns"])
    if any(column in modelable.columns for column in sensitive):
        raise EvaluationError("audit-only column leaked into modelable snapshot")
    if list(audit_only.columns) != ["ID", *sensitive]:
        raise EvaluationError("audit-only snapshot schema mismatch")
    if not modelable["ID"].is_unique or not audit_only["ID"].is_unique:
        raise EvaluationError("snapshot ID is not unique")
    source = modelable.merge(audit_only, on="ID", validate="one_to_one")
    expected_columns = cast(list[str], contract.raw["expected_schema"]["columns"])
    source = (
        source[expected_columns]
        .sort_values("ID", kind="mergesort")
        .reset_index(drop=True)
    )
    report = _verified_academic_evaluation(contract, acquisition, source, evaluation)
    contract_hash = hashlib.sha256(contract.canonical_json().encode()).hexdigest()
    evaluation_hash = sha256_file(evaluation / "evaluation.json")
    source_logical_hash = logical_table_hash(source, ("ID",))
    identity = hashlib.sha256(
        b"cop-uci-academic-snapshot-v2\0"
        + _canonical_json(
            {
                "contract_sha256": contract_hash,
                "evaluation_sha256": evaluation_hash,
                "source_logical_sha256": source_logical_hash,
                "source_sha256": acquisition_manifest["source_file"]["sha256"],
            }
        )
    ).hexdigest()
    expected_id = f"{contract.dataset_id}-academic-{identity}"
    data_file = _parquet_manifest(data_path, modelable)
    audit_file = _parquet_manifest(audit_path, audit_only)
    expected_manifest = {
        "manifest_version": SNAPSHOT_MANIFEST_VERSION,
        "snapshot_id": expected_id,
        "dataset_id": contract.dataset_id,
        "accepted_use": "academic_baseline_only",
        "source_acquisition_id": acquisition_manifest["acquisition_id"],
        "source_sha256": acquisition_manifest["source_file"]["sha256"],
        "source_logical_sha256": source_logical_hash,
        "contract_sha256": contract_hash,
        "evaluation_id": report["evaluation_id"],
        "evaluation_sha256": evaluation_hash,
        "rows": len(source),
        "modelable_columns": list(modelable.columns),
        "audit_only_columns": list(audit_only.columns),
        "schema": inspect_schema(contract, source),
        "target": contract.raw["target"],
        "protected_or_sensitive_columns": sensitive,
        "file": data_file,
        "audit_only_file": audit_file,
        "files": {"modelable": data_file, "audit_only": audit_file},
        "prohibited_claims": [
            "temporal_validation",
            "longitudinal_monitoring",
            "production",
            "fairness",
            "real_credit_decisions",
        ],
    }
    if snapshot.name != expected_id or manifest != expected_manifest:
        raise EvaluationError("academic snapshot differs from verified inputs")
    return cast(dict[str, Any], manifest)


def _verified_academic_evaluation(
    contract: DatasetContract,
    acquisition: Path,
    frame: pd.DataFrame,
    evaluation: Path,
) -> dict[str, Any]:
    # Local import prevents the evaluator/ingestion module dependency from cycling.
    from cop.data.evaluation.evaluator import verify_evaluation

    report = verify_evaluation(contract, acquisition, frame, evaluation)
    required = ("provenance", "license", "target_definition", "schema")
    if any(report["capabilities"][name]["status"] != "pass" for name in required):
        raise EvaluationError("academic snapshot required gate is not pass")
    if report["capabilities"]["academic_modeling"]["status"] != "pass":
        raise EvaluationError("academic modeling capability is not pass")
    if report["academic_snapshot_authorized"] is not True:
        raise EvaluationError("academic snapshot is not authorized")
    return report


def _parquet_manifest(path: Path, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "physical_sha256": sha256_file(path),
        "logical_sha256": logical_table_hash(frame, ("ID",)),
    }
