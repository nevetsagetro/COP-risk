from __future__ import annotations

from pathlib import Path

from scripts.evaluate_home_credit_candidate import evaluate_candidate


def test_missing_home_credit_acquisition_is_blocked_without_download(
    tmp_path: Path,
) -> None:
    report = evaluate_candidate(tmp_path / "missing")

    assert report["status"] == "blocked_no_local_acquisition"
    assert report["download_performed"] is False
    assert report["acceptance_status"] == "not_accepted"
