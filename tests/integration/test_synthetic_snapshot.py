import hashlib
import json
from pathlib import Path

import pytest

from cop.data.synthetic.config import load_config
from cop.data.synthetic.snapshot import (
    SnapshotError,
    generate_snapshot,
    verify_snapshot,
)

FIXTURE = Path("tests/fixtures/synthetic-small.yaml")


def test_two_equivalent_snapshots_have_same_hashes(tmp_path: Path) -> None:
    config = load_config(FIXTURE)
    first = generate_snapshot(config, tmp_path / "first")
    second = generate_snapshot(config, tmp_path / "second")

    first_manifest = verify_snapshot(first)
    second_manifest = verify_snapshot(second)
    assert first_manifest["snapshot_id"] == second_manifest["snapshot_id"]
    assert (
        first_manifest["logical_snapshot_sha256"]
        == second_manifest["logical_snapshot_sha256"]
    )
    for table in ("applications", "ledger", "audit_only"):
        assert (
            first_manifest["files"][table]["physical_sha256"]
            == second_manifest["files"][table]["physical_sha256"]
        )
        assert (
            first_manifest["files"][table]["logical_sha256"]
            == second_manifest["files"][table]["logical_sha256"]
        )


def test_existing_snapshot_requires_force(tmp_path: Path) -> None:
    config = load_config(FIXTURE)
    destination = generate_snapshot(config, tmp_path)

    with pytest.raises(SnapshotError, match="already exists"):
        generate_snapshot(config, tmp_path)

    replaced = generate_snapshot(config, tmp_path, force=True)
    assert replaced == destination
    verify_snapshot(replaced)


def test_corrupted_file_fails_verification(tmp_path: Path) -> None:
    config = load_config(FIXTURE)
    destination = generate_snapshot(config, tmp_path)
    applications = destination / "applications.parquet"
    payload = bytearray(applications.read_bytes())
    payload[len(payload) // 2] ^= 1
    applications.write_bytes(payload)

    with pytest.raises(SnapshotError, match="physical hash mismatch"):
        verify_snapshot(destination)


def test_tampered_manifest_metadata_fails_even_with_updated_sidecar(
    tmp_path: Path,
) -> None:
    destination = generate_snapshot(load_config(FIXTURE), tmp_path)
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["row_counts"]["applications"] += 1
    payload = (
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()
    manifest_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (destination / "manifest.sha256").write_text(
        f"{digest}  manifest.json\n", encoding="utf-8"
    )

    with pytest.raises(SnapshotError, match="metadata differs"):
        verify_snapshot(destination)


@pytest.mark.parametrize("mutation", ["corrupt", "extra"])
def test_force_refuses_unverified_existing_snapshot(
    tmp_path: Path, mutation: str
) -> None:
    config = load_config(FIXTURE)
    destination = generate_snapshot(config, tmp_path)
    if mutation == "corrupt":
        path = destination / "applications.parquet"
        path.write_bytes(path.read_bytes() + b"corrupt")
    else:
        (destination / "unexpected.txt").write_text("do not delete", encoding="utf-8")

    with pytest.raises(SnapshotError):
        generate_snapshot(config, tmp_path, force=True)
    assert destination.exists()


def test_symlink_snapshot_is_rejected(tmp_path: Path) -> None:
    destination = generate_snapshot(load_config(FIXTURE), tmp_path / "real")
    link = tmp_path / "snapshot-link"
    link.symlink_to(destination, target_is_directory=True)

    with pytest.raises(SnapshotError, match="symlink"):
        verify_snapshot(link)


def test_force_rolls_back_if_publish_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_config(FIXTURE)
    destination = generate_snapshot(config, tmp_path)
    original_hash = verify_snapshot(destination)["logical_snapshot_sha256"]
    original_rename = Path.rename

    def fail_staging_publish(source: Path, target: Path) -> Path:
        if ".tmp-" in source.name and target == destination:
            raise OSError("injected publish failure")
        return original_rename(source, target)

    monkeypatch.setattr(Path, "rename", fail_staging_publish)
    with pytest.raises(OSError, match="injected"):
        generate_snapshot(config, tmp_path, force=True)

    assert verify_snapshot(destination)["logical_snapshot_sha256"] == original_hash
