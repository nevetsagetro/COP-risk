from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

import cop.data.evaluation.academic_splits as academic_splits_module
from cop.data.evaluation.academic_splits import (
    create_academic_splits,
    verify_academic_splits,
)
from cop.data.evaluation.contract import (
    DatasetContract,
    EvaluationError,
    load_dataset_contract,
)
from cop.data.evaluation.evaluator import (
    evaluate_candidate,
    load_evaluation,
    verify_evaluation,
)
from cop.data.ingestion.uci_credit_card import (
    acquire_official_dataset,
    materialize_academic_snapshot,
    verify_academic_snapshot,
    verify_acquisition,
)
from cop.data.synthetic.hashing import sha256_file

CONFIG = Path("configs/datasets/uci-default-credit-card.yaml")


def _contract(tmp_path: Path, name: str) -> DatasetContract:
    loaded = load_dataset_contract(CONFIG)
    raw = dict(loaded.raw)
    raw["expected_schema"] = dict(raw["expected_schema"])
    raw["expected_schema"]["rows"] = 300
    raw["output_root"] = str(tmp_path / name / "raw")
    raw["snapshot_root"] = str(tmp_path / name / "processed")
    return DatasetContract(raw)


def _archive() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("default of credit card clients.xls", b"fixture-xls")
    return stream.getvalue()


def _frame(contract: DatasetContract) -> pd.DataFrame:
    columns = contract.raw["expected_schema"]["columns"]
    data = {column: list(range(1, 301)) for column in columns}
    data["ID"] = list(range(1, 301))
    data["default_payment_next_month"] = [0] * 240 + [1] * 60
    return pd.DataFrame(data, columns=columns)


def test_acquisition_evaluation_snapshot_and_splits_are_reproducible(
    tmp_path: Path,
) -> None:
    first_contract = _contract(tmp_path, "first")
    second_contract = _contract(tmp_path, "second")
    payload = _archive()
    first_acquisition = acquire_official_dataset(first_contract, payload=payload)
    second_acquisition = acquire_official_dataset(second_contract, payload=payload)
    first_source = verify_acquisition(first_contract, first_acquisition)
    second_source = verify_acquisition(second_contract, second_acquisition)
    assert first_source["archive"]["sha256"] == second_source["archive"]["sha256"]
    assert first_source == second_source

    frame = _frame(first_contract)
    first_evaluation = evaluate_candidate(
        first_contract,
        first_acquisition,
        frame,
        first_contract.snapshot_root / "evaluations",
    )
    second_evaluation = evaluate_candidate(
        second_contract,
        second_acquisition,
        frame,
        second_contract.snapshot_root / "evaluations",
    )
    first_report = load_evaluation(first_evaluation)
    second_report = load_evaluation(second_evaluation)
    assert first_report == second_report
    statuses = {
        name: decision["status"]
        for name, decision in first_report["capabilities"].items()
    }
    assert statuses["academic_modeling"] == "pass"
    assert statuses["entity_identity"] == "limited"
    assert statuses["temporal_split"] == "fail"
    assert statuses["longitudinal_monitoring"] == "fail"
    assert statuses["production_claims"] == "fail"
    assert {
        "timestamps",
        "temporal_split",
        "longitudinal_monitoring",
        "production_claims",
    }.issubset(first_report["failed_capabilities"])

    first_snapshot = materialize_academic_snapshot(
        first_contract, first_acquisition, frame, first_evaluation
    )
    second_snapshot = materialize_academic_snapshot(
        second_contract, second_acquisition, frame, second_evaluation
    )
    first_snapshot_manifest = verify_academic_snapshot(
        first_contract, first_acquisition, first_evaluation, first_snapshot
    )
    second_snapshot_manifest = verify_academic_snapshot(
        second_contract, second_acquisition, second_evaluation, second_snapshot
    )
    assert (
        first_snapshot_manifest["file"]["logical_sha256"]
        == second_snapshot_manifest["file"]["logical_sha256"]
    )

    first_splits = create_academic_splits(
        first_contract,
        first_acquisition,
        first_snapshot,
        first_evaluation,
        first_contract.snapshot_root / "splits",
    )
    second_splits = create_academic_splits(
        second_contract,
        second_acquisition,
        second_snapshot,
        second_evaluation,
        second_contract.snapshot_root / "splits",
    )
    first_split_manifest = verify_academic_splits(
        first_contract,
        first_acquisition,
        first_snapshot,
        first_evaluation,
        first_splits,
    )
    second_split_manifest = verify_academic_splits(
        second_contract,
        second_acquisition,
        second_snapshot,
        second_evaluation,
        second_splits,
    )
    assert (
        first_split_manifest["logical_splits_sha256"]
        == second_split_manifest["logical_splits_sha256"]
    )
    assert first_split_manifest["id_intersections"] == 0
    assert sum(item["rows"] for item in first_split_manifest["files"].values()) == 300


def test_failed_schema_remains_visible_and_blocks_academic_snapshot(
    tmp_path: Path,
) -> None:
    contract = _contract(tmp_path, "failed")
    acquisition = acquire_official_dataset(contract, payload=_archive())
    invalid = _frame(contract).drop(columns=["LIMIT_BAL"])

    evaluation = evaluate_candidate(
        contract, acquisition, invalid, contract.snapshot_root / "evaluations"
    )
    report = load_evaluation(evaluation)

    assert report["capabilities"]["schema"]["status"] == "fail"
    assert report["capabilities"]["academic_modeling"]["status"] == "fail"
    assert "schema" in report["failed_capabilities"]
    assert report["academic_snapshot_authorized"] is False


@pytest.mark.parametrize("gate", ["provenance", "license"])
@pytest.mark.parametrize("status", ["limited", "needs_review", "fail"])
def test_documentary_gate_is_never_promoted_and_blocks_snapshot(
    tmp_path: Path, gate: str, status: str
) -> None:
    contract = _contract(tmp_path, f"{gate}-{status}")
    raw = dict(contract.raw)
    raw["capabilities"] = {
        name: dict(decision) for name, decision in raw["capabilities"].items()
    }
    raw["capabilities"][gate]["status"] = status
    contract = DatasetContract(raw)
    acquisition = acquire_official_dataset(contract, payload=_archive())
    frame = _frame(contract)

    evaluation = evaluate_candidate(
        contract, acquisition, frame, contract.snapshot_root / "evaluations"
    )
    report = verify_evaluation(contract, acquisition, frame, evaluation)

    assert report["capabilities"][gate]["status"] == status
    assert report["capabilities"]["academic_modeling"]["status"] == "fail"
    assert report["academic_snapshot_authorized"] is False
    with pytest.raises(EvaluationError, match="required gate"):
        materialize_academic_snapshot(contract, acquisition, frame, evaluation)


def test_snapshot_physically_separates_audit_only_columns(tmp_path: Path) -> None:
    contract = _contract(tmp_path, "audit-separation")
    acquisition = acquire_official_dataset(contract, payload=_archive())
    frame = _frame(contract)
    evaluation = evaluate_candidate(
        contract, acquisition, frame, contract.snapshot_root / "evaluations"
    )
    snapshot = materialize_academic_snapshot(contract, acquisition, frame, evaluation)

    modelable = pd.read_parquet(snapshot / "dataset.parquet")
    audit_only = pd.read_parquet(snapshot / "audit_only.parquet")
    sensitive = contract.raw["protected_or_sensitive_columns"]

    assert set(sensitive).isdisjoint(modelable.columns)
    assert list(audit_only.columns) == ["ID", *sensitive]
    assert modelable["ID"].is_unique and audit_only["ID"].is_unique
    assert set(modelable["ID"]) == set(audit_only["ID"])


def test_tampered_authorization_report_cannot_create_splits(tmp_path: Path) -> None:
    contract = _contract(tmp_path, "tampered-report")
    acquisition = acquire_official_dataset(contract, payload=_archive())
    frame = _frame(contract)
    evaluation = evaluate_candidate(
        contract, acquisition, frame, contract.snapshot_root / "evaluations"
    )
    snapshot = materialize_academic_snapshot(contract, acquisition, frame, evaluation)
    report_path = evaluation / "evaluation.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["capabilities"]["license"]["status"] = "fail"
    report_path.write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (evaluation / "evaluation.sha256").write_text(
        f"{sha256_file(report_path)}  evaluation.json\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="differs from current contract"):
        create_academic_splits(
            contract,
            acquisition,
            snapshot,
            evaluation,
            contract.snapshot_root / "splits",
        )


def test_changed_contract_invalidates_existing_acquisition(tmp_path: Path) -> None:
    contract = _contract(tmp_path, "changed-contract")
    acquisition = acquire_official_dataset(contract, payload=_archive())
    changed = dict(contract.raw)
    changed["doi"] = "changed-after-evaluation"

    with pytest.raises(EvaluationError, match="differs from contract"):
        verify_acquisition(DatasetContract(changed), acquisition)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorized_use", "production"),
        ("strategy", "unverified"),
        ("seed", 999),
        ("academic_split_version", 999),
        ("id_intersections", 1),
    ],
)
def test_split_manifest_authorization_fields_are_recomputed(
    tmp_path: Path, field: str, value: object
) -> None:
    contract = _contract(tmp_path, f"split-tamper-{field}")
    acquisition = acquire_official_dataset(contract, payload=_archive())
    frame = _frame(contract)
    evaluation = evaluate_candidate(
        contract, acquisition, frame, contract.snapshot_root / "evaluations"
    )
    snapshot = materialize_academic_snapshot(contract, acquisition, frame, evaluation)
    splits = create_academic_splits(
        contract,
        acquisition,
        snapshot,
        evaluation,
        contract.snapshot_root / "splits",
    )
    manifest_path = splits / "split-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[field] = value
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (splits / "split-manifest.sha256").write_text(
        f"{sha256_file(manifest_path)}  split-manifest.json\n", encoding="utf-8"
    )

    with pytest.raises(EvaluationError, match="manifest metadata mismatch"):
        verify_academic_splits(contract, acquisition, snapshot, evaluation, splits)


def test_interrupted_split_write_leaves_no_partial_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _contract(tmp_path, "atomic-splits")
    acquisition = acquire_official_dataset(contract, payload=_archive())
    frame = _frame(contract)
    evaluation = evaluate_candidate(
        contract, acquisition, frame, contract.snapshot_root / "evaluations"
    )
    snapshot = materialize_academic_snapshot(contract, acquisition, frame, evaluation)
    destination = contract.snapshot_root / "splits" / f"academic-splits-{snapshot.name}"
    original_write = getattr(academic_splits_module, "_write_split_files")

    def interrupted_write(*args: object, **kwargs: object) -> None:
        original_write(*args, **kwargs)
        raise OSError("simulated interruption")

    monkeypatch.setattr(academic_splits_module, "_write_split_files", interrupted_write)
    with pytest.raises(OSError, match="simulated interruption"):
        create_academic_splits(
            contract,
            acquisition,
            snapshot,
            evaluation,
            contract.snapshot_root / "splits",
        )
    assert not destination.exists()

    monkeypatch.setattr(academic_splits_module, "_write_split_files", original_write)
    assert create_academic_splits(
        contract,
        acquisition,
        snapshot,
        evaluation,
        contract.snapshot_root / "splits",
    ).is_dir()
