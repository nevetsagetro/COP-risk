from cop.evaluation.feature_ablation import feature_families


def test_feature_families_are_versioned_and_disjoint() -> None:
    baseline = ("AMT_CREDIT", "BUREAU_COUNT")
    challenger = baseline + (
        "APP_CREDIT_INCOME_RATIO",
        "EXT_SOURCE_MEAN",
        "INSTALLMENT_LATE_RATE",
    )

    families = feature_families(baseline, challenger)

    assert families["baseline"] == baseline
    assert families["financial_ratios"] == baseline + ("APP_CREDIT_INCOME_RATIO",)
    assert families["external_score_quality"] == baseline + ("EXT_SOURCE_MEAN",)
    assert families["credit_history_behavior"] == baseline + ("INSTALLMENT_LATE_RATE",)
    assert families["all_v2"] == challenger
