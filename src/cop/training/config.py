"""Strict configuration for the frozen UCI academic baseline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from cop.data.hashing import sha256_file
from cop.data.yaml import StrictYamlError, UniqueKeyLoader
from cop.features.uci import (
    UCI_APPROVED_FEATURES,
    UCI_CATEGORICAL_FEATURES,
    UCI_NUMERIC_FEATURES,
)

TARGET = "default_payment_next_month"
LOGISTIC_REGRESSION_PARAMETERS: dict[str, Any] = {
    "C": 1.0,
    "class_weight": None,
    "fit_intercept": True,
    "l1_ratio": 0.0,
    "max_iter": 1000,
    "solver": "liblinear",
}
LIGHTGBM_PARAMETERS: dict[str, Any] = {
    "class_weight": None,
    "colsample_bytree": 1.0,
    "deterministic": True,
    "force_col_wise": True,
    "learning_rate": 0.05,
    "max_depth": -1,
    "min_child_samples": 20,
    "n_estimators": 200,
    "n_jobs": 1,
    "num_leaves": 31,
    "objective": "binary",
    "reg_alpha": 0.0,
    "reg_lambda": 0.0,
    "subsample": 1.0,
    "verbosity": -1,
}


@dataclass(frozen=True)
class BaselineConfig:
    path: Path
    raw: dict[str, Any]
    snapshot_directory: Path
    splits_directory: Path
    run_root: Path

    @property
    def file_sha256(self) -> str:
        return sha256_file(self.path)

    @property
    def canonical_sha256(self) -> str:
        payload = json.dumps(
            self.raw,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
        return hashlib.sha256(payload).hexdigest()


def _mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"training config {key} must be a mapping")
    return cast(dict[str, Any], value)


def _path(repository: Path, value: Any, key: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"training config {key} must be a path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"training config {key} must stay repository-relative")
    return repository / path


def load_baseline_config(path: Path) -> BaselineConfig:
    resolved = path.resolve(strict=True)
    try:
        loaded = yaml.load(resolved.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError, StrictYamlError) as exc:
        raise ValueError(f"cannot load training config: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError("training config root must be a mapping")
    raw = cast(dict[str, Any], loaded)
    repository = resolved.parents[2]
    required_top_level = {
        "training_contract_version",
        "dataset_id",
        "authorized_use",
        "snapshot",
        "splits",
        "target",
        "features",
        "missing_policy",
        "threshold",
        "random_seed",
        "models",
        "run_root",
    }
    if set(raw) != required_top_level:
        raise ValueError("training config top-level fields differ from contract")
    if raw["training_contract_version"] != 1:
        raise ValueError("unsupported training contract version")
    if raw["dataset_id"] != "uci-default-credit-card":
        raise ValueError("training config must select the UCI dataset")
    if raw["authorized_use"] != "academic_baseline_only":
        raise ValueError("training config exceeds accepted academic use")
    if raw["target"] != TARGET:
        raise ValueError("training config target differs from UCI contract")
    if raw["missing_policy"] != "fail":
        raise ValueError("baseline does not permit imputation")
    if raw["threshold"] != 0.5:
        raise ValueError("baseline threshold must remain descriptive at 0.5")
    if raw["random_seed"] != 42:
        raise ValueError("baseline random seed is frozen at 42")

    features = _mapping(raw, "features")
    if set(features) != {"approved", "categorical", "numeric"}:
        raise ValueError("feature groups differ from contract")
    if tuple(features["approved"]) != UCI_APPROVED_FEATURES:
        raise ValueError("training config must contain exactly 19 approved features")
    if tuple(features["categorical"]) != UCI_CATEGORICAL_FEATURES:
        raise ValueError("PAY_0 and PAY_2-PAY_6 must be categorical")
    if tuple(features["numeric"]) != UCI_NUMERIC_FEATURES:
        raise ValueError("numeric feature group differs from contract")

    models = _mapping(raw, "models")
    if set(models) != {"logistic_regression", "lightgbm"}:
        raise ValueError("exactly two fixed baseline models are required")
    if models["logistic_regression"] != LOGISTIC_REGRESSION_PARAMETERS:
        raise ValueError("logistic regression parameters differ from frozen baseline")
    if models["lightgbm"] != LIGHTGBM_PARAMETERS:
        raise ValueError("LightGBM parameters differ from frozen baseline")
    snapshot = _mapping(raw, "snapshot")
    splits = _mapping(raw, "splits")
    for section, name, hash_keys in (
        (snapshot, "snapshot", ("logical_sha256",)),
        (splits, "splits", ("logical_sha256", "manifest_sha256")),
    ):
        for hash_key in hash_keys:
            value = section.get(hash_key)
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"{name}.{hash_key} must be SHA-256")
    development_files = splits.get("development_files")
    if not isinstance(development_files, dict) or set(development_files) != {
        "train",
        "validation",
    }:
        raise ValueError("splits.development_files must contain train and validation")
    for name, expected_path in (
        ("train", "train.parquet"),
        ("validation", "validation.parquet"),
    ):
        entry = development_files[name]
        if not isinstance(entry, dict) or set(entry) != {
            "path",
            "rows",
            "class_counts",
            "physical_sha256",
            "logical_sha256",
        }:
            raise ValueError(f"invalid frozen development metadata: {name}")
        if entry["path"] != expected_path or not isinstance(entry["rows"], int):
            raise ValueError(f"invalid frozen development identity: {name}")
        if set(entry["class_counts"]) != {"0", "1"}:
            raise ValueError(f"invalid frozen development class counts: {name}")
        for key in ("physical_sha256", "logical_sha256"):
            if not isinstance(entry[key], str) or len(entry[key]) != 64:
                raise ValueError(f"invalid frozen development hash: {name}.{key}")
    if not isinstance(snapshot.get("snapshot_id"), str):
        raise ValueError("snapshot.snapshot_id is required")
    return BaselineConfig(
        path=resolved,
        raw=raw,
        snapshot_directory=_path(repository, snapshot.get("directory"), "snapshot"),
        splits_directory=_path(repository, splits.get("directory"), "splits"),
        run_root=_path(repository, raw["run_root"], "run_root"),
    )
