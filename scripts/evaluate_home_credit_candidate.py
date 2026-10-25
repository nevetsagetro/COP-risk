"""Inspect a local Home Credit acquisition without downloading or accepting it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = (
    "application_train.csv",
    "application_test.csv",
    "bureau.csv",
    "bureau_balance.csv",
    "previous_application.csv",
    "POS_CASH_balance.csv",
    "installments_payments.csv",
    "credit_card_balance.csv",
    "HomeCredit_columns_description.csv",
)


def _header(path: Path) -> list[str]:
    return [str(column) for column in pd.read_csv(path, nrows=0).columns]


def evaluate_candidate(acquisition: Path) -> dict[str, Any]:
    """Return a gate report; never download or modify the acquisition."""
    report: dict[str, Any] = {
        "candidate": "home-credit-default-risk",
        "authorized_use": "academic_candidate_only",
        "acceptance_status": "not_accepted",
        "acquisition_path": str(acquisition),
        "download_performed": False,
        "decision_window": "pending",
        "target_definition": "pending",
        "temporal_split": "pending",
        "audit_only_columns": "pending",
    }
    if not acquisition.is_dir():
        report["status"] = "blocked_no_local_acquisition"
        report["missing_files"] = list(REQUIRED_FILES)
        report["message"] = (
            "Provide a human-approved local acquisition; "
            "the inspector never downloads data."
        )
        return report

    present = [name for name in REQUIRED_FILES if (acquisition / name).is_file()]
    missing = [name for name in REQUIRED_FILES if name not in present]
    report["present_files"] = present
    report["missing_files"] = missing
    if missing:
        report["status"] = "incomplete_local_acquisition"
        return report

    train_columns = _header(acquisition / "application_train.csv")
    test_columns = _header(acquisition / "application_test.csv")
    report["status"] = "schema_inspected_pending_methodology"
    report["train_columns"] = len(train_columns)
    report["test_columns"] = len(test_columns)
    report["train_has_target"] = "TARGET" in train_columns
    report["test_has_target"] = "TARGET" in test_columns
    report["train_has_entity_id"] = "SK_ID_CURR" in train_columns
    report["test_has_entity_id"] = "SK_ID_CURR" in test_columns
    report["schema_checks"] = {
        "target_only_in_train": "TARGET" in train_columns
        and "TARGET" not in test_columns,
        "entity_id_in_train_and_test": "SK_ID_CURR" in train_columns
        and "SK_ID_CURR" in test_columns,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--acquisition",
        type=Path,
        default=Path("data/raw/home-credit"),
        help="Local acquisition directory; no download is attempted.",
    )
    args = parser.parse_args()
    print(json.dumps(evaluate_candidate(args.acquisition), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
