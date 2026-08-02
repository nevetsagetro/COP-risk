from pathlib import Path

from cop.data.splitting.synthetic import create_splits, verify_splits
from cop.data.synthetic.config import load_config
from cop.data.synthetic.snapshot import generate_snapshot

FIXTURE = Path("tests/fixtures/synthetic-small.yaml")


def test_split_artifacts_and_hashes_are_reproducible(tmp_path: Path) -> None:
    snapshot = generate_snapshot(load_config(FIXTURE), tmp_path / "snapshots")
    first = create_splits(snapshot, tmp_path / "first")
    second = create_splits(snapshot, tmp_path / "second")

    first_manifest = verify_splits(snapshot, first)
    second_manifest = verify_splits(snapshot, second)
    assert (
        first_manifest["logical_splits_sha256"]
        == second_manifest["logical_splits_sha256"]
    )
    assert first_manifest["intersection_checks"] == {
        "borrower_id": 0,
        "application_id": 0,
        "observation_fingerprint": 0,
    }
    assert first_manifest["test_access"].startswith("sealed")
    assert set(first_manifest["files"]) == {
        "train",
        "validation",
        "calibration",
        "threshold",
        "test",
    }
