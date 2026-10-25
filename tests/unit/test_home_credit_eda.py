from __future__ import annotations

import pandas as pd

from cop.evaluation.home_credit_eda import build_home_credit_eda_report


def test_home_credit_eda_is_train_scoped_and_json_safe() -> None:
    train = pd.DataFrame(
        {
            "TARGET": [0, 1, 0, 1],
            "AMT_INCOME_TOTAL": [100.0, 200.0, None, 300.0],
            "AMT_CREDIT": [1000.0, 2000.0, 1500.0, 2500.0],
            "EXT_SOURCE_1": [0.1, 0.2, 0.3, 0.4],
        }
    )
    validation = pd.DataFrame({"TARGET": [0, 1, 1]})
    manifest = {
        "dataset_id": "home-credit-default-risk",
        "feature_version": "features-v0",
        "authorized_use": "academic_static_benchmark_only",
        "target": "TARGET",
        "rows": 7,
        "class_counts": {"0": 4, "1": 3},
        "files": {"test": {"rows": 1}},
        "model_features": ["AMT_INCOME_TOTAL", "AMT_CREDIT", "EXT_SOURCE_1"],
        "audit_only_columns": ["CODE_GENDER"],
        "logical_sha256": "fingerprint",
        "split_seed": 42,
        "static_split_strategy": "entity-disjoint",
    }

    report = build_home_credit_eda_report(train, validation, manifest)

    assert report["test_status"] == "unopened"
    assert report["population"]["analysis_split"] == "train"
    assert report["population"]["final_test_used"] is False
    assert report["prevalence"]["validation"]["rate"] == 2 / 3
    assert report["missingness"]["features"][0]["feature"] == "AMT_INCOME_TOTAL"
    assert report["correlations"]["method"] == "Pearson correlation"
    assert report["correlations"]["features"] == [
        "AMT_INCOME_TOTAL",
        "AMT_CREDIT",
        "EXT_SOURCE_1",
    ]
