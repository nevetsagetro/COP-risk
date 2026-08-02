from dataclasses import replace
from pathlib import Path

import pytest

import cop.data.synthetic.snapshot as snapshot_module
from cop.data.synthetic.config import ConfigError, SyntheticConfig, load_config
from cop.data.synthetic.snapshot import generator_code_hash, snapshot_id

FIXTURE = Path("tests/fixtures/synthetic-small.yaml")


def test_load_config_is_strict_and_normalized() -> None:
    config = load_config(FIXTURE)

    assert config.applications == 240
    assert config.borrowers == 180
    assert "output_root" not in config.normalized()
    assert config.canonical_json() == config.canonical_json()


def test_duplicate_yaml_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text("seed: 1\nseed: 2\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="duplicate"):
        load_config(path)


def test_naive_timestamp_is_rejected(tmp_path: Path) -> None:
    content = FIXTURE.read_text(encoding="utf-8").replace(
        '"2022-01-01T00:00:00Z"', '"2022-01-01T00:00:00"'
    )
    path = tmp_path / "naive.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigError, match="ending in Z"):
        load_config(path)


def test_snapshot_identity_changes_with_seed_but_not_output_root() -> None:
    config = load_config(FIXTURE)

    assert snapshot_id(config) == snapshot_id(replace(config, output_root="/tmp/other"))
    assert snapshot_id(config) != snapshot_id(replace(config, seed=config.seed + 1))
    assert len(generator_code_hash()) == 64


def test_snapshot_identity_changes_with_generator_code_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_config(FIXTURE)
    original = snapshot_id(config)

    monkeypatch.setattr(snapshot_module, "generator_code_hash", lambda: "0" * 64)

    assert snapshot_id(config) != original


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("config_version", 99),
        ("schema_version", 99),
        ("seed", -1),
        ("dataset_version", "../unsafe"),
        ("reporting_lag_days", -1),
        ("test_months", 0),
        ("test_months", 5),
        ("parquet_compression_level", 23),
        ("parquet_row_group_size", 0),
    ],
)
def test_invalid_operational_values_are_rejected(field: str, value: object) -> None:
    config = load_config(FIXTURE)
    mapping = config.normalized()
    mapping["output_root"] = config.output_root
    mapping[field] = value

    with pytest.raises(ConfigError):
        SyntheticConfig.from_mapping(mapping)
