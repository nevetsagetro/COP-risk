from pathlib import Path

import pytest

from cop.data.splitting.synthetic import SPLIT_NAMES, SplitError, split_tables
from cop.data.synthetic.config import load_config
from cop.data.synthetic.generator import generate_tables

FIXTURE = Path("tests/fixtures/synthetic-small.yaml")


def test_splits_are_temporal_mature_and_borrower_disjoint() -> None:
    config = load_config(FIXTURE)
    result = split_tables(generate_tables(config).applications, config)

    assert tuple(result.frames) == SPLIT_NAMES
    assert result.purge_rows > 0
    seen_borrowers: set[str] = set()
    seen_applications: set[str] = set()
    seen_fingerprints: set[str] = set()
    for name in SPLIT_NAMES:
        frame = result.frames[name]
        assert not frame.empty
        assert set(frame["label_status"]) == {"mature"}
        assert frame["default_within_horizon"].notna().all()
        borrowers = set(frame["borrower_id"])
        applications = set(frame["application_id"])
        fingerprints = set(frame["observation_fingerprint"])
        assert not seen_borrowers & borrowers
        assert not seen_applications & applications
        assert not seen_fingerprints & fingerprints
        seen_borrowers |= borrowers
        seen_applications |= applications
        seen_fingerprints |= fingerprints


def test_same_snapshot_produces_identical_split_tables() -> None:
    config = load_config(FIXTURE)
    applications = generate_tables(config).applications

    first = split_tables(applications, config)
    second = split_tables(applications.sample(frac=1, random_state=7), config)

    assert first.purge_rows == second.purge_rows
    assert first.purge_borrowers == second.purge_borrowers
    for name in SPLIT_NAMES:
        assert first.frames[name].equals(second.frames[name])


def test_content_clone_under_different_ids_is_rejected() -> None:
    config = load_config(FIXTURE)
    applications = generate_tables(config).applications.copy()
    source = applications.iloc[0]
    clone_index = applications.index[-1]
    preserved_ids = applications.loc[clone_index, ["application_id", "borrower_id"]]
    applications.loc[clone_index] = source
    applications.loc[clone_index, ["application_id", "borrower_id"]] = preserved_ids

    with pytest.raises(SplitError, match="fingerprint"):
        split_tables(applications, config)
