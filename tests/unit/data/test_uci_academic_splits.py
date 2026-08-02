from pathlib import Path

import pandas as pd

from cop.data.evaluation.academic_splits import stratified_assignments
from cop.data.evaluation.contract import DatasetContract, load_dataset_contract

CONFIG = Path("configs/datasets/uci-default-credit-card.yaml")


def _contract() -> DatasetContract:
    loaded = load_dataset_contract(CONFIG)
    raw = dict(loaded.raw)
    raw["expected_schema"] = dict(raw["expected_schema"])
    raw["expected_schema"]["rows"] = 100
    return DatasetContract(raw)


def test_stratified_assignments_are_deterministic_and_disjoint() -> None:
    frame = pd.DataFrame(
        {
            "ID": range(1, 101),
            "default_payment_next_month": [0] * 80 + [1] * 20,
        }
    )
    contract = _contract()

    first = stratified_assignments(contract, frame)
    second = stratified_assignments(contract, frame.sample(frac=1, random_state=9))

    assert first.equals(second)
    assert first["ID"].is_unique
    assert first["split_name"].value_counts().to_dict() == {
        "train": 70,
        "validation": 15,
        "test": 15,
    }
    counts = first.groupby(["split_name", "default_payment_next_month"]).size()
    assert counts["train", 1] == 14
    assert counts["validation", 1] == 3
    assert counts["test", 1] == 3
