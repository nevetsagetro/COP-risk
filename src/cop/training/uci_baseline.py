"""Leakage-safe two-phase training for the UCI academic baseline."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import (  # type: ignore[import-untyped]
    OneHotEncoder,
    StandardScaler,
)

from cop.data.hashing import sha256_file
from cop.evaluation.binary import binary_classification_metrics, prevalence
from cop.features.uci import (
    UCI_APPROVED_FEATURES,
    UCI_CATEGORICAL_FEATURES,
    UCI_NUMERIC_FEATURES,
    validate_uci_features,
)
from cop.training.config import BaselineConfig, load_baseline_config

RUN_MANIFEST_VERSION = 1
MODEL_NAMES = ("logistic_regression", "lightgbm")
CLAIM_FILE = "finalize-test.claim"
FINAL_RESULTS_FILE = "final-test-results.json"
FINAL_PREDICTIONS_FILE = "final-test-predictions.csv"


@dataclass(frozen=True)
class SplitData:
    identifiers: npt.NDArray[np.int64]
    features: pd.DataFrame
    target: npt.NDArray[np.int64]


@dataclass(frozen=True)
class DevelopmentData:
    train: SplitData
    validation: SplitData


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return cast(dict[str, Any], value)


def _verify_sidecar(manifest_path: Path) -> str:
    sidecar = manifest_path.with_suffix(".sha256")
    fields = sidecar.read_text(encoding="utf-8").split()
    actual = sha256_file(manifest_path)
    if len(fields) != 2 or fields[1] != manifest_path.name or fields[0] != actual:
        raise ValueError(f"manifest sidecar mismatch: {manifest_path.name}")
    return actual


def _source_metadata(
    config: BaselineConfig, *, verify_test_file: bool
) -> dict[str, Any]:
    snapshot_path = config.snapshot_directory / "snapshot-manifest.json"
    split_path = config.splits_directory / "split-manifest.json"
    snapshot_sha = _verify_sidecar(snapshot_path)
    split_sha = _verify_sidecar(split_path)
    snapshot = _load_json(snapshot_path)

    configured_snapshot = cast(dict[str, Any], config.raw["snapshot"])
    configured_splits = cast(dict[str, Any], config.raw["splits"])
    if split_sha != configured_splits["manifest_sha256"]:
        raise ValueError("split manifest hash differs from frozen training config")
    if verify_test_file:
        splits = _load_json(split_path)
    else:
        # Development deliberately does not parse the manifest containing test
        # statistics. Its train/validation evidence is frozen separately.
        splits = {
            "snapshot_id": configured_snapshot["snapshot_id"],
            "authorized_use": "academic_baseline_only",
            "logical_splits_sha256": configured_splits["logical_sha256"],
            "files": configured_splits["development_files"],
        }
    if snapshot.get("snapshot_id") != configured_snapshot["snapshot_id"]:
        raise ValueError("snapshot identity differs from frozen training config")
    if snapshot.get("accepted_use") != "academic_baseline_only":
        raise ValueError("snapshot is not accepted for academic baseline use")
    modelable = cast(dict[str, Any], snapshot.get("file"))
    if modelable.get("path") != "dataset.parquet":
        raise ValueError("unexpected modelable snapshot path")
    if modelable.get("logical_sha256") != configured_snapshot["logical_sha256"]:
        raise ValueError("snapshot logical hash differs from frozen config")
    expected_columns = ["ID", *UCI_APPROVED_FEATURES, config.raw["target"]]
    if snapshot.get("modelable_columns") != expected_columns:
        raise ValueError("snapshot modelable columns differ from feature contract")
    if set(snapshot.get("audit_only_columns", [])) & set(UCI_APPROVED_FEATURES):
        raise ValueError("an audit-only column appears in approved features")
    dataset_path = config.snapshot_directory / "dataset.parquet"
    if sha256_file(dataset_path) != modelable.get("physical_sha256"):
        raise ValueError("modelable snapshot physical hash mismatch")

    if splits.get("snapshot_id") != snapshot.get("snapshot_id"):
        raise ValueError("split manifest references another snapshot")
    if splits.get("authorized_use") != "academic_baseline_only":
        raise ValueError("splits are not authorized for academic baseline use")
    if splits.get("logical_splits_sha256") != configured_splits["logical_sha256"]:
        raise ValueError("split logical hash differs from frozen config")
    files = splits.get("files")
    expected_names = (
        {"train", "validation", "test"} if verify_test_file else {"train", "validation"}
    )
    if not isinstance(files, dict) or set(files) != expected_names:
        raise ValueError("split manifest inventory differs from baseline contract")
    for name in ("train", "validation"):
        entry = cast(dict[str, Any], files[name])
        if entry.get("path") != f"{name}.parquet":
            raise ValueError(f"unexpected {name} split path")
        if sha256_file(config.splits_directory / f"{name}.parquet") != entry.get(
            "physical_sha256"
        ):
            raise ValueError(f"{name} split physical hash mismatch")
    if verify_test_file:
        test_entry = cast(dict[str, Any], files["test"])
        if test_entry.get("path") != "test.parquet":
            raise ValueError("unexpected test split path")
        if sha256_file(config.splits_directory / "test.parquet") != test_entry.get(
            "physical_sha256"
        ):
            raise ValueError("test split physical hash mismatch")
    return {
        "snapshot": snapshot,
        "snapshot_manifest_sha256": snapshot_sha,
        "split_manifest": splits,
        "split_manifest_sha256": split_sha,
    }


def _load_assignments(config: BaselineConfig, name: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        config.splits_directory / f"{name}.parquet",
        columns=["ID", cast(str, config.raw["target"])],
    )
    if tuple(frame.columns) != ("ID", config.raw["target"]):
        raise ValueError(f"{name} split columns differ from contract")
    if frame.isna().any(axis=None) or not frame["ID"].is_unique:
        raise ValueError(f"{name} split contains missing or duplicate values")
    if set(frame[cast(str, config.raw["target"])]) != {0, 1}:
        raise ValueError(f"{name} split target must contain both binary classes")
    return frame


def _load_features_for_ids(
    config: BaselineConfig, identifiers: list[int]
) -> pd.DataFrame:
    # Predicate pushdown and explicit projection are deliberate: development never
    # reads the snapshot target or audit-only file.
    frame = pd.read_parquet(
        config.snapshot_directory / "dataset.parquet",
        columns=["ID", *UCI_APPROVED_FEATURES],
        filters=[("ID", "in", identifiers)],
    )
    if tuple(frame.columns) != ("ID", *UCI_APPROVED_FEATURES):
        raise ValueError("snapshot projection differs from the feature contract")
    if not frame["ID"].is_unique or set(frame["ID"]) != set(identifiers):
        raise ValueError("snapshot feature projection does not match requested IDs")
    return frame


def _align(assignments: pd.DataFrame, projected: pd.DataFrame) -> SplitData:
    target_name = assignments.columns[1]
    aligned = assignments.merge(projected, on="ID", how="left", validate="one_to_one")
    features = aligned.loc[:, list(UCI_APPROVED_FEATURES)]
    validate_uci_features(features)
    return SplitData(
        identifiers=aligned["ID"].to_numpy(dtype=np.int64, copy=True),
        features=features,
        target=aligned[target_name].to_numpy(dtype=np.int64, copy=True),
    )


def load_development_data(config: BaselineConfig) -> DevelopmentData:
    """Load train/validation only; the test and audit-only files remain unopened."""
    metadata = _source_metadata(config, verify_test_file=False)
    train = _load_assignments(config, "train")
    validation = _load_assignments(config, "validation")
    if set(train["ID"]) & set(validation["ID"]):
        raise ValueError("ID crosses train and validation splits")
    files = cast(dict[str, Any], metadata["split_manifest"]["files"])
    for name, frame in (("train", train), ("validation", validation)):
        expected = cast(dict[str, Any], files[name])
        counts = {
            str(key): int(value)
            for key, value in frame[cast(str, config.raw["target"])]
            .value_counts()
            .sort_index()
            .items()
        }
        if len(frame) != expected.get("rows") or counts != expected.get("class_counts"):
            raise ValueError(f"{name} split statistics differ from manifest")
    all_ids = [int(value) for value in pd.concat([train["ID"], validation["ID"]])]
    projected = _load_features_for_ids(config, all_ids)
    return DevelopmentData(
        train=_align(train, projected),
        validation=_align(validation, projected),
    )


def _preprocessor(*, scale_numeric: bool) -> ColumnTransformer:
    numeric: StandardScaler | str = StandardScaler() if scale_numeric else "passthrough"
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", dtype=np.float64),
                list(UCI_CATEGORICAL_FEATURES),
            ),
            ("numeric", numeric, list(UCI_NUMERIC_FEATURES)),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_models(config: BaselineConfig) -> dict[str, Pipeline]:
    params = cast(dict[str, dict[str, Any]], config.raw["models"])
    seed = cast(int, config.raw["random_seed"])
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", _preprocessor(scale_numeric=True)),
                (
                    "classifier",
                    LogisticRegression(
                        **params["logistic_regression"], random_state=seed
                    ),
                ),
            ]
        ),
        "lightgbm": Pipeline(
            steps=[
                ("preprocessor", _preprocessor(scale_numeric=False)),
                (
                    "classifier",
                    LGBMClassifier(**params["lightgbm"], random_state=seed),
                ),
            ]
        ),
    }


def _positive_probability(
    model: Pipeline, features: pd.DataFrame
) -> npt.NDArray[np.float64]:
    probability = np.asarray(model.predict_proba(features), dtype=np.float64)
    classes = np.asarray(model.classes_)
    positions = np.flatnonzero(classes == 1)
    if probability.ndim != 2 or len(positions) != 1:
        raise ValueError("model does not expose one positive-class probability")
    return cast(npt.NDArray[np.float64], probability[:, int(positions[0])])


def _run_identity(config: BaselineConfig, metadata: dict[str, Any]) -> str:
    identity = {
        "config_file_sha256": config.file_sha256,
        "config_sha256": config.canonical_sha256,
        "snapshot_manifest_sha256": metadata["snapshot_manifest_sha256"],
        "split_manifest_sha256": metadata["split_manifest_sha256"],
    }
    digest = hashlib.sha256(_canonical_json(identity)).hexdigest()
    return f"uci-baseline-{digest}"


def _artifact_entry(path: Path) -> dict[str, Any]:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _expected_run_path(config: BaselineConfig, metadata: dict[str, Any]) -> Path:
    return config.run_root / _run_identity(config, metadata)


def _write_validation_predictions(
    path: Path,
    identifiers: npt.NDArray[np.int64],
    target: npt.NDArray[np.int64],
    probabilities: dict[str, npt.NDArray[np.float64]],
) -> None:
    frame = pd.DataFrame({"ID": identifiers, "target": target})
    for name in MODEL_NAMES:
        frame[f"{name}_probability"] = probabilities[name]
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.17g")


def train_development(config_path: Path) -> Path:
    """Fit on train and record validation only in an atomic immutable run."""
    config = load_baseline_config(config_path)
    metadata = _source_metadata(config, verify_test_file=False)
    destination = _expected_run_path(config, metadata)
    if destination.exists():
        _verify_run(config, metadata, destination)
        return destination
    data = load_development_data(config)
    models = build_models(config)
    probabilities: dict[str, npt.NDArray[np.float64]] = {}
    metrics: dict[str, Any] = {}
    for name in MODEL_NAMES:
        model = models[name]
        model.fit(data.train.features, data.train.target)
        probabilities[name] = _positive_probability(model, data.validation.features)
        metrics[name] = binary_classification_metrics(
            data.validation.target,
            probabilities[name],
            threshold=cast(float, config.raw["threshold"]),
        )

    config.run_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".uci-baseline-", dir=config.run_root
    ) as temp:
        staging = Path(temp)
        frozen_config = staging / "training-config.yaml"
        frozen_config.write_bytes(config.path.read_bytes())
        model_entries: dict[str, Any] = {}
        for name in MODEL_NAMES:
            model_path = staging / f"{name}.joblib"
            joblib.dump(models[name], model_path, compress=3)
            model_entries[name] = {
                "parameters": config.raw["models"][name],
                "artifact": _artifact_entry(model_path),
            }
        predictions_path = staging / "validation-predictions.csv"
        _write_validation_predictions(
            predictions_path,
            data.validation.identifiers,
            data.validation.target,
            probabilities,
        )
        results = {
            "phase": "development",
            "authorized_use": "academic_baseline_only",
            "fit_split": "train",
            "evaluation_split": "validation",
            "threshold": config.raw["threshold"],
            "prevalence": {
                "train": prevalence(data.train.target),
                "validation": prevalence(data.validation.target),
            },
            "models": metrics,
            "claims_not_made": [
                "champion",
                "primary_metric",
                "winner",
                "optimal_threshold",
                "production_validity",
                "fairness",
                "real_world_calibration",
            ],
        }
        results_path = staging / "validation-results.json"
        results_path.write_bytes(_canonical_json(results))
        snapshot = cast(dict[str, Any], metadata["snapshot"])
        split_manifest = cast(dict[str, Any], metadata["split_manifest"])
        manifest = {
            "run_manifest_version": RUN_MANIFEST_VERSION,
            "run_id": destination.name,
            "phase": "development_frozen",
            "config": {
                "source_path": str(config.path.relative_to(config.path.parents[2])),
                "file_sha256": config.file_sha256,
                "canonical_sha256": config.canonical_sha256,
                "frozen": _artifact_entry(frozen_config),
            },
            "snapshot": {
                "snapshot_id": snapshot["snapshot_id"],
                "manifest_sha256": metadata["snapshot_manifest_sha256"],
                "logical_sha256": snapshot["file"]["logical_sha256"],
                "physical_sha256": snapshot["file"]["physical_sha256"],
            },
            "splits": {
                "manifest_sha256": metadata["split_manifest_sha256"],
                "logical_sha256": split_manifest["logical_splits_sha256"],
                "files": split_manifest["files"],
            },
            "features": list(UCI_APPROVED_FEATURES),
            "categorical_features": list(UCI_CATEGORICAL_FEATURES),
            "target": config.raw["target"],
            "random_seed": config.raw["random_seed"],
            "models": model_entries,
            "validation_results": _artifact_entry(results_path),
            "validation_predictions": _artifact_entry(predictions_path),
            "test_status": "unopened",
        }
        (staging / "run-manifest.json").write_bytes(_canonical_json(manifest))
        for artifact in staging.iterdir():
            artifact.chmod(0o444)
        try:
            staging.rename(destination)
        except FileExistsError:
            _verify_run(config, metadata, destination)
    _verify_run(config, metadata, destination)
    return destination


def _verify_run(
    config: BaselineConfig, metadata: dict[str, Any], directory: Path
) -> dict[str, Any]:
    manifest = _load_json(directory / "run-manifest.json")
    if manifest.get("run_manifest_version") != RUN_MANIFEST_VERSION:
        raise ValueError("unsupported run manifest version")
    if manifest.get("run_id") != directory.name:
        raise ValueError("run directory identity mismatch")
    if directory != _expected_run_path(config, metadata):
        raise ValueError("run does not match current frozen inputs")
    config_entry = cast(dict[str, Any], manifest.get("config"))
    if config_entry.get("file_sha256") != config.file_sha256:
        raise ValueError("current training config differs from frozen run")
    if config_entry.get("canonical_sha256") != config.canonical_sha256:
        raise ValueError("current canonical config differs from frozen run")
    frozen = cast(dict[str, Any], config_entry.get("frozen"))
    if sha256_file(directory / cast(str, frozen["path"])) != frozen.get("sha256"):
        raise ValueError("frozen training config hash mismatch")
    snapshot = cast(dict[str, Any], manifest.get("snapshot"))
    if snapshot.get("manifest_sha256") != metadata["snapshot_manifest_sha256"]:
        raise ValueError("snapshot manifest changed after development")
    splits = cast(dict[str, Any], manifest.get("splits"))
    if splits.get("manifest_sha256") != metadata["split_manifest_sha256"]:
        raise ValueError("split manifest changed after development")
    for name in MODEL_NAMES:
        model = cast(dict[str, Any], manifest["models"][name])
        artifact = cast(dict[str, Any], model["artifact"])
        path = directory / cast(str, artifact["path"])
        if sha256_file(path) != artifact.get("sha256"):
            raise ValueError(f"{name} model artifact hash mismatch")
    for key in ("validation_results", "validation_predictions"):
        artifact = cast(dict[str, Any], manifest[key])
        if sha256_file(directory / cast(str, artifact["path"])) != artifact.get(
            "sha256"
        ):
            raise ValueError(f"{key} artifact hash mismatch")
    return manifest


def _exclusive_write(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise


def _claim_test(run_directory: Path, manifest: dict[str, Any]) -> None:
    payload = _canonical_json(
        {
            "run_id": manifest["run_id"],
            "state": "consumed",
            "policy": "no_retry_even_after_failure",
        }
    )
    _exclusive_write(run_directory / CLAIM_FILE, payload)


def _load_test_data(config: BaselineConfig) -> SplitData:
    # This is the only tabular opening of test.parquet, and it occurs after claim.
    assignments = _load_assignments(config, "test")
    projected = _load_features_for_ids(
        config, [int(value) for value in assignments["ID"]]
    )
    return _align(assignments, projected)


def finalize_test(config_path: Path) -> Path:
    """Consume the final test once after verifying every frozen input and model."""
    config = load_baseline_config(config_path)
    metadata = _source_metadata(config, verify_test_file=True)
    run_directory = _expected_run_path(config, metadata)
    claim_path = run_directory / CLAIM_FILE
    if claim_path.exists():
        raise RuntimeError("final test has already been consumed for this run")
    if (run_directory / FINAL_RESULTS_FILE).exists() or (
        run_directory / FINAL_PREDICTIONS_FILE
    ).exists():
        raise RuntimeError("final test artifacts exist without a consumption claim")
    manifest = _verify_run(config, metadata, run_directory)
    models: dict[str, Pipeline] = {}
    for name in MODEL_NAMES:
        artifact = manifest["models"][name]["artifact"]
        loaded = joblib.load(run_directory / artifact["path"])
        if not isinstance(loaded, Pipeline):
            raise ValueError(f"{name} artifact is not a fitted sklearn pipeline")
        models[name] = loaded

    _claim_test(run_directory, manifest)
    test = _load_test_data(config)
    split_manifest = cast(dict[str, Any], metadata["split_manifest"])
    expected_test = cast(dict[str, Any], split_manifest["files"]["test"])
    counts = {
        str(key): int(value)
        for key, value in pd.Series(test.target).value_counts().sort_index().items()
    }
    if (
        len(test.target) != expected_test["rows"]
        or counts != expected_test["class_counts"]
    ):
        raise ValueError("test split statistics differ from frozen manifest")
    probabilities = {
        name: _positive_probability(models[name], test.features) for name in MODEL_NAMES
    }
    metrics = {
        name: binary_classification_metrics(
            test.target,
            probabilities[name],
            threshold=cast(float, config.raw["threshold"]),
        )
        for name in MODEL_NAMES
    }
    predictions = pd.DataFrame({"ID": test.identifiers, "target": test.target})
    for name in MODEL_NAMES:
        predictions[f"{name}_probability"] = probabilities[name]
    prediction_payload = predictions.to_csv(
        index=False, lineterminator="\n", float_format="%.17g"
    ).encode()
    _exclusive_write(run_directory / FINAL_PREDICTIONS_FILE, prediction_payload)
    results = {
        "phase": "final_test",
        "run_id": manifest["run_id"],
        "authorized_use": "academic_baseline_only",
        "evaluation_split": "test",
        "test_prevalence": prevalence(test.target),
        "threshold": config.raw["threshold"],
        "models": metrics,
        "predictions_sha256": hashlib.sha256(prediction_payload).hexdigest(),
        "claims_not_made": [
            "champion",
            "primary_metric",
            "winner",
            "optimal_threshold",
            "production_validity",
            "fairness",
            "real_world_calibration",
        ],
    }
    result_path = run_directory / FINAL_RESULTS_FILE
    _exclusive_write(result_path, _canonical_json(results))
    return result_path
