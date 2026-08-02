"""Snapshot serialization, manifest creation, and verification."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from cop.data.schemas.synthetic import (
    FEATURE_AVAILABILITY,
    FEATURE_DEPENDENCIES,
    INPUT_FEATURE_COLUMNS,
)
from cop.data.synthetic.config import SyntheticConfig
from cop.data.synthetic.generator import (
    RNG_DERIVATION_ALGORITHM,
    RNG_NAMESPACES,
    GeneratedTables,
    generate_tables,
)
from cop.data.synthetic.hashing import (
    LOGICAL_HASH_ALGORITHM,
    logical_snapshot_hash,
    logical_table_hash,
    sha256_file,
)
from cop.data.validation.synthetic import ValidationError, validate_snapshot

GENERATOR_VERSION = "1.1.0"
MANIFEST_VERSION = 1
TABLE_KEYS: dict[str, tuple[str, ...]] = {
    "applications": ("application_id",),
    "ledger": ("application_id", "installment_number"),
    "audit_only": ("application_id",),
}


class SnapshotError(RuntimeError):
    """Raised for unsafe writes or failed snapshot verification."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def config_hash(config: SyntheticConfig) -> str:
    return hashlib.sha256(config.canonical_json().encode()).hexdigest()


def generator_code_hash() -> str:
    """Hash every repository module that determines synthetic snapshot content."""
    data_root = Path(__file__).parents[1]
    paths = (
        data_root / "schemas" / "synthetic.py",
        data_root / "synthetic" / "config.py",
        data_root / "synthetic" / "generator.py",
        data_root / "synthetic" / "hashing.py",
        data_root / "synthetic" / "snapshot.py",
        data_root / "validation" / "synthetic.py",
    )
    digest = hashlib.sha256(b"cop-generator-code-v1\0")
    for path in paths:
        relative = path.relative_to(data_root)
        digest.update(str(relative).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def snapshot_id(config: SyntheticConfig) -> str:
    cutoff = pd.Timestamp(config.snapshot_as_of).strftime("%Y%m%dT%H%M%SZ")
    identity = hashlib.sha256(
        b"cop-synthetic-snapshot-v1\0"
        + config.canonical_json().encode()
        + b"\0"
        + generator_code_hash().encode()
    ).hexdigest()
    return f"{config.dataset_version}-{cutoff}-{identity}"


def _schema_description(table: pa.Table) -> list[dict[str, Any]]:
    return [
        {
            "name": field.name,
            "type": str(field.type),
            "nullable": field.nullable,
        }
        for field in table.schema.remove_metadata()
    ]


def _write_table(
    frame: pd.DataFrame,
    path: Path,
    config: SyntheticConfig,
    primary_key: tuple[str, ...],
) -> dict[str, Any]:
    ordered = frame.sort_values(list(primary_key), kind="mergesort").reset_index(
        drop=True
    )
    table = pa.Table.from_pandas(ordered, preserve_index=False)
    pq.write_table(
        table,
        path,
        compression=config.parquet_compression,
        compression_level=config.parquet_compression_level,
        row_group_size=config.parquet_row_group_size,
        version="2.6",
        data_page_version="2.0",
        use_dictionary=True,
        write_statistics=True,
        coerce_timestamps="us",
        allow_truncated_timestamps=False,
        use_compliant_nested_type=True,
    )
    persisted = pd.read_parquet(path)
    persisted_table = pq.read_table(path)
    return {
        "path": path.name,
        "rows": len(ordered),
        "bytes": path.stat().st_size,
        "primary_key": list(primary_key),
        "canonical_order": list(primary_key),
        "schema": _schema_description(persisted_table),
        "physical_sha256": sha256_file(path),
        "logical_sha256": logical_table_hash(persisted, primary_key),
        "logical_hash_algorithm": LOGICAL_HASH_ALGORITHM,
    }


def _persisted_file_metadata(
    frame: pd.DataFrame, path: Path, primary_key: tuple[str, ...]
) -> dict[str, Any]:
    table = pq.read_table(path)
    return {
        "path": path.name,
        "rows": len(frame),
        "bytes": path.stat().st_size,
        "primary_key": list(primary_key),
        "canonical_order": list(primary_key),
        "schema": _schema_description(table),
        "physical_sha256": sha256_file(path),
        "logical_sha256": logical_table_hash(frame, primary_key),
        "logical_hash_algorithm": LOGICAL_HASH_ALGORITHM,
    }


def _manifest(
    config: SyntheticConfig,
    files: dict[str, dict[str, Any]],
    tables: GeneratedTables,
) -> dict[str, Any]:
    table_hashes = {
        name: str(metadata["logical_sha256"]) for name, metadata in files.items()
    }
    status_counts = (
        tables.applications["label_status"].value_counts().sort_index().to_dict()
    )
    mature = tables.applications.loc[
        tables.applications["label_status"] == "mature",
        "default_within_horizon",
    ]
    borrower_frequency = tables.applications["borrower_id"].value_counts()
    frequency_distribution = borrower_frequency.value_counts().sort_index().to_dict()
    return {
        "manifest_version": MANIFEST_VERSION,
        "snapshot_id": snapshot_id(config),
        "snapshot_as_of": config.snapshot_as_of,
        "seed": config.seed,
        "generator_version": GENERATOR_VERSION,
        "generator_code_sha256": generator_code_hash(),
        "dataset_version": config.dataset_version,
        "schema_version": config.schema_version,
        "configuration": config.normalized(),
        "configuration_sha256": config_hash(config),
        "logical_hash_algorithm": LOGICAL_HASH_ALGORITHM,
        "logical_snapshot_sha256": logical_snapshot_hash(table_hashes),
        "row_counts": {
            "applications": len(tables.applications),
            "ledger": len(tables.ledger),
            "audit_only": len(tables.audit_only),
        },
        "entity_counts": {"borrowers": tables.applications["borrower_id"].nunique()},
        "borrower_application_distribution": {
            "borrowers_by_application_count": {
                str(key): int(value) for key, value in frequency_distribution.items()
            },
            "mean_applications_per_repeated_borrower": round(
                float(borrower_frequency.loc[borrower_frequency > 1].mean()), 8
            ),
            "maximum_applications_per_borrower": int(borrower_frequency.max()),
        },
        "label_counts": {str(key): int(value) for key, value in status_counts.items()},
        "mature_positive_rate": (
            None if mature.empty else round(float(mature.mean()), 8)
        ),
        "feature_availability_contract": {
            "rule": "available_at <= decision_timestamp",
            "source": "cop.data.schemas.synthetic.FEATURE_AVAILABILITY",
            "input_features": list(INPUT_FEATURE_COLUMNS),
            "availability": FEATURE_AVAILABILITY,
            "dependencies": {
                key: list(value) for key, value in FEATURE_DEPENDENCIES.items()
            },
        },
        "roles_and_lineage": {
            "applications": "decision-time inputs and nullable derived label",
            "ledger": "post-decision schedule and payment outcomes; target source",
            "audit_only": "protected synthetic attributes; prohibited as inputs",
            "target_derivation": (
                "ledger.days_past_due >= default_dpd_threshold within horizon"
            ),
        },
        "rng": {
            "algorithm": RNG_DERIVATION_ALGORITHM,
            "master_seed": config.seed,
            "namespaces": list(RNG_NAMESPACES),
        },
        "temporal_ranges": {
            "decision_timestamp": {
                "minimum": tables.applications["decision_timestamp"].min().isoformat(),
                "maximum": tables.applications["decision_timestamp"].max().isoformat(),
            },
            "snapshot_as_of": config.snapshot_as_of,
        },
        "reconciliation": {
            "repeated_borrowers": int(
                (tables.applications["borrower_id"].value_counts() > 1).sum()
            ),
            "duplicate_applications": int(tables.applications.duplicated().sum()),
            "duplicate_ledger_rows": int(tables.ledger.duplicated().sum()),
            "excluded_from_known_labels": {
                "immature": int(status_counts.get("immature", 0)),
                "censored": int(status_counts.get("censored", 0)),
            },
        },
        "provenance": {
            "provenance": "project-generated synthetic data",
            "source_data": "none",
            "external_data_dependencies": "none",
            "training_use": "approved_for_local_demo",
            "real_credit_use": "prohibited",
            "redistribution": "pending_project_license",
            "publication_claims": "restricted_to_synthetic_engineering_demo",
            "source_version": GENERATOR_VERSION,
            "source_code_sha256": generator_code_hash(),
            "source_commit": None,
            "source_state": "uncommitted-development",
        },
        "files": files,
        "parquet": {
            "compression": config.parquet_compression,
            "compression_level": config.parquet_compression_level,
            "row_group_size": config.parquet_row_group_size,
            "version": "2.6",
            "data_page_version": "2.0",
            "timestamp_unit": "us",
        },
        "toolchain": {
            "pandas": importlib.metadata.version("pandas"),
            "numpy": importlib.metadata.version("numpy"),
            "pyarrow": importlib.metadata.version("pyarrow"),
            "PyYAML": importlib.metadata.version("PyYAML"),
        },
    }


def _write_snapshot_content(directory: Path, config: SyntheticConfig) -> dict[str, Any]:
    tables = generate_tables(config)
    validate_snapshot(tables, config)
    files: dict[str, dict[str, Any]] = {}
    for name, frame in (
        ("applications", tables.applications),
        ("ledger", tables.ledger),
        ("audit_only", tables.audit_only),
    ):
        files[name] = _write_table(
            frame, directory / f"{name}.parquet", config, TABLE_KEYS[name]
        )
    manifest = _manifest(config, files, tables)
    manifest_path = directory / "manifest.json"
    manifest_path.write_bytes(_canonical_json(manifest) + b"\n")
    (directory / "manifest.sha256").write_text(
        f"{sha256_file(manifest_path)}  manifest.json\n", encoding="utf-8"
    )
    return manifest


def _safe_existing_destination(destination: Path, expected_id: str) -> None:
    if destination.is_symlink() or not destination.is_dir():
        raise SnapshotError("existing destination is not a safe snapshot directory")
    manifest_path = destination / "manifest.json"
    if not manifest_path.is_file():
        raise SnapshotError("refusing to replace a directory without COP manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError("existing manifest is unreadable") from exc
    if manifest.get("snapshot_id") != expected_id:
        raise SnapshotError("existing directory belongs to another snapshot")


def generate_snapshot(
    config: SyntheticConfig, output_root: Path, *, force: bool = False
) -> Path:
    """Generate, verify, and atomically publish a snapshot directory."""
    if output_root.is_symlink():
        raise SnapshotError("output root must not be a symlink")
    root = output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    identifier = snapshot_id(config)
    destination = root / identifier
    lock = root / f".{identifier}.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise SnapshotError(
            f"snapshot generation is already running: {identifier}"
        ) from exc

    staging: Path | None = None
    backup = root / f".{identifier}.backup"
    try:
        if destination.exists() and not force:
            raise SnapshotError(
                f"snapshot already exists: {destination}; pass --force explicitly"
            )
        if destination.exists():
            _safe_existing_destination(destination, identifier)
            verify_snapshot(destination)
        staging = Path(tempfile.mkdtemp(prefix=f".{identifier}.tmp-", dir=root))
        _write_snapshot_content(staging, config)
        verify_snapshot(staging)
        if destination.exists():
            if backup.exists():
                raise SnapshotError("stale backup prevents safe replacement")
            destination.rename(backup)
        try:
            staging.rename(destination)
        except Exception:
            if backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        directory_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return destination
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        if lock.exists():
            lock.rmdir()


def _load_frames(directory: Path) -> GeneratedTables:
    return GeneratedTables(
        applications=pd.read_parquet(directory / "applications.parquet"),
        ledger=pd.read_parquet(directory / "ledger.parquet"),
        audit_only=pd.read_parquet(directory / "audit_only.parquet"),
    )


def verify_snapshot(directory: Path) -> dict[str, Any]:
    """Recompute manifest, physical hashes, logical hashes, and contract checks."""
    if directory.is_symlink():
        raise SnapshotError("snapshot path must not be a symlink")
    root = directory.resolve()
    if not root.is_dir():
        raise SnapshotError("snapshot path must be a real directory")
    expected_names = {
        "applications.parquet",
        "ledger.parquet",
        "audit_only.parquet",
        "manifest.json",
        "manifest.sha256",
    }
    actual_names = {path.name for path in root.iterdir()}
    if actual_names != expected_names:
        raise SnapshotError("snapshot inventory differs from manifest contract")
    sidecar = (root / "manifest.sha256").read_text(encoding="utf-8").split()
    if len(sidecar) != 2 or sidecar[1] != "manifest.json":
        raise SnapshotError("manifest sidecar is invalid")
    if sidecar[0] != sha256_file(root / "manifest.json"):
        raise SnapshotError("manifest hash mismatch")
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        config_mapping = dict(manifest["configuration"])
        config_mapping["output_root"] = "."
        config = SyntheticConfig.from_mapping(config_mapping)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SnapshotError("manifest content is invalid") from exc
    if manifest["snapshot_id"] != snapshot_id(config):
        raise SnapshotError("snapshot identity mismatch")
    if root.name != manifest["snapshot_id"] and not root.name.startswith(
        f".{manifest['snapshot_id']}.tmp-"
    ):
        raise SnapshotError("snapshot directory name does not match identity")

    try:
        frames = _load_frames(root)
    except Exception as exc:
        raise SnapshotError("snapshot Parquet content is unreadable") from exc
    try:
        validate_snapshot(frames, config)
    except ValidationError as exc:
        raise SnapshotError(f"contract validation failed: {exc}") from exc
    recomputed_files: dict[str, dict[str, Any]] = {}
    for name, frame in (
        ("applications", frames.applications),
        ("ledger", frames.ledger),
        ("audit_only", frames.audit_only),
    ):
        metadata = manifest["files"][name]
        path = root / metadata["path"]
        if path.parent != root:
            raise SnapshotError("manifest contains unsafe file path")
        if sha256_file(path) != metadata["physical_sha256"]:
            raise SnapshotError(f"physical hash mismatch: {name}")
        logical = logical_table_hash(frame, TABLE_KEYS[name])
        if logical != metadata["logical_sha256"]:
            raise SnapshotError(f"logical hash mismatch: {name}")
        if len(frame) != metadata["rows"]:
            raise SnapshotError(f"row count mismatch: {name}")
        recomputed_files[name] = _persisted_file_metadata(frame, path, TABLE_KEYS[name])
    expected_manifest = _manifest(config, recomputed_files, frames)
    if manifest != expected_manifest:
        raise SnapshotError("manifest metadata differs from recomputed snapshot")
    return cast(dict[str, Any], manifest)
