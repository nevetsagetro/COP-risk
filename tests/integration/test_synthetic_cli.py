import subprocess
import sys
from pathlib import Path


def test_cli_generates_and_verifies_snapshot(tmp_path: Path) -> None:
    command = [
        sys.executable,
        "scripts/generate_synthetic_snapshot.py",
        "--config",
        "tests/fixtures/synthetic-small.yaml",
        "--output-root",
        str(tmp_path),
    ]
    generated = subprocess.run(command, check=False, capture_output=True, text=True)

    assert generated.returncode == 0, generated.stderr
    snapshot = next(path for path in tmp_path.iterdir() if path.is_dir())
    verified = subprocess.run(
        [
            sys.executable,
            "scripts/generate_synthetic_snapshot.py",
            "--verify",
            str(snapshot),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert verified.returncode == 0, verified.stderr
    assert "Verified snapshot" in verified.stdout


def test_cli_reports_malformed_manifest_without_traceback(tmp_path: Path) -> None:
    snapshot = tmp_path / "broken"
    snapshot.mkdir()
    for name in ("applications.parquet", "ledger.parquet", "audit_only.parquet"):
        (snapshot / name).write_bytes(b"invalid")
    (snapshot / "manifest.json").write_text("{", encoding="utf-8")
    (snapshot / "manifest.sha256").write_text(
        "invalid  manifest.json\n", encoding="utf-8"
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_synthetic_snapshot.py",
            "--verify",
            str(snapshot),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
