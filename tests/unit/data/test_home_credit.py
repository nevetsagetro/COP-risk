import pandas as pd
import pytest

from cop.data.home_credit import (
    HOME_CREDIT_APPLICATION_FEATURES,
    aggregate_bureau,
    aggregate_installments,
    aggregate_previous_applications,
    build_static_feature_frame,
    build_static_feature_frame_v2,
    stable_entity_split,
)


def _application() -> pd.DataFrame:
    rows = 40
    frame = pd.DataFrame(
        {
            feature: [float(index) for index in range(rows)]
            for feature in HOME_CREDIT_APPLICATION_FEATURES
        }
    )
    frame["SK_ID_CURR"] = list(range(10, 10 + rows))
    frame["TARGET"] = [index % 2 for index in range(rows)]
    return frame


def test_static_feature_frame_aggregates_only_historical_rows() -> None:
    application = _application()
    bureau = pd.DataFrame(
        {
            "SK_ID_CURR": [10, 10, 10, 11],
            "CREDIT_ACTIVE": ["Active", "Closed", "Active", "Active"],
            "DAYS_CREDIT": [-10, 0, 4, -2],
            "CREDIT_DAY_OVERDUE": [1, 0, 99, 2],
            "AMT_CREDIT_SUM": [100, 200, 999, 300],
            "AMT_CREDIT_SUM_DEBT": [50, 20, 999, 100],
        }
    )
    previous = pd.DataFrame(
        {
            "SK_ID_CURR": [10, 10, 11],
            "DAYS_DECISION": [-2, 4, -3],
            "NAME_CONTRACT_STATUS": ["Approved", "Refused", "Refused"],
            "AMT_CREDIT": [100, 999, 300],
        }
    )
    installments = pd.DataFrame(
        {
            "SK_ID_CURR": [10, 10, 11],
            "DAYS_INSTALMENT": [-4, 4, -3],
            "DAYS_ENTRY_PAYMENT": [-3, 5, -2],
            "AMT_INSTALMENT": [100, 999, 300],
            "AMT_PAYMENT": [80, 999, 250],
        }
    )

    result = build_static_feature_frame(
        application,
        bureau=bureau,
        previous_applications=previous,
        installments=installments,
    )

    row = result.loc[result["SK_ID_CURR"] == 10].iloc[0]
    assert row["BUREAU_COUNT"] == 2
    assert row["BUREAU_OVERDUE_MAX"] == 1
    assert row["PREVIOUS_APPLICATION_COUNT"] == 1
    assert row["INSTALLMENT_COUNT"] == 1
    assert row["INSTALLMENT_SHORTFALL_SUM"] == 20


def test_static_split_is_deterministic_and_entity_disjoint() -> None:
    application = _application()
    first = stable_entity_split(application)
    second = stable_entity_split(application)

    pd.testing.assert_frame_equal(first, second)
    assert first["SK_ID_CURR"].is_unique
    assert set(first["split"]) == {"train", "validation", "test"}


def test_feature_engineering_v2_preserves_baseline_and_adds_ratios() -> None:
    application = _application()
    bureau = pd.DataFrame(
        {
            "SK_ID_CURR": [10],
            "CREDIT_ACTIVE": ["Active"],
            "DAYS_CREDIT": [-10],
            "CREDIT_DAY_OVERDUE": [1],
            "AMT_CREDIT_SUM": [100],
            "AMT_CREDIT_SUM_DEBT": [50],
        }
    )
    previous = pd.DataFrame(
        {
            "SK_ID_CURR": [10],
            "DAYS_DECISION": [-2],
            "NAME_CONTRACT_STATUS": ["Approved"],
            "AMT_CREDIT": [100],
        }
    )
    installments = pd.DataFrame(
        {
            "SK_ID_CURR": [10],
            "DAYS_INSTALMENT": [-4],
            "DAYS_ENTRY_PAYMENT": [-3],
            "AMT_INSTALMENT": [100],
            "AMT_PAYMENT": [80],
        }
    )

    result = build_static_feature_frame_v2(
        application,
        bureau=bureau,
        previous_applications=previous,
        installments=installments,
    )

    row = result.loc[result["SK_ID_CURR"] == 10].iloc[0]
    assert row["AMT_CREDIT"] == application.loc[0, "AMT_CREDIT"]
    assert row["BUREAU_DEBT_CREDIT_RATIO"] == pytest.approx(0.5)
    assert row["PREVIOUS_APPROVAL_RATE"] == pytest.approx(1.0)
    assert row["INSTALLMENT_PAYMENT_COVERAGE"] == pytest.approx(0.8)


def test_aggregators_require_contract_columns() -> None:
    with pytest.raises(ValueError, match="bureau frame missing"):
        aggregate_bureau(pd.DataFrame())
    with pytest.raises(ValueError, match="previous application frame missing"):
        aggregate_previous_applications(pd.DataFrame())
    with pytest.raises(ValueError, match="installments frame missing"):
        aggregate_installments(pd.DataFrame())
