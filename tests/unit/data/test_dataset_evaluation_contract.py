from pathlib import Path

import pytest

from cop.data.evaluation.contract import (
    CAPABILITY_NAMES,
    EvaluationError,
    load_dataset_contract,
)

CONFIG = Path("configs/datasets/uci-default-credit-card.yaml")


def test_uci_contract_declares_every_independent_capability() -> None:
    contract = load_dataset_contract(CONFIG)

    assert tuple(contract.capabilities) == CAPABILITY_NAMES
    assert contract.capabilities["academic_modeling"].status == "pass"
    assert contract.capabilities["entity_identity"].status == "limited"
    assert contract.capabilities["temporal_split"].status == "fail"
    assert contract.capabilities["longitudinal_monitoring"].status == "fail"
    assert contract.capabilities["production_claims"].status == "fail"


def test_contract_rejects_non_official_download_origin(tmp_path: Path) -> None:
    content = CONFIG.read_text(encoding="utf-8").replace(
        "https://archive.ics.uci.edu/static/public/350/",
        "https://example.invalid/",
    )
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(EvaluationError, match="official UCI"):
        load_dataset_contract(path)


def test_contract_rejects_unknown_capability_status(tmp_path: Path) -> None:
    content = CONFIG.read_text(encoding="utf-8").replace(
        "status: limited", "status: maybe", 1
    )
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(EvaluationError, match="invalid status"):
        load_dataset_contract(path)
