from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest
import yaml

import cop.training.uci_baseline as baseline_module
from cop.data.hashing import sha256_file
from cop.features.uci import UCI_APPROVED_FEATURES, UCI_CATEGORICAL_FEATURES
from cop.training.uci_baseline import finalize_test, train_development

SOURCE_CONFIG = Path("configs/training/uci-baseline.yaml")
TARGET = "default_payment_next_month"


def _canonical_json(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        + b"\n"
    )


def _write_manifest(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes(_canonical_json(value))
    path.with_suffix(".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n", encoding="utf-8"
    )


def _fixture(tmp_path: Path, name: str = "fixture") -> Path:
    root = tmp_path / name
    snapshot = root / "data" / "snapshot"
    splits = root / "data" / "splits"
    snapshot.mkdir(parents=True)
    splits.mkdir(parents=True)
    rows = 100
    identifiers = np.arange(1, rows + 1)
    values: dict[str, Any] = {"ID": identifiers}
    for position, feature in enumerate(UCI_APPROVED_FEATURES):
        values[feature] = identifiers * (position + 1)
    for position, feature in enumerate(UCI_CATEGORICAL_FEATURES):
        values[feature] = (identifiers + position) % 5 - 2
    values[TARGET] = identifiers % 2
    dataset = pd.DataFrame(values, columns=["ID", *UCI_APPROVED_FEATURES, TARGET])
    dataset_path = snapshot / "dataset.parquet"
    dataset.to_parquet(dataset_path, index=False)
    (snapshot / "audit_only.parquet").write_bytes(b"must-not-open")
    snapshot_id = f"uci-test-{name}"
    logical_snapshot = "a" * 64
    snapshot_manifest = {
        "snapshot_id": snapshot_id,
        "accepted_use": "academic_baseline_only",
        "modelable_columns": ["ID", *UCI_APPROVED_FEATURES, TARGET],
        "audit_only_columns": ["ID", "SEX", "EDUCATION", "MARRIAGE", "AGE"],
        "file": {
            "path": "dataset.parquet",
            "physical_sha256": sha256_file(dataset_path),
            "logical_sha256": logical_snapshot,
        },
    }
    _write_manifest(snapshot / "snapshot-manifest.json", snapshot_manifest)

    assignments = {
        "train": dataset.loc[:59, ["ID", TARGET]],
        "validation": dataset.loc[60:79, ["ID", TARGET]],
        "test": dataset.loc[80:, ["ID", TARGET]],
    }
    files: dict[str, Any] = {}
    for split_name, frame in assignments.items():
        path = splits / f"{split_name}.parquet"
        frame.to_parquet(path, index=False)
        files[split_name] = {
            "path": path.name,
            "physical_sha256": sha256_file(path),
            "logical_sha256": split_name[0] * 64,
            "rows": len(frame),
            "class_counts": {"0": len(frame) // 2, "1": len(frame) // 2},
        }
    logical_splits = "b" * 64
    split_manifest_path = splits / "split-manifest.json"
    _write_manifest(
        split_manifest_path,
        {
            "snapshot_id": snapshot_id,
            "authorized_use": "academic_baseline_only",
            "logical_splits_sha256": logical_splits,
            "files": files,
        },
    )

    raw = yaml.safe_load(SOURCE_CONFIG.read_text(encoding="utf-8"))
    raw["snapshot"] = {
        "directory": str(snapshot.relative_to(root)),
        "snapshot_id": snapshot_id,
        "logical_sha256": logical_snapshot,
    }
    raw["splits"] = {
        "directory": str(splits.relative_to(root)),
        "manifest_sha256": sha256_file(split_manifest_path),
        "logical_sha256": logical_splits,
        "development_files": {name: files[name] for name in ("train", "validation")},
    }
    raw["run_root"] = "runs"
    config = root / "configs" / "training" / "uci-baseline.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return config


def test_development_never_opens_test_audit_or_snapshot_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture(tmp_path)
    original = cast(Any, pd.read_parquet)
    calls: list[tuple[Path, object, object]] = []

    def spy(path: object, *args: object, **kwargs: object) -> pd.DataFrame:
        calls.append(
            (Path(path), kwargs.get("columns"), kwargs.get("filters"))  # type: ignore[arg-type]
        )
        return cast(pd.DataFrame, original(path, *args, **kwargs))

    monkeypatch.setattr(pd, "read_parquet", spy)
    run = train_development(config)

    names = [path.name for path, _, _ in calls]
    assert "train.parquet" in names and "validation.parquet" in names
    assert "test.parquet" not in names and "audit_only.parquet" not in names
    dataset_calls = [
        (columns, filters)
        for path, columns, filters in calls
        if path.name == "dataset.parquet"
    ]
    assert len(dataset_calls) == 1
    assert dataset_calls[0][0] == ["ID", *UCI_APPROVED_FEATURES]
    assert isinstance(dataset_calls[0][0], list)
    assert TARGET not in dataset_calls[0][0]
    assert dataset_calls[0][1]
    results = json.loads((run / "validation-results.json").read_text(encoding="utf-8"))
    assert results["fit_split"] == "train"
    assert results["evaluation_split"] == "validation"
    assert set(results["models"]) == {"logistic_regression", "lightgbm"}
    assert not (run / baseline_module.CLAIM_FILE).exists()
    manifest = json.loads((run / "run-manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["splits"]["files"]) == {"train", "validation"}
    assert manifest["test_status"] == "unopened"


def test_tampered_model_blocks_before_test_open_or_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture(tmp_path)
    run = train_development(config)
    model = run / "logistic_regression.joblib"
    model.chmod(0o644)
    model.write_bytes(model.read_bytes() + b"tampered")
    original = cast(Any, pd.read_parquet)
    test_opened = False

    def spy(path: object, *args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal test_opened
        if Path(path).name == "test.parquet":  # type: ignore[arg-type]
            test_opened = True
        return cast(pd.DataFrame, original(path, *args, **kwargs))

    monkeypatch.setattr(pd, "read_parquet", spy)
    with pytest.raises(ValueError, match="model artifact hash mismatch"):
        finalize_test(config)
    assert test_opened is False
    assert not (run / baseline_module.CLAIM_FILE).exists()


def test_finalize_claims_before_one_test_open_and_cannot_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture(tmp_path)
    run = train_development(config)
    original = cast(Any, pd.read_parquet)
    test_opens = 0

    def spy(path: object, *args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal test_opens
        if Path(path).name == "test.parquet":  # type: ignore[arg-type]
            assert (run / baseline_module.CLAIM_FILE).is_file()
            test_opens += 1
        return cast(pd.DataFrame, original(path, *args, **kwargs))

    monkeypatch.setattr(pd, "read_parquet", spy)
    result_path = finalize_test(config)

    assert result_path.name == baseline_module.FINAL_RESULTS_FILE
    assert test_opens == 1
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["evaluation_split"] == "test"
    assert result["test_prevalence"] == 0.5
    with pytest.raises(RuntimeError, match="already been consumed"):
        finalize_test(config)
    assert test_opens == 1


def test_interrupted_finalize_consumes_claim_and_blocks_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _fixture(tmp_path)
    run = train_development(config)

    def interrupted(_: object) -> None:
        raise OSError("simulated failure after claim")

    monkeypatch.setattr(baseline_module, "_load_test_data", interrupted)
    with pytest.raises(OSError, match="after claim"):
        finalize_test(config)
    assert (run / baseline_module.CLAIM_FILE).is_file()
    with pytest.raises(RuntimeError, match="already been consumed"):
        finalize_test(config)


def test_development_metrics_are_reproducible(tmp_path: Path) -> None:
    first = train_development(_fixture(tmp_path, "first"))
    second = train_development(_fixture(tmp_path, "second"))

    first_results = json.loads(
        (first / "validation-results.json").read_text(encoding="utf-8")
    )
    second_results = json.loads(
        (second / "validation-results.json").read_text(encoding="utf-8")
    )
    assert first_results == second_results
