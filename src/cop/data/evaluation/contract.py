"""Strict machine-readable dataset evaluation contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from cop.data.yaml import StrictYamlError, UniqueKeyLoader

CapabilityStatus = Literal["pass", "limited", "needs_review", "fail", "not_applicable"]
ALLOWED_STATUSES = {
    "pass",
    "limited",
    "needs_review",
    "fail",
    "not_applicable",
}
CAPABILITY_NAMES = (
    "provenance",
    "license",
    "target_definition",
    "schema",
    "entity_identity",
    "timestamps",
    "temporal_split",
    "group_split",
    "academic_modeling",
    "longitudinal_monitoring",
    "public_portfolio_use",
    "production_claims",
)


class EvaluationError(ValueError):
    """Raised when a contract or candidate violates the evaluation protocol."""


@dataclass(frozen=True)
class CapabilityDecision:
    status: CapabilityStatus
    reason: str


@dataclass(frozen=True)
class DatasetContract:
    raw: dict[str, Any]

    @property
    def dataset_id(self) -> str:
        return cast(str, self.raw["dataset_id"])

    @property
    def output_root(self) -> Path:
        return Path(cast(str, self.raw["output_root"]))

    @property
    def snapshot_root(self) -> Path:
        return Path(cast(str, self.raw["snapshot_root"]))

    @property
    def capabilities(self) -> dict[str, CapabilityDecision]:
        raw_capabilities = cast(dict[str, dict[str, str]], self.raw["capabilities"])
        return {
            name: CapabilityDecision(
                cast(CapabilityStatus, value["status"]), value["reason"]
            )
            for name, value in raw_capabilities.items()
        }

    def canonical_json(self) -> str:
        normalized = dict(self.raw)
        normalized.pop("output_root", None)
        normalized.pop("snapshot_root", None)
        return json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def _validate(raw: dict[str, Any]) -> None:
    required = {
        "contract_version",
        "dataset_id",
        "dataset_title",
        "publisher",
        "official_page_url",
        "official_download_url",
        "doi",
        "license",
        "acquisition_date",
        "archive_filename",
        "source_filename",
        "source_member",
        "output_root",
        "snapshot_root",
        "expected_schema",
        "target",
        "entity",
        "timestamps",
        "protected_or_sensitive_columns",
        "academic_split",
        "capabilities",
    }
    _require(set(raw) == required, "contract top-level keys differ from version 1")
    _require(raw["contract_version"] == 1, "unsupported contract_version")
    _require(raw["dataset_id"] == "uci-default-credit-card", "unsafe dataset_id")
    download_url = raw["official_download_url"]
    _require(
        isinstance(download_url, str)
        and download_url.startswith("https://archive.ics.uci.edu/"),
        "download must use the official UCI HTTPS origin",
    )
    capabilities = raw["capabilities"]
    _require(isinstance(capabilities, dict), "capabilities must be a mapping")
    _require(
        tuple(capabilities) == CAPABILITY_NAMES,
        "capability names or ordering differ from contract",
    )
    for name, decision in capabilities.items():
        _require(isinstance(decision, dict), f"capability {name} must be a mapping")
        _require(set(decision) == {"status", "reason"}, f"invalid capability {name}")
        _require(decision["status"] in ALLOWED_STATUSES, f"invalid status for {name}")
        _require(bool(decision["reason"]), f"capability {name} requires a reason")
    fractions = raw["academic_split"]
    total = sum(
        float(fractions[key])
        for key in ("train_fraction", "validation_fraction", "test_fraction")
    )
    _require(abs(total - 1.0) < 1e-12, "academic split fractions must sum to one")


def load_dataset_contract(path: Path) -> DatasetContract:
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError, StrictYamlError) as exc:
        raise EvaluationError(f"cannot load dataset contract: {exc}") from exc
    if not isinstance(raw, dict):
        raise EvaluationError("dataset contract root must be a mapping")
    _validate(raw)
    return DatasetContract(cast(dict[str, Any], raw))
