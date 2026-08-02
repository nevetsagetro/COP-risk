"""Strict loading and canonicalization for synthetic generator configuration."""

from __future__ import annotations

import json
import re
from calendar import monthrange
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when generator configuration is invalid."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)  # type: ignore[no-untyped-call]
        if not isinstance(key, str):
            raise ConfigError("configuration keys must be strings")
        if key in mapping:
            raise ConfigError(f"duplicate configuration key: {key}")
        mapping[key] = loader.construct_object(  # type: ignore[no-untyped-call]
            value_node, deep=deep
        )
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _utc_timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ConfigError(f"{field} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConfigError(f"{field} is not a valid timestamp") from exc
    if parsed.tzinfo != UTC:
        raise ConfigError(f"{field} must use UTC")
    return parsed


def _add_calendar_months(value: datetime, months: int) -> datetime:
    absolute_month = value.year * 12 + value.month - 1 + months
    year, zero_based_month = divmod(absolute_month, 12)
    month = zero_based_month + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


@dataclass(frozen=True)
class SyntheticConfig:
    """Fully resolved synthetic-v1 configuration."""

    config_version: int
    dataset_version: str
    schema_version: int
    generator_version: str
    seed: int
    applications: int
    borrowers: int
    decision_start: str
    decision_end: str
    snapshot_as_of: str
    horizon_months: int
    default_dpd_threshold: int
    target_positive_rate: float
    risk_intercept: float
    risk_log_income_mean: float
    risk_log_income_std: float
    risk_debt_to_income_center: float
    risk_utilization_center: float
    repeated_borrowers_fraction: float
    censored_fraction: float
    reporting_lag_days: int
    test_months: int
    train_end: str
    validation_end: str
    calibration_end: str
    threshold_end: str
    test_end: str
    group_key: str
    time_key: str
    output_root: str
    parquet_compression: str
    parquet_compression_level: int
    parquet_row_group_size: int

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> SyntheticConfig:
        expected = set(cls.__dataclass_fields__)
        unknown = set(raw) - expected
        missing = expected - set(raw)
        if unknown:
            raise ConfigError(f"unknown configuration keys: {sorted(unknown)}")
        if missing:
            raise ConfigError(f"missing configuration keys: {sorted(missing)}")
        try:
            config = cls(**raw)
        except TypeError as exc:
            raise ConfigError(str(exc)) from exc
        config.validate()
        return config

    def validate(self) -> None:
        int_fields = (
            "config_version",
            "schema_version",
            "seed",
            "applications",
            "borrowers",
            "horizon_months",
            "default_dpd_threshold",
            "reporting_lag_days",
            "test_months",
            "parquet_compression_level",
            "parquet_row_group_size",
        )
        for field in int_fields:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConfigError(f"{field} must be an integer")
        float_fields = (
            "target_positive_rate",
            "risk_intercept",
            "risk_log_income_mean",
            "risk_log_income_std",
            "risk_debt_to_income_center",
            "risk_utilization_center",
            "repeated_borrowers_fraction",
            "censored_fraction",
        )
        for field in float_fields:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ConfigError(f"{field} must be numeric")
        if self.config_version != 1 or self.schema_version != 1:
            raise ConfigError("v1 requires config_version=1 and schema_version=1")
        if self.seed < 0:
            raise ConfigError("seed must be non-negative")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.dataset_version):
            raise ConfigError("dataset_version must be a lowercase safe slug")
        start = _utc_timestamp(self.decision_start, "decision_start")
        end = _utc_timestamp(self.decision_end, "decision_end")
        cutoff = _utc_timestamp(self.snapshot_as_of, "snapshot_as_of")
        if start >= end:
            raise ConfigError("decision_start must precede exclusive decision_end")
        if cutoff <= end:
            raise ConfigError("snapshot_as_of must follow decision_end")
        if self.applications < self.borrowers or self.borrowers <= 0:
            raise ConfigError("applications must be >= positive borrowers")
        if not 0 < self.repeated_borrowers_fraction < 1:
            raise ConfigError("repeated_borrowers_fraction must be between 0 and 1")
        repeated = round(self.borrowers * self.repeated_borrowers_fraction)
        if repeated <= 0 or self.applications - self.borrowers < repeated:
            raise ConfigError(
                "applications cannot give every configured repeated borrower "
                "a second application"
            )
        for field in ("target_positive_rate", "censored_fraction"):
            if not 0 <= float(getattr(self, field)) < 1:
                raise ConfigError(f"{field} must be in [0, 1)")
        if self.horizon_months <= 0 or self.default_dpd_threshold <= 0:
            raise ConfigError("horizon and DPD threshold must be positive")
        if self.reporting_lag_days < 0 or self.test_months <= 0:
            raise ConfigError(
                "reporting lag must be non-negative and test_months positive"
            )
        if self.risk_log_income_std <= 0:
            raise ConfigError("risk_log_income_std must be positive")
        boundaries = [
            start,
            _utc_timestamp(self.train_end, "train_end"),
            _utc_timestamp(self.validation_end, "validation_end"),
            _utc_timestamp(self.calibration_end, "calibration_end"),
            _utc_timestamp(self.threshold_end, "threshold_end"),
            _utc_timestamp(self.test_end, "test_end"),
        ]
        if boundaries[-1] != end or any(
            left >= right for left, right in zip(boundaries, boundaries[1:])
        ):
            raise ConfigError(
                "split boundaries must be strictly ordered and end at decision_end"
            )
        if _add_calendar_months(boundaries[-2], self.test_months) != boundaries[-1]:
            raise ConfigError("test_months does not match the frozen test window")
        if self.group_key != "borrower_id" or self.time_key != "decision_timestamp":
            raise ConfigError("v1 requires borrower_id and decision_timestamp keys")
        if self.generator_version != "1.1.0":
            raise ConfigError("configuration generator_version is unsupported")
        if self.parquet_compression != "zstd":
            raise ConfigError("v1 supports only zstd Parquet compression")
        if not 1 <= self.parquet_compression_level <= 22:
            raise ConfigError("zstd compression level must be between 1 and 22")
        if self.parquet_row_group_size <= 0:
            raise ConfigError("parquet_row_group_size must be positive")

    def normalized(self) -> dict[str, Any]:
        """Return deterministic config content, excluding destination path."""
        result = asdict(self)
        result.pop("output_root")
        return result

    def canonical_json(self) -> str:
        return json.dumps(
            self.normalized(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


def load_config(path: Path) -> SyntheticConfig:
    """Load a strict YAML configuration."""
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot load configuration: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")
    return SyntheticConfig.from_mapping(raw)
