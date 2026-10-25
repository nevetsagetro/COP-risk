"""Materialize the approved static Home Credit academic snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from cop.data.hashing import logical_table_hash, sha256_file
from cop.data.home_credit import (
    HOME_CREDIT_APPLICATION_FEATURES,
    HOME_CREDIT_AUDIT_ONLY_COLUMNS,
    HOME_CREDIT_FEATURE_VERSION_V0,
    HOME_CREDIT_FEATURE_VERSION_V2,
    HOME_CREDIT_ID,
    HOME_CREDIT_SPLIT_SEED,
    HOME_CREDIT_TARGET,
    add_engineered_features_v2,
    aggregate_bureau,
    aggregate_installments,
    aggregate_previous_applications,
    build_static_feature_frame,
    stable_entity_split,
)

CHUNK_SIZE = 250_000


def _read_application(path: Path) -> pd.DataFrame:
    columns = [HOME_CREDIT_ID, HOME_CREDIT_TARGET, *HOME_CREDIT_APPLICATION_FEATURES]
    return pd.read_csv(path, usecols=columns)


def _combine(
    frames: list[pd.DataFrame],
    *,
    sum_columns: tuple[str, ...],
    max_columns: tuple[str, ...] = (),
    min_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=[HOME_CREDIT_ID])
    combined = pd.concat(frames, ignore_index=True)
    aggregations: dict[str, str] = {column: "sum" for column in sum_columns}
    aggregations.update({column: "max" for column in max_columns})
    aggregations.update({column: "min" for column in min_columns})
    return combined.groupby(HOME_CREDIT_ID, as_index=False).agg(aggregations)


def _read_bureau(path: Path) -> pd.DataFrame:
    columns = [
        HOME_CREDIT_ID,
        "CREDIT_ACTIVE",
        "DAYS_CREDIT",
        "CREDIT_DAY_OVERDUE",
        "AMT_CREDIT_SUM",
        "AMT_CREDIT_SUM_DEBT",
    ]
    pieces = [
        aggregate_bureau(chunk)
        for chunk in pd.read_csv(path, usecols=columns, chunksize=CHUNK_SIZE)
    ]
    return _combine(
        pieces,
        sum_columns=(
            "BUREAU_COUNT",
            "BUREAU_ACTIVE_COUNT",
            "BUREAU_CREDIT_SUM",
            "BUREAU_DEBT_SUM",
        ),
        max_columns=("BUREAU_OVERDUE_MAX",),
    )


def _read_previous(path: Path) -> pd.DataFrame:
    columns = [HOME_CREDIT_ID, "DAYS_DECISION", "NAME_CONTRACT_STATUS", "AMT_CREDIT"]
    pieces = [
        aggregate_previous_applications(chunk)
        for chunk in pd.read_csv(path, usecols=columns, chunksize=CHUNK_SIZE)
    ]
    return _combine(
        pieces,
        sum_columns=(
            "PREVIOUS_APPLICATION_COUNT",
            "PREVIOUS_APPROVED_COUNT",
            "PREVIOUS_REFUSED_COUNT",
            "PREVIOUS_CREDIT_SUM",
        ),
        min_columns=("PREVIOUS_DAYS_DECISION_MIN",),
    )


def _read_installments(path: Path) -> pd.DataFrame:
    columns = [
        HOME_CREDIT_ID,
        "DAYS_INSTALMENT",
        "DAYS_ENTRY_PAYMENT",
        "AMT_INSTALMENT",
        "AMT_PAYMENT",
    ]
    pieces = [
        aggregate_installments(chunk)
        for chunk in pd.read_csv(path, usecols=columns, chunksize=CHUNK_SIZE)
    ]
    return _combine(
        pieces,
        sum_columns=(
            "INSTALLMENT_COUNT",
            "INSTALLMENT_LATE_COUNT",
            "INSTALLMENT_SHORTFALL_SUM",
            "INSTALLMENT_PAYMENT_SUM",
            "INSTALLMENT_AMOUNT_DUE_SUM",
        ),
    )


def _manifest(
    frame: pd.DataFrame, source_tables: list[str], feature_version: str
) -> dict[str, Any]:
    split = stable_entity_split(frame, seed=HOME_CREDIT_SPLIT_SEED)
    return {
        "snapshot_version": 1,
        "feature_version": feature_version,
        "split_seed": HOME_CREDIT_SPLIT_SEED,
        "dataset_id": "home-credit-default-risk",
        "authorized_use": "academic_static_benchmark_only",
        "temporal_status": "not_available_in_source_archive",
        "target": HOME_CREDIT_TARGET,
        "entity_key": HOME_CREDIT_ID,
        "audit_only_columns": list(HOME_CREDIT_AUDIT_ONLY_COLUMNS),
        "model_features": [
            column
            for column in frame.columns
            if column not in {HOME_CREDIT_ID, HOME_CREDIT_TARGET, "split"}
        ],
        "source_tables": source_tables,
        "rows": len(frame),
        "class_counts": {
            str(key): int(value)
            for key, value in frame[HOME_CREDIT_TARGET]
            .value_counts()
            .sort_index()
            .items()
        },
        "split_rows": {
            str(key): int(value)
            for key, value in split["split"].value_counts().sort_index().items()
        },
        "logical_sha256": logical_table_hash(
            frame.drop(columns="split"), (HOME_CREDIT_ID,)
        ),
        "static_split_strategy": "stable hash of SK_ID_CURR; entity-disjoint 70/15/15",
    }


def build(
    acquisition: Path,
    output: Path,
    *,
    feature_version: str = HOME_CREDIT_FEATURE_VERSION_V0,
) -> Path:
    if output.exists():
        raise FileExistsError(f"output already exists; refusing to overwrite: {output}")
    application = _read_application(acquisition / "application_train.csv")
    bureau = _read_bureau(acquisition / "bureau.csv")
    previous = _read_previous(acquisition / "previous_application.csv")
    installments = _read_installments(acquisition / "installments_payments.csv")
    if feature_version not in {
        HOME_CREDIT_FEATURE_VERSION_V0,
        HOME_CREDIT_FEATURE_VERSION_V2,
    }:
        raise ValueError(f"unsupported feature version: {feature_version}")
    frame = build_static_feature_frame(application)
    for aggregate in (bureau, previous, installments):
        frame = frame.merge(
            aggregate,
            on=HOME_CREDIT_ID,
            how="left",
            validate="one_to_one",
        )
    if feature_version == HOME_CREDIT_FEATURE_VERSION_V2:
        frame = add_engineered_features_v2(frame)
    assignments = stable_entity_split(frame, seed=HOME_CREDIT_SPLIT_SEED)
    frame = frame.merge(
        assignments, on=[HOME_CREDIT_ID, HOME_CREDIT_TARGET], validate="one_to_one"
    )
    output.mkdir(parents=True, exist_ok=False)
    snapshot_path = output / "snapshot.parquet"
    frame.to_parquet(snapshot_path, index=False)
    for name in ("train", "validation", "test"):
        frame.loc[frame["split"] == name].to_parquet(
            output / f"{name}.parquet", index=False
        )
    manifest = _manifest(
        frame,
        [
            "application_train.csv",
            "bureau.csv",
            "previous_application.csv",
            "installments_payments.csv",
        ],
        feature_version,
    )
    manifest["files"] = {
        name: {
            "path": f"{name}.parquet",
            "rows": int((frame["split"] == name).sum()),
            "physical_sha256": sha256_file(output / f"{name}.parquet"),
        }
        for name in ("train", "validation", "test")
    }
    manifest["snapshot_physical_sha256"] = sha256_file(snapshot_path)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--acquisition", type=Path, default=Path("data/raw/home-credit")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/home-credit-static")
    )
    parser.add_argument(
        "--feature-version",
        choices=(HOME_CREDIT_FEATURE_VERSION_V0, HOME_CREDIT_FEATURE_VERSION_V2),
        default=HOME_CREDIT_FEATURE_VERSION_V0,
    )
    args = parser.parse_args()
    destination = build(
        args.acquisition, args.output, feature_version=args.feature_version
    )
    print(f"created static snapshot: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
