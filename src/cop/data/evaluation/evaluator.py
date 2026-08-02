"""Deterministic independent capability evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from cop.data.evaluation.contract import (
    CAPABILITY_NAMES,
    CapabilityDecision,
    DatasetContract,
)
from cop.data.hashing import sha256_file
from cop.data.ingestion.uci_credit_card import inspect_schema, verify_acquisition

EVALUATION_MANIFEST_VERSION = 1


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _decision(status: str, reason: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"status": status, "reason": reason, "evidence": evidence}


def evaluate_candidate(
    contract: DatasetContract,
    acquisition: Path,
    frame: pd.DataFrame,
    output_root: Path,
) -> Path:
    """Evaluate every capability independently and persist deterministic evidence."""
    report = _build_report(contract, acquisition, frame)
    evaluation_id = cast(str, report["evaluation_id"])
    destination = output_root.resolve() / evaluation_id
    payload = _canonical_json(report) + b"\n"
    if destination.exists():
        verify_evaluation(contract, acquisition, frame, destination)
        return destination
    destination.mkdir(parents=True)
    report_path = destination / "evaluation.json"
    report_path.write_bytes(payload)
    (destination / "evaluation.sha256").write_text(
        f"{sha256_file(report_path)}  evaluation.json\n", encoding="utf-8"
    )
    return destination


def _build_report(
    contract: DatasetContract, acquisition: Path, frame: pd.DataFrame
) -> dict[str, Any]:
    source_manifest = verify_acquisition(contract, acquisition)
    schema = inspect_schema(contract, frame)
    declared = contract.capabilities
    provenance_pass = all(
        (
            source_manifest["publisher"] == contract.raw["publisher"],
            source_manifest["official_page_url"] == contract.raw["official_page_url"],
            source_manifest["official_download_url"]
            == contract.raw["official_download_url"],
            source_manifest["doi"] == contract.raw["doi"],
        )
    )
    license_pass = source_manifest["license"] == contract.raw["license"]
    schema_pass = bool(
        schema["rows_match"]
        and schema["columns_match"]
        and schema["missing_cells"] == 0
    )
    target_pass = bool(
        schema["target_values"] == [0, 1] and schema["target_missing"] == 0
    )

    actual_gates = {
        "provenance": provenance_pass,
        "license": license_pass,
        "schema": schema_pass,
        "target_definition": target_pass,
    }
    decisions: dict[str, dict[str, Any]] = {}
    for name in CAPABILITY_NAMES:
        configured: CapabilityDecision = declared[name]
        status = configured.status
        evidence: dict[str, Any] = {"declared_status": configured.status}
        if name in actual_gates:
            passed = actual_gates[name]
            status = configured.status if passed else "fail"
            evidence["verified"] = passed
        elif name == "academic_modeling":
            gate_statuses = {
                gate: decisions[gate]["status"]
                for gate in ("provenance", "license", "target_definition", "schema")
            }
            passed = all(value == "pass" for value in gate_statuses.values())
            status = configured.status if passed else "fail"
            evidence["required_gates"] = gate_statuses
        elif name == "public_portfolio_use":
            required = {
                gate: decisions[gate]["status"] for gate in ("provenance", "license")
            }
            passed = all(value == "pass" for value in required.values())
            status = configured.status if passed else "fail"
            evidence["required_gates"] = required
        decisions[name] = _decision(status, configured.reason, evidence)

    contract_hash = hashlib.sha256(contract.canonical_json().encode()).hexdigest()
    evaluation_id = (
        f"evaluation-{contract.dataset_id}-"
        f"{source_manifest['source_file']['sha256']}-{contract_hash}"
    )
    return {
        "evaluation_manifest_version": EVALUATION_MANIFEST_VERSION,
        "evaluation_id": evaluation_id,
        "dataset_id": contract.dataset_id,
        "acquisition_id": source_manifest["acquisition_id"],
        "source_sha256": source_manifest["source_file"]["sha256"],
        "contract_sha256": contract_hash,
        "schema_inspection": schema,
        "capabilities": decisions,
        "failed_capabilities": [
            name for name in CAPABILITY_NAMES if decisions[name]["status"] == "fail"
        ],
        "academic_snapshot_authorized": (
            decisions["academic_modeling"]["status"] == "pass"
        ),
    }


def load_evaluation(directory: Path) -> dict[str, Any]:
    report_path = directory / "evaluation.json"
    sidecar = (directory / "evaluation.sha256").read_text().split()
    if len(sidecar) != 2 or sidecar[1] != report_path.name:
        raise ValueError("invalid evaluation sidecar")
    if sidecar[0] != sha256_file(report_path):
        raise ValueError("evaluation hash mismatch")
    return cast(dict[str, Any], json.loads(report_path.read_text(encoding="utf-8")))


def verify_evaluation(
    contract: DatasetContract,
    acquisition: Path,
    frame: pd.DataFrame,
    directory: Path,
) -> dict[str, Any]:
    report = load_evaluation(directory)
    expected = _build_report(contract, acquisition, frame)
    if report != expected:
        raise ValueError("evaluation differs from current contract and source evidence")
    return report
